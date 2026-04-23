# backend/ai/prompts.py


def investment_explanation_prompt(user_profile, allocation):
    return f"""
User Profile:
Income: {user_profile['income']}
Expenses: {user_profile['expenses']}
Risk: {user_profile['risk']}
Goal: {user_profile['goal']}

Recommended Allocation:
{allocation}

Explain:
1. Why this allocation suits the user
2. Risks involved
3. Long-term benefits

Keep it simple, structured, and practical.
"""


def financial_analysis_prompt(income, expenses, debt, invest_amt, risk, goal, target_amt, target_time):
    return f"""Analyze this financial profile and return ONLY valid JSON (no markdown, no explanation):
Income: {income}
Expenses: {expenses}
Debt: {debt}
Monthly Investment: {invest_amt}
Risk Appetite: {risk}
Financial Goal: {goal}
Target Amount: {target_amt}
Target Timeline: {target_time} months

Return ONLY this JSON format:
{{"financial_health_score": <0-100>, "analysis": "<2-3 sentence insight>", "recommendations": ["<r1>", "<r2>", "<r3>"], "investment_strategy": {{"equity": <0-100>, "debt": <0-100>, "cash": <0-100>}}}}"""