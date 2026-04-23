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