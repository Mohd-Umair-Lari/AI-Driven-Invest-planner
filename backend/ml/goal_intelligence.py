import math

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
def compute_goal_intelligence(user):
# 1. Data Extraction
    try:
        u=normalize_user(user)
        monthly_income = u['monthly_income']
        monthly_expenses = u['monthly_expenses']
        monthly_savings = monthly_income - monthly_expenses

        target_amount = u["goal_amount"]
        target_time_months = u["goal_time_months"]

        risk_level = u["risk_level"]
    except Exception:
        return {
            "error": "Insufficient data to compute goal intelligence"
        }
    if monthly_savings <= 0 or target_time_months <= 0 or target_amount <= 0:
        return {
            "error": "Invalid financial values"
        }
# 2. Risk → ROI mapping
    risk_roi_map = {
        "Low": 6,
        "Moderate": 10,
        "High": 14
    }

    annual_roi = risk_roi_map.get(risk_level, 8)
    monthly_roi = annual_roi / 12 / 100  # convert % to decimal

# 3. SIP Future Value
    n = target_time_months
    P = monthly_savings
    r = monthly_roi

    future_value = P * ((math.pow(1 + r, n) - 1) / r)

# 4. Probability & Gap
    probability = min((future_value / target_amount) * 100, 120)
    gap = future_value - target_amount

# 5. Verdict
    if probability >= 100:
        verdict = "Goal Achievable"
    elif probability >= 75:
        verdict = "On Track but Needs Discipline"
    elif probability >= 50:
        verdict = "High Risk – Needs Adjustment"
    else:
        verdict = "Goal Unlikely Without Changes"

# 6. Final Output
    return {
        "monthly_savings": monthly_savings,
        "expected_corpus": int(future_value),
        "target_amount": target_amount,
        "gap": int(gap),
        "goal_probability": round(probability, 2),
        "risk_level": risk_level,
        "roi_assumed": annual_roi,
        "verdict": verdict
    }