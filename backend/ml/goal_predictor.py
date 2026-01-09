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
    goal_amt = user["Goal"]["target-amt"]
    months = user["Goal"]["target-time"]
    invest = user["investments"]["invest-amt"]

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
    risk = user["investments"]["risk-opt"]
    invest_amt = user["investments"]["invest-amt"]

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