from agent.decision_engine import agent_decision
from agent.what_if import simulate_sip_change
from ai.groq_client import generate_response
from ai.prompts import investment_explanation_prompt


def generate_investment_insight(user_profile, allocation):
    prompt = investment_explanation_prompt(user_profile, allocation)
    
    ai_response = generate_response(prompt)

    return ai_response

def run_agent(goal_intelligence):
    # Guard: if goal_intelligence has an error (incomplete user data), return early
    if not goal_intelligence or "error" in goal_intelligence:
        return {
            "decision": "HOLD",
            "reason": goal_intelligence.get("error", "Insufficient data") if goal_intelligence else "No data"
        }

    decision = agent_decision(goal_intelligence)

    response = {
        "decision": decision,
        "reason": goal_intelligence.get("verdict", "No verdict available")
    }

    if decision in ["ADJUST", "SWITCH"]:
        response["what_if"] = simulate_sip_change(
            current_savings=goal_intelligence.get("monthly_savings", 0),
            target=goal_intelligence.get("target_amount", 0),
            years=10,
            roi=goal_intelligence.get("roi_assumed", 8)
        )

    return response