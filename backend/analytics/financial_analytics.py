def get_num(v, default=0):
    if v is None:
        return default
    if isinstance(v, dict):
        return float(list(v.values())[0])
    try:
        return float(v)
    except:
        return default
    
def compute_financial_health(user):
    income = get_num(user.get("financials", {}).get("monthly-income"))
    expenses = get_num(user.get("financials", {}).get("monthly-expenses"))
    savings = get_num(user.get("financials", {}).get("monthly_savings"))
    debt = get_num(user.get("financials", {}).get("debt"))

    # Guard against division by zero
    savings_ratio = savings / income if income > 0 else 0
    expense_ratio = expenses / income if income > 0 else 0

    # Simple health logic (can evolve later)
    if savings_ratio >= 0.3:
        financial_health = "Excellent"
    elif savings_ratio >= 0.2:
        financial_health = "Good"
    elif savings_ratio > 0:
        financial_health = "Needs Improvement"
    else:
        financial_health = "Critical"

    # Risk score (0–100)
    risk_score = min(100, max(0, (expense_ratio * 100)))

    return {
        "financial_health": financial_health,
        "savings_ratio": round(savings_ratio, 2),
        "expense_ratio": round(expense_ratio, 2),
        "risk_score": round(risk_score, 1)
    }
