"""
rag/retriever.py
----------------
Retrieves all relevant financial context for a given user from MongoDB.
Returns structured Python dicts — no AI involved at this stage.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def retrieve_user_context(collection, email: str) -> Dict[str, Any]:
    """
    Fetches full user profile + transaction history.
    This is the 'R' in RAG — pure data retrieval.
    """
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        return {}

    financials   = user.get("financials", {})
    goal         = user.get("Goal", {})
    investments  = user.get("investments", {})
    progress     = user.get("progress", {})

    # ── Core numbers ─────────────────────────────────────────────
    income   = float(financials.get("monthly-income") or 0)
    expenses = float(financials.get("monthly-expenses") or 0)
    debt     = float(financials.get("debt") or 0)
    em_fund  = financials.get("em-fund-opted", False)

    # ── Spending categories (if stored) ──────────────────────────
    spending_categories: Dict[str, float] = financials.get("categories", {})

    # ── Goal info ────────────────────────────────────────────────
    goal_name        = goal.get("goal", "Wealth Building")
    target_amount    = float(goal.get("target-amt") or 0)
    target_months    = int(goal.get("target-time") or 0)
    risk             = goal.get("risk", "moderate")

    # ── Investment info ──────────────────────────────────────────
    invest_mode   = investments.get("prefered-mode", "Monthly SIP")
    invest_amount = float(investments.get("invest-amt") or 0)
    risk_opt      = investments.get("risk-opt", risk)

    # ── Derived metrics ──────────────────────────────────────────
    surplus        = income - expenses
    savings_rate   = round((surplus / income * 100), 1) if income > 0 else 0
    debt_ratio     = round((debt / income), 2) if income > 0 else 0
    months_to_goal = target_months

    # ── Transaction history (if exists) ──────────────────────────
    transactions: List[Dict] = user.get("transactions", [])

    # ── Progress / portfolio snapshot ────────────────────────────
    current_portfolio = float(progress.get("current-portfolio") or 0)
    goal_probability  = float(progress.get("goal-probability") or 0)

    return {
        "name":               user.get("Name", "User"),
        "employment_status":  user.get("employment-status", "Salaried"),
        "age":                user.get("Age", ""),
        "income":             income,
        "expenses":           expenses,
        "debt":               debt,
        "surplus":            surplus,
        "savings_rate":       savings_rate,
        "debt_ratio":         debt_ratio,
        "emergency_fund":     em_fund,
        "spending_categories": spending_categories,
        "transactions":       transactions,
        "goal_name":          goal_name,
        "target_amount":      target_amount,
        "target_months":      target_months,
        "risk":               risk,
        "invest_mode":        invest_mode,
        "invest_amount":      invest_amount,
        "current_portfolio":  current_portfolio,
        "goal_probability":   goal_probability,
    }


def retrieve_transactions_by_category(
    context: Dict[str, Any], category: str
) -> List[Dict]:
    """
    Filter transactions relevant to a specific category keyword.
    E.g., 'food', 'groceries', 'rent', 'entertainment'
    """
    keyword = category.lower()
    return [
        t for t in context.get("transactions", [])
        if keyword in t.get("category", "").lower()
        or keyword in t.get("description", "").lower()
    ]
