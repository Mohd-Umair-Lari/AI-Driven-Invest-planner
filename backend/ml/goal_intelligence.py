import math
from utils.data_normalizer import normalize_user
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