import json
import asyncio
import re
import time

from council.state import create_initial_state, log_event

from council.prompts import *

from council.agreement import cluster_answers, consensus_score

from llm.openrouter_client import OpenRouterClient

from config.settings import MODEL_REGISTRY, FALLBACK_REGISTRY


llm = OpenRouterClient()


async def call_agent(agent_name, prompt):

    models_to_try = [MODEL_REGISTRY[agent_name]]

    if agent_name in FALLBACK_REGISTRY:
        models_to_try.extend(FALLBACK_REGISTRY[agent_name])

    last_error = None

    for model in models_to_try:

        try:
            output = await asyncio.wait_for(
                llm.generate(model, prompt),
                timeout=90
            )

            try:
                parsed = json.loads(output)

                if isinstance(parsed, dict):
                    parsed["model"] = model
                    parsed["agent_role"] = agent_name

                return parsed

            except Exception:
                return {
                    "raw_output": output,
                    "model": model,
                    "agent_role": agent_name
                }

        except asyncio.TimeoutError:
            last_error = f"timeout on {model}"
            continue

        except Exception as e:
            last_error = f"{model}: {str(e)}"
            continue

    return {
        "error": last_error or "all_models_failed",
        "agent_role": agent_name,
        "model": models_to_try[0],
        "proposed_answer": f"All models failed for {agent_name}"
    }


async def run_council(query):

    state = create_initial_state(query)

    start_time = time.time()
    state["execution_metrics"]["start_time"] = start_time

    state["active_models"] = MODEL_REGISTRY.copy()
    state["fallback_models"] = FALLBACK_REGISTRY.copy()


    # ROUND 1A: run analyst first (complexity detection)

    analyst = await call_agent(
        "analyst",
        analyst_prompt(query)
    )

    log_event(state, "round1", "analyst", analyst)

    # Extract complexity from parsed JSON or analyst raw_output
    complexity_raw = analyst.get("complexity")

    if not complexity_raw and "raw_output" in analyst:
        raw = analyst["raw_output"]

        match = re.search(r'"complexity"\s*:\s*"([^"]+)"', raw, re.IGNORECASE)

        if match:
            complexity_raw = match.group(1)

    complexity_raw = str(complexity_raw or "medium").strip().lower()

    if "high" in complexity_raw:
        complexity = "high"
    elif "medium" in complexity_raw:
        complexity = "medium"
    elif "low" in complexity_raw:
        complexity = "low"
    else:
        complexity = "medium"

    state["complexity"] = complexity

    # Extract analyst requested council size
    minimum_council_size = analyst.get("minimum_council_size")

    if minimum_council_size is None and "raw_output" in analyst:
        raw = analyst["raw_output"]

        match = re.search(
            r'"(?:minimum_council_size|min_council_size)"\s*:\s*(\d+)',
            raw,
            re.IGNORECASE
        )

        if match:
            minimum_council_size = int(match.group(1))

    try:
        minimum_council_size = int(minimum_council_size)
    except:
        minimum_council_size = None

    state["minimum_council_size"] = minimum_council_size

    # ROUND 1B: adaptive agent routing

    if complexity == "low":

        primary_reasoning = await call_agent(
            "reasoner_primary",
            primary_reasoning_prompt(query)
        )

        log_event(state, "round1", "primary_reasoner", primary_reasoning)

        fast_reasoning = None
        validator = None

        state["council_size"] = 1
        state["routing_decision"] = "LOW complexity routed to primary reasoner only"

    elif complexity == "medium":

        primary_task = call_agent(
            "reasoner_primary",
            primary_reasoning_prompt(query)
        )

        fast_task = call_agent(
            "reasoner_fast",
            alternative_reasoning_prompt(query)
        )

        primary_reasoning, fast_reasoning = await asyncio.gather(
            primary_task,
            fast_task
        )

        log_event(state, "round1", "primary_reasoner", primary_reasoning)
        log_event(state, "round1", "alternative_reasoner", fast_reasoning)

        validator = None

        state["council_size"] = 2
        state["routing_decision"] = "MEDIUM complexity routed to primary and alternative reasoners"

    else:  # high complexity

        primary_task = call_agent(
            "reasoner_primary",
            primary_reasoning_prompt(query)
        )

        fast_task = call_agent(
            "reasoner_fast",
            alternative_reasoning_prompt(query)
        )

        validator_task = call_agent(
            "technical_validator",
            validator_prompt(query)
        )

        primary_reasoning, fast_reasoning, validator = await asyncio.gather(
            primary_task,
            fast_task,
            validator_task
        )

        log_event(state, "round1", "primary_reasoner", primary_reasoning)
        log_event(state, "round1", "alternative_reasoner", fast_reasoning)
        log_event(state, "round1", "technical_validator", validator)

        state["council_size"] = max(3, minimum_council_size or 3)

        state["routing_decision"] = (
            f"HIGH complexity routed to primary reasoner, alternative reasoner, and technical validator "
            f"(analyst requested minimum council size: {minimum_council_size or 3})"
        )

    state["agent_outputs"]["analyst"] = analyst
    state["agent_outputs"]["primary_reasoner"] = primary_reasoning

    if fast_reasoning is not None:
        state["agent_outputs"]["alternative_reasoner"] = fast_reasoning

    if validator is not None:
        state["agent_outputs"]["technical_validator"] = validator

    critic_input = [primary_reasoning]

    if fast_reasoning:
        critic_input.append(fast_reasoning)

    if validator is not None:
        critic_input.append(validator)

    # call critic only when multiple viewpoints exist
    if fast_reasoning is not None:

        critic = await call_agent(
            "critic",
            debate_prompt(query, critic_input)
        )

        log_event(state, "round2", "critic", critic)

        state["agent_outputs"]["critic"] = critic

    else:
        critic = {"skipped": "single viewpoint"}


    answers = {
        "primary_reasoner": primary_reasoning
    }

    if fast_reasoning is not None:
        answers["alternative_reasoner"] = fast_reasoning

    if validator is not None:
        answers["technical_validator"] = validator

    clusters = cluster_answers(answers)

    state["agreement_matrix"] = clusters

    agent_outputs = {
        "primary_reasoner": primary_reasoning
    }

    if fast_reasoning is not None:
        agent_outputs["alternative_reasoner"] = fast_reasoning

    if validator is not None:
        agent_outputs["technical_validator"] = validator

    score = consensus_score(
        clusters,
        answers=answers,
        agent_outputs=agent_outputs
    )

    state["consensus_score"] = score
    state["final_consensus_score"] = score

    state["agreement_history"].append({
        "round": 2,
        "score": score
    })


    if score < 0.6 and fast_reasoning is not None:

        evidence = await call_agent(

            "reasoner_primary",

            evidence_prompt(query, answers)
        )

        log_event(state, "evidence", "primary_reasoner", evidence)

        state["evidence_pool"]["primary_reasoner"] = evidence

        state["evidence_triggered"] = True
        state["evidence_count"] += 1

    revision_context = {
        "answers": answers,
        "critic": critic,
        "consensus_score": score,
        "agreement_matrix": clusters
    }

    revised_positions = {}

    primary_revision = await call_agent(
        "reasoner_primary",
        revision_prompt(query, revision_context)
    )

    log_event(state, "round3", "primary_reasoner_revision", primary_revision)

    state["agent_outputs"]["primary_reasoner_revision"] = primary_revision

    revised_positions["primary_reasoner"] = primary_revision

    if fast_reasoning is not None:

        alternative_revision = await call_agent(
            "reasoner_fast",
            revision_prompt(query, revision_context)
        )

        log_event(state, "round3", "alternative_reasoner_revision", alternative_revision)

        state["agent_outputs"]["alternative_reasoner_revision"] = alternative_revision

        revised_positions["alternative_reasoner"] = alternative_revision

    if validator is not None:

        validator_revision = await call_agent(
            "technical_validator",
            revision_prompt(query, revision_context)
        )

        log_event(state, "round3", "technical_validator_revision", validator_revision)

        state["agent_outputs"]["technical_validator_revision"] = validator_revision

        revised_positions["technical_validator"] = validator_revision

    state["revision_history"] = {}

    for agent_name, revision_output in revised_positions.items():

        original_output = state["agent_outputs"].get(agent_name, {})

        state["revision_history"][agent_name] = {
            "before": original_output.get("proposed_answer", ""),
            "after": revision_output.get(
                "final_position",
                revision_output.get("proposed_answer", "")
            ),
            "confidence_before": original_output.get("confidence"),
            "confidence_after": revision_output.get("confidence")
        }


    revised_answers = {}

    for agent_name, revision_output in revised_positions.items():
        revised_answers[agent_name] = revision_output

    revised_clusters = cluster_answers(revised_answers)

    revised_score = consensus_score(
        revised_clusters,
        answers=revised_answers,
        agent_outputs=revised_positions
    )

    state["agreement_matrix"] = revised_clusters
    state["consensus_score"] = revised_score
    state["final_consensus_score"] = revised_score

    state["agreement_history"].append({
        "round": 3,
        "score": revised_score
    })

    if revised_score >= 0.75:
        state["high_consensus"] = True
    else:
        state["high_consensus"] = False

    try:
        moderator = await call_agent(
            "moderator",
            moderator_prompt(query, {
                "revisions": revised_positions,
                "critic": critic,
                "consensus_score": revised_score,
                "revision_history": state["revision_history"],
                "high_consensus": state["high_consensus"],
                "agreement_matrix": revised_clusters
            })
        )
    except Exception as e:
        moderator = {
            "final_answer": "Moderator unavailable. Returning council consensus.",
            "consensus_score": revised_score,
            "agreement_summary": f"Consensus derived from {len(revised_positions)} revised positions.",
            "error": str(e),
            "agent_role": "moderator_fallback"
        }

    log_event(state, "final", "moderator", moderator)

    state["agent_outputs"]["moderator"] = moderator


    state["final_answer"] = moderator

    if isinstance(moderator, dict):
        moderator["consensus_score"] = state["consensus_score"]

        minority = moderator.get("minority_opinions", [])

        if minority:
            state["minority_positions"] = minority

    end_time = time.time()

    state["execution_metrics"]["end_time"] = end_time
    state["execution_metrics"]["duration"] = round(end_time - start_time, 2)

    return state