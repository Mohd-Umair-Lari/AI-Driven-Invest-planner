# backend/ai/prompts.py


def investment_explanation_prompt(user_profile, allocation):
    income   = user_profile.get('income', 0)
    expenses = user_profile.get('expenses', 0)
    risk     = user_profile.get('risk', 'moderate')
    goal     = user_profile.get('goal', 'Wealth Building')

    savings        = max(0, income - expenses)
    savings_rate   = round((savings / income * 100), 1) if income > 0 else 0
    equity_pct     = allocation.get('equity', 30)
    debt_pct       = allocation.get('debt', 50)
    cash_pct       = allocation.get('cash', 20)
    monthly_invest = round(savings * 0.6)   # invest 60% of surplus

    # Classify user financial tier for tailored advice
    if income < 20000:
        tier = "entry-level / working class"
    elif income < 75000:
        tier = "lower-middle class"
    elif income < 200000:
        tier = "middle class"
    elif income < 500000:
        tier = "upper-middle class"
    else:
        tier = "high-income / business class"

    return f"""You are a senior certified financial planner advising an Indian investor.

=== CLIENT FINANCIAL SNAPSHOT ===
Monthly Income    : ₹{income:,.0f}
Monthly Expenses  : ₹{expenses:,.0f}
Monthly Savings   : ₹{savings:,.0f}  ({savings_rate}% savings rate)
Financial Tier    : {tier}
Risk Appetite     : {risk}
Primary Goal      : {goal}

Recommended Portfolio Split
  Equity : {equity_pct}%
  Debt   : {debt_pct}%
  Cash   : {cash_pct}%

=== YOUR TASK ===
Write a STRUCTURED, ACTIONABLE financial plan in plain English (no JSON, no markdown headers with #).
Use simple section labels like "SECTION 1:", "SECTION 2:", etc.

SECTION 1 — FINANCIAL HEALTH DIAGNOSIS
- Comment on their savings rate ({savings_rate}%). Is it healthy, critical, or exceptional?
- What does their income-to-expense ratio say about their current lifestyle?
- Give an honest 1-paragraph assessment they can understand without being a finance expert.

SECTION 2 — WHY THIS ALLOCATION SUITS THEM
- Explain in plain language why {equity_pct}% equity / {debt_pct}% debt / {cash_pct}% cash is right for their tier and risk level.
- Avoid jargon. Think of explaining it to a first-time investor.

SECTION 3 — MONTHLY INVESTMENT PLAN (Actionable Numbers)
Assume they invest roughly ₹{monthly_invest:,.0f}/month (60% of their savings surplus).
Break it down by instrument with approximate amounts:
- SIP in Mutual Funds (Equity): ₹X/month — suggest 1-2 specific fund categories (e.g., large-cap index, flexi-cap)
- Recurring Deposit / Debt Fund: ₹X/month
- Emergency / Liquid Fund: ₹X/month
- PPF / NPS (if applicable): ₹X/month

SECTION 4 — QUARTERLY ACTIONS (Every 3 months)
List 3-4 concrete tasks they should do every quarter:
- Portfolio rebalancing check
- SIP top-up consideration
- Expense audit
- Insurance / term plan review (if they don't have one)

SECTION 5 — ANNUAL MILESTONES
- Tax-saving investments before 31 March (ELSS, PPF, NPS under 80C)
- Annual goal progress review: are they on track for "{goal}"?
- When to step up SIP (salary hike rule: increase SIP by 10-15% each year)

SECTION 6 — WEALTH-BUILDING TACTICS FOR THEIR TIER
Based on their tier ({tier}), give 3-5 specific tactics:
  - For entry-level/working class: micro-SIPs, chit funds, post office schemes, gold bonds
  - For middle class: index funds, term insurance, home loan vs rent analysis
  - For upper-middle/business class: direct equity, REITs, international funds, tax harvesting

SECTION 7 — TOP 3 RISKS TO WATCH
List the 3 biggest financial risks for this specific profile and one mitigation tip for each.

Keep the tone warm, motivating, and practical. End with one powerful one-liner that motivates the user to start today.
"""


def financial_analysis_prompt(income, expenses, debt, invest_amt, risk, goal, target_amt, target_time):
    savings      = max(0, income - expenses)
    savings_rate = round((savings / income * 100), 1) if income > 0 else 0
    debt_ratio   = round(debt / income, 2) if income > 0 else 0

    return f"""You are a financial analyst. Analyze this profile and return ONLY valid JSON (no markdown, no explanation).

Profile:
- Monthly Income   : {income}
- Monthly Expenses : {expenses}
- Monthly Savings  : {savings} ({savings_rate}% savings rate)
- Total Debt       : {debt} (debt-to-income ratio: {debt_ratio}x monthly income)
- Monthly SIP/Investment : {invest_amt}
- Risk Appetite    : {risk}
- Financial Goal   : {goal}
- Target Amount    : {target_amt}
- Target Timeline  : {target_time} months

Return ONLY this exact JSON (replace placeholders with real values):
{{"financial_health_score": <integer 0-100>, "analysis": "<2-3 sentence honest assessment mentioning savings rate and debt ratio>", "recommendations": ["<specific actionable tip 1>", "<specific actionable tip 2>", "<specific actionable tip 3>"], "investment_strategy": {{"equity": <integer>, "debt": <integer>, "cash": <integer>}}}}

Rules:
- financial_health_score must reflect savings_rate and debt_ratio realistically
- recommendations must be specific (mention SIP amounts, fund types, or debt reduction tactics)
- equity+debt+cash must sum to exactly 100
- No extra keys, no markdown, no explanation outside the JSON"""