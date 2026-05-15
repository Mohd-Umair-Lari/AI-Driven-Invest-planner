

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
    monthly_invest = round(savings * 0.6)

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

    return f

def financial_analysis_prompt(income, expenses, debt, invest_amt, risk, goal, target_amt, target_time):
    savings      = max(0, income - expenses)
    savings_rate = round((savings / income * 100), 1) if income > 0 else 0
    debt_ratio   = round(debt / income, 2) if income > 0 else 0

    return f