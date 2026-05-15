import random

def simulate_goal(
    monthly_invest,
    months,
    expected_return=0.12,
    volatility=0.08,
    simulations=1000
):
    results = []

    for _ in range(simulations):
        value = 0
        for _ in range(months):
            monthly_return = random.gauss(
                expected_return / 12,
                volatility / (12 ** 0.5)
            )
            value = value * (1 + monthly_return) + monthly_invest
        results.append(value)

    return results

def goal_probability(user):
    try:
        goal_amt = user.get("Goal", {}).get("target-amt", 0)
        months = user.get("Goal", {}).get("target-time", 12)
        invest = user.get("investments", {}).get("invest-amt", 0)

        if goal_amt <= 0 or months <= 0 or invest <= 0:
            return {"goal_probability": 0, "expected_value": 0}
    except Exception:
        return {"goal_probability": 0, "expected_value": 0}

    results = simulate_goal(invest, months)

    success = sum(1 for r in results if r >= goal_amt)
    probability = success / len(results)

    return {
        "goal_probability": round(probability * 100, 2),
        "expected_value": round(sum(results) / len(results), 2)
    }

def asset_allocation(risk):
    if risk == "Low":
        return {"Equity": 30, "Debt": 60, "Gold": 10}
    if risk == "Moderate":
        return {"Equity": 60, "Debt": 30, "Gold": 10}
    return {"Equity": 80, "Debt": 15, "Gold": 5}

def generate_plan(user):
    risk = user.get("investments", {}).get("risk-opt", "Moderate")
    invest_amt = user.get("investments", {}).get("invest-amt", 0)

    if invest_amt <= 0:
        return {"Equity": 0, "Debt": 0, "Gold": 0}

    allocation = asset_allocation(risk)

    plan = {}
    for asset, pct in allocation.items():
        plan[asset] = round(invest_amt * pct / 100, 2)

    return plan

def should_adjust(user, probability):
    if probability < 50:
        return "Increase tenure or reduce risk"
    if probability < 70:
        return "Increase monthly investment"
    return "No change required"