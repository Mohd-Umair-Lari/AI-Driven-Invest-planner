def agent_decision(goal_intelligence):
    p = goal_intelligence.get("goal_probability",0)
    if p >= 80:
        return {
            "action": "HOLD",
            "message": "Your goal is on track. Continue current plan."
        }
    if 50 <= p < 80:
        return {
            "action": "ADJUST",
            "message": "Increase SIP slightly or extend tenure to improve success probability."
        }
    if 30 <= p < 50:
        return {
            "action": "SWITCH",
            "message": "Current strategy is weak. Consider higher savings or different instruments."
        }
    return {
        "action": "ABORT",
        "message": "Goal is unrealistic under current conditions. Redefine goal or timeline."
    }