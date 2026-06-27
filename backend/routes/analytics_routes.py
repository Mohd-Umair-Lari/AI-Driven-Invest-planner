"""FastAPI analytics routes: financial health, predictions, recommendations."""

import json
import re

from fastapi import APIRouter, HTTPException, Path as FPath

from analytics.financial_analytics import compute_financial_health
from ml.goal_predictor import generate_plan, goal_probability
from ml.goal_intelligence import compute_goal_intelligence
from agent.financial_agent import run_agent
from db import collection, get_num

router = APIRouter(tags=["Analytics"])


@router.get("/api/analytics/{email}")
async def analytics(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(404, "User not found")
    return {"analytics": compute_financial_health(user)}


@router.get("/api/predict/{email}")
async def predict(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(404, "User not found")
    return goal_probability(user)


@router.get("/api/recommend/{email}")
async def recommend(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(404, "User not found")
    return {"recommended_plan": generate_plan(user)}


@router.get("/api/goal-intelligence/{email}")
async def goal_intelligence(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(404, "User not found")
    return {"goal_intelligence": compute_goal_intelligence(user)}


@router.get("/api/agent/{email}", tags=["Agent"])
async def agent_api(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(404, "User not found")
    try:
        intel = compute_goal_intelligence(user)
        resp = run_agent(intel) or {
            "action": "HOLD",
            "message": "No data",
            "reason": "Incomplete profile",
        }
        return {"goal_intelligence": intel, "agent": resp}
    except Exception as e:
        return {"agent": {"action": "ERROR", "message": "Failed", "reason": str(e)}}


@router.get("/api/recommended-actions/{email}")
async def recommended_actions(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(404, "User not found")

    fin = user.get("financials") or {}
    inv = user.get("investments") or {}
    goal = user.get("Goal") or {}
    health = compute_financial_health(user)

    income = get_num(fin, "monthly-income")
    expenses = get_num(fin, "monthly-expenses")
    debt = get_num(fin, "debt")
    invest_amt = get_num(inv, "invest-amt")
    risk = (inv.get("risk-opt") or "moderate").lower()
    timeline = get_num(goal, "target-time")
    target_amt = get_num(goal, "target-amt")
    goal_name = goal.get("goal", "your goal")
    sav_ratio = health.get("savings_ratio", 0)
    exp_ratio = health.get("expense_ratio", 0)
    fin_health = health.get("financial_health", "")
    surplus = max(0, income - expenses - debt)

    actions = []

    # Emergency fund check
    em_fund = fin.get("em-fund-opted", False)
    if not em_fund or surplus < 5000:
        months_covered = (invest_amt / expenses) if expenses > 0 else 0
        if months_covered < 3:
            actions.append({
                "title": "Build Your Emergency Fund",
                "subtitle": (
                    f"You have less than 3 months of expenses (₹{expenses:,.0f}/mo) "
                    f"saved as a buffer. Aim for ₹{expenses * 6:,.0f}."
                ),
                "priority": 1,
                "tag": "Critical",
                "color": "red",
            })

    # Expense ratio check
    if exp_ratio > 0.75 and income > 0:
        over_spend = expenses - (income * 0.6)
        actions.append({
            "title": "Reduce Monthly Expenses",
            "subtitle": (
                f"You're spending {exp_ratio * 100:.0f}% of income on expenses. "
                f"Cutting ₹{over_spend:,.0f}/mo could free up significant savings."
            ),
            "priority": 1 if exp_ratio > 0.85 else 2,
            "tag": "High Priority",
            "color": "orange",
        })

    # Debt ratio check
    debt_ratio = debt / income if income > 0 else 0
    if debt_ratio > 0.4:
        actions.append({
            "title": "Accelerate Debt Repayment",
            "subtitle": (
                f"Your EMI/debt (₹{debt:,.0f}) is {debt_ratio * 100:.0f}% of income. "
                f"Prioritise clearing high-interest debt before increasing investments."
            ),
            "priority": 2,
            "tag": "Debt Alert",
            "color": "red",
        })

    # SIP recommendations
    if sav_ratio > 0.25 and invest_amt > 0:
        sip_boost = round(invest_amt * 0.10 / 500) * 500
        actions.append({
            "title": f"Increase SIP by ₹{sip_boost:,.0f}/mo",
            "subtitle": (
                f"Your savings rate is healthy at {sav_ratio * 100:.0f}%. "
                f"A 10% SIP step-up each year can significantly accelerate your corpus."
            ),
            "priority": 3,
            "tag": "Growth",
            "color": "green",
        })
    elif sav_ratio > 0.1 and invest_amt == 0:
        invest_suggestion = round(surplus * 0.5 / 500) * 500
        actions.append({
            "title": "Start a SIP Investment",
            "subtitle": (
                f"You have a monthly surplus of ₹{surplus:,.0f}. "
                f"Starting a SIP of ₹{invest_suggestion:,.0f}/mo can help build long-term wealth."
            ),
            "priority": 2,
            "tag": "Action Required",
            "color": "indigo",
        })

    # Goal gap analysis
    if target_amt > 0 and timeline > 0 and income > 0:
        required_monthly = target_amt / timeline
        if invest_amt < required_monthly * 0.8:
            gap = required_monthly - invest_amt
            actions.append({
                "title": f"Top-up Investment for '{goal_name}'",
                "subtitle": (
                    f"To reach ₹{target_amt:,.0f} in {int(timeline)} months you need "
                    f"~₹{required_monthly:,.0f}/mo. Current SIP is ₹{invest_amt:,.0f} — "
                    f"gap of ₹{gap:,.0f}."
                ),
                "priority": 2,
                "tag": "Goal Gap",
                "color": "amber",
            })
        else:
            actions.append({
                "title": f"Stay the Course on '{goal_name}'",
                "subtitle": (
                    f"You're on track! Keep your ₹{invest_amt:,.0f} SIP consistent "
                    f"and review the plan every 6 months."
                ),
                "priority": 4,
                "tag": "On Track",
                "color": "green",
            })

    # Risk-age alignment
    age = get_num(user, "Age")
    if age > 50 and risk in ("aggressive", "high"):
        actions.append({
            "title": "Review Risk Appetite",
            "subtitle": (
                f"At age {int(age)}, an aggressive risk profile may expose you to "
                f"significant volatility. Consider shifting 20-30% to debt/balanced funds."
            ),
            "priority": 3,
            "tag": "Risk Review",
            "color": "amber",
        })
    elif age < 30 and risk in ("conservative", "low"):
        actions.append({
            "title": "Consider Higher-Growth Assets",
            "subtitle": (
                f"At age {int(age)}, a conservative strategy may limit your long-term wealth. "
                f"Consider allocating 40-60% to equity for better returns."
            ),
            "priority": 3,
            "tag": "Opportunity",
            "color": "indigo",
        })

    # Tax saving suggestion
    if income > 50000:
        actions.append({
            "title": "Maximise 80C Deductions",
            "subtitle": (
                f"With ₹{income:,.0f} monthly income, ensure you're fully using "
                f"your ₹1.5L annual 80C limit via ELSS, PPF, or life insurance."
            ),
            "priority": 4,
            "tag": "Tax Saving",
            "color": "indigo",
        })

    # Fallback
    if not actions:
        actions.append({
            "title": "Complete Your Financial Profile",
            "subtitle": "Add your income, expenses, and investment details to receive personalised recommendations.",
            "priority": 1,
            "tag": "Setup Required",
            "color": "slate",
        })

    actions.sort(key=lambda x: x["priority"])
    return {"actions": actions[:5], "financial_health": fin_health, "savings_ratio": sav_ratio}


@router.get("/api/analyze-finances/{email}")
async def analyze_finances(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(404, "User not found")

    fin = user.get("financials", {})
    goal = user.get("Goal", {})
    inv = user.get("investments", {})
    income = float(fin.get("monthly-income") or 0)
    expenses = float(fin.get("monthly-expenses") or 0)
    debt = float(fin.get("debt") or 0)
    invest_amt = float(inv.get("invest-amt") or 0)
    risk = goal.get("risk", "moderate")

    if income == 0:
        raise HTTPException(400, "Please complete your financial profile first")

    allocation = {
        "equity": 60 if risk == "high" else 50 if risk == "medium" else 30,
        "debt": 25 if risk == "high" else 35 if risk == "medium" else 50,
        "cash": 15,
    }

    try:
        from ai.groq_client import generate_response
        from ai.formatter import clean_response

        prompt = (
            f"Analyze and return ONLY valid JSON:\n"
            f"Income:{income} Expenses:{expenses} Debt:{debt} Invest:{invest_amt} Risk:{risk}\n"
            f"Goal:{goal.get('goal', 'Wealth Building')} Target:{goal.get('target-amt', 0)} "
            f"in {goal.get('target-time', 0)} months\n"
            f'Return: {{"financial_health_score":<0-100>,"analysis":"...","recommendations":["..."],'
            f'"investment_strategy":{{"equity":<n>,"debt":<n>,"cash":<n>}}}}'
        )
        raw = generate_response(prompt)
        return json.loads(clean_response(re.sub(r"```json|```", "", raw)))
    except Exception:
        sr = (income - expenses) / income if income else 0
        dr = debt / income if income else 0
        score = (
            50
            + (25 if sr > 0.3 else 0)
            + (15 if dr < 1 else 0)
            + (10 if expenses < income * 0.7 else 0)
        )
        recs = []
        if dr > 2:
            recs.append("Focus on reducing high-interest debt first")
        if sr < 0.1:
            recs.append("Aim to save at least 20% of monthly income")
        if not recs:
            recs = ["Continue your current plan", "Monitor expenses regularly"]
        return {
            "financial_health_score": min(100, score),
            "analysis": f"Savings rate: {sr * 100:.1f}%.",
            "recommendations": recs[:3],
            "investment_strategy": allocation,
        }
