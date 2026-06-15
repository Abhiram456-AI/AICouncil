import asyncio
import json
import time

from council.orchestrator import run_council


TEST_QUERY = """
Will AGI arrive before 2035?.
"""


async def main():

    print("\n==============================")
    print(" AI COUNCIL TEST STARTED")
    print("==============================\n")

    print("Query:")
    print(TEST_QUERY)
    print("\nCouncil is deliberating...\n")

    start_time = time.time()

    result = await run_council(TEST_QUERY)

    execution_metrics = result.get("execution_metrics", {})

    end_time = time.time()

    print("\n==============================")
    print(" COUNCIL ROUTING")
    print("==============================\n")

    print(f"Complexity: {result.get('complexity')}")
    print(f"Council Size: {result.get('council_size')}")
    print(f"Routing: {result.get('routing_decision')}")


    print("\n==============================")
    print(" ACTIVE MODELS")
    print("==============================\n")

    print(json.dumps(result.get("active_models", {}), indent=2))

    print("\n==============================")
    print(" FINAL OUTPUT")
    print("==============================\n")

    print(json.dumps(result["final_answer"], indent=2))


    print("\n==============================")
    print(" CONSENSUS SCORE")
    print("==============================\n")

    print(result["consensus_score"])

    print("\n==============================")
    print(" AGREEMENT HISTORY")
    print("==============================\n")

    print(json.dumps(result.get("agreement_history", []), indent=2))


    print("\n==============================")
    print(" MINORITY POSITIONS")
    print("==============================\n")

    print(json.dumps(result.get("minority_positions", []), indent=2))


    print("\n==============================")
    print(" AGREEMENT MATRIX")
    print("==============================\n")

    print(json.dumps(result["agreement_matrix"], indent=2))


    print("\n==============================")
    print(" AGENT OUTPUTS")
    print("==============================\n")

    agent_outputs = result.get("agent_outputs", {})

    for role, output in agent_outputs.items():

        model = "unknown"

        if isinstance(output, dict):
            model = output.get("model", "unknown")

        print(f"{role} -> {model}")

    print()

    print("Detailed Agent Metadata:")

    metadata = {}

    for role, output in agent_outputs.items():

        if isinstance(output, dict):
            metadata[role] = {
                "model": output.get("model", "unknown"),
                "agent_role": output.get("agent_role", role),
                "confidence": output.get("confidence", "N/A")
            }

    print(json.dumps(metadata, indent=2))


    print("\n==============================")
    print(" PARLIAMENT LOG")
    print("==============================\n")

    for step in result["discussion_log"]:

        print(f"\n--- {step['round']} | {step['agent']} ---")

        print(json.dumps(step["payload"], indent=2))


    print("\n==============================")
    print(" EXECUTION METRICS")
    print("==============================\n")

    print(f"Wall Clock Time: {round(end_time - start_time, 2)} seconds")

    if execution_metrics:
        print(json.dumps(execution_metrics, indent=2))

    print()


if __name__ == "__main__":

    asyncio.run(main())