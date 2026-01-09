from agent.decision_engine import agent_decision
from agent.what_if import simulate_sip_change

def run_agent(goal_intelligence):
    decision = agent_decision(goal_intelligence)

    response = {
        "decision": decision,
        "reason": goal_intelligence["verdict"]
    }

    if decision in ["ADJUST", "SWITCH"]:
        response["what_if"] = simulate_sip_change(
            current_savings=goal_intelligence["monthly_savings"],
            target=goal_intelligence["target_amount"],
            years=10,
            roi=goal_intelligence["roi_assumed"]
        )

    return response