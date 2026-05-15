
import math
from typing import Dict, Any

def sip_future_value(monthly_amount: float, annual_rate: float, years: float) -> Dict[str, Any]:

    if monthly_amount <= 0 or years <= 0:
        return {"future_value": 0, "total_invested": 0, "total_gain": 0}

    r = (annual_rate / 100) / 12
    n = years * 12
    if r == 0:
        fv = monthly_amount * n
    else:
        fv = monthly_amount * (((1 + r) ** n - 1) / r) * (1 + r)

    invested = monthly_amount * n
    return {
        "future_value":   round(fv, 2),
        "total_invested": round(invested, 2),
        "total_gain":     round(fv - invested, 2),
        "xirr_approx":    round(annual_rate, 1),
    }

def emi_calculator(principal: float, annual_rate: float, months: int) -> Dict[str, Any]:

    if principal <= 0 or months <= 0:
        return {"emi": 0, "total_payment": 0, "total_interest": 0}

    r = (annual_rate / 100) / 12
    if r == 0:
        emi = principal / months
    else:
        emi = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)

    total = emi * months
    return {
        "emi":            round(emi, 2),
        "total_payment":  round(total, 2),
        "total_interest": round(total - principal, 2),
        "principal":      round(principal, 2),
    }

def goal_feasibility(
    target_amount: float,
    monthly_invest: float,
    years: float,
    annual_rate: float = 12.0,
) -> Dict[str, Any]:

    result = sip_future_value(monthly_invest, annual_rate, years)
    fv = result["future_value"]
    probability = min(100, round((fv / target_amount) * 100, 1)) if target_amount > 0 else 0
    shortfall = max(0, target_amount - fv)

    r = (annual_rate / 100) / 12
    n = years * 12
    if r == 0 or n == 0:
        required_sip = target_amount / n if n > 0 else 0
    else:
        required_sip = target_amount / (((1 + r) ** n - 1) / r * (1 + r))

    return {
        "projected_value":   round(fv, 2),
        "target_amount":     round(target_amount, 2),
        "probability_pct":   probability,
        "shortfall":         round(shortfall, 2),
        "required_monthly_sip": round(required_sip, 2),
        "current_monthly_sip":  round(monthly_invest, 2),
        "years":             years,
    }

def savings_rate(income: float, expenses: float) -> Dict[str, Any]:

    surplus = max(0, income - expenses)
    rate = round(surplus / income * 100, 1) if income > 0 else 0
    return {
        "monthly_surplus": round(surplus, 2),
        "savings_rate_pct": rate,
        "expense_ratio_pct": round(expenses / income * 100, 1) if income > 0 else 0,
    }
