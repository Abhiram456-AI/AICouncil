from typing import Dict, Any

def create_initial_state(query: str) -> Dict[str, Any]:

    return {

        "query": query,

        "complexity": None,

        "council_size": None,

        "routing_decision": None,

        "active_models": {},

        "round1_responses": {},

        "debate_comments": {},

        "evidence_pool": {},

        "revised_positions": {},

        "agent_outputs": {},

        "agreement_matrix": {},

        "agreement_history": [],

        "confidence_history": [],

        "minority_positions": [],

        "consensus_score": 0.0,

        "evidence_triggered": False,

        "evidence_count": 0,

        "execution_metrics": {
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "tokens_estimated": 0
        },

        "final_answer": {},

        "discussion_log": []
    }


def log_event(state, round_name, agent, payload):

    state["discussion_log"].append({

        "round": round_name,

        "agent": agent,

        "payload": payload
    })

    return state