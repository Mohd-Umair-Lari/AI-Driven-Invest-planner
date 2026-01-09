def get_num(value, default=0):
    if value is None:
        return default
    if isinstance(value, dict):
        return float(list(value.values())[0])
    try:
        return float(value)
    except:
        return default


def normalize_user(user):
    financials = user.get("financials", {})
    goal = user.get("Goal", {})
    investments = user.get("investments", {})

    monthly_income = get_num(financials.get("monthly-income"))
    monthly_expenses = get_num(financials.get("monthly-expenses"))

    return {
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_savings": monthly_income - monthly_expenses,

        "goal_amount": get_num(goal.get("target-amt")),
        "goal_time_months": int(get_num(goal.get("target-time"))),

        "risk_level": investments.get("risk-opt", "Moderate"),

        "investment_amount": get_num(investments.get("invest-amt")),

        "has_emergency_fund": bool(financials.get("em-fund-opted", False))
    }
