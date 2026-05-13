"""
orchestrator/intent_classifier.py
----------------------------------
Lightweight rule-based + keyword intent classifier.
Routes user queries to the correct agent/tool without burning LLM tokens.
Designed to be replaced by a fine-tuned classifier later.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class Intent(str, Enum):
    # Spending / budget
    SPENDING_QUERY       = "spending_query"       # "how much did I spend on food?"
    BUDGET_ADVICE        = "budget_advice"         # "how can I save more?"
    EXPENSE_BREAKDOWN    = "expense_breakdown"     # "show my expenses"

    # Investment
    INVESTMENT_QUERY     = "investment_query"      # "where should I invest?"
    PORTFOLIO_ANALYSIS   = "portfolio_analysis"    # "analyze my portfolio"
    MARKET_QUERY         = "market_query"          # "how is Nifty doing?"

    # Goals
    GOAL_PLANNING        = "goal_planning"         # "will I reach my goal?"
    SIP_CALCULATION      = "sip_calculation"       # "calculate my SIP"
    EMI_CALCULATION      = "emi_calculation"       # "what is my EMI?"

    # Financial health
    HEALTH_ANALYSIS      = "health_analysis"       # "what's my financial health?"
    DEBT_ADVICE          = "debt_advice"           # "how to reduce my debt?"

    # General / fallback
    GENERAL_ADVICE       = "general_advice"        # catch-all
    GREETING             = "greeting"


@dataclass
class ClassifiedIntent:
    intent: Intent
    confidence: float
    entities: dict
    agent: str   # which agent should handle this


# ── Keyword maps ───────────────────────────────────────────────
_INTENT_RULES: List[tuple] = [
    # (keywords, intent, agent)
    (["spend", "spent", "food", "grocery", "groceries", "rent", "dining",
      "transport", "medical", "shopping", "entertainment", "category"],
     Intent.SPENDING_QUERY, "BudgetOptimizerAgent"),

    (["save", "saving", "savings rate", "cut", "reduce expenses", "budget"],
     Intent.BUDGET_ADVICE, "BudgetOptimizerAgent"),

    (["invest", "investment", "mutual fund", "sip", "stock", "equity",
      "portfolio", "where to put", "allocate"],
     Intent.INVESTMENT_QUERY, "FinancialAnalystAgent"),

    (["portfolio", "holdings", "returns", "performance", "asset"],
     Intent.PORTFOLIO_ANALYSIS, "FinancialAnalystAgent"),

    (["goal", "target", "reach", "achieve", "retire", "retirement"],
     Intent.GOAL_PLANNING, "GoalPlannerAgent"),

    (["sip calculator", "calculate sip", "sip amount", "monthly sip"],
     Intent.SIP_CALCULATION, "GoalPlannerAgent"),

    (["emi", "loan", "home loan", "car loan", "personal loan"],
     Intent.EMI_CALCULATION, "GoalPlannerAgent"),

    (["health", "score", "healthy", "financial health", "how am i doing"],
     Intent.HEALTH_ANALYSIS, "FinancialAnalystAgent"),

    (["debt", "loan", "owe", "repay", "pay off"],
     Intent.DEBT_ADVICE, "BudgetOptimizerAgent"),

    (["hi", "hello", "hey", "good morning", "good evening", "namaste"],
     Intent.GREETING, "general"),

    (["expense", "breakdown", "spending breakdown", "monthly expenses"],
     Intent.EXPENSE_BREAKDOWN, "BudgetOptimizerAgent"),
]


def classify_intent(query: str) -> ClassifiedIntent:
    """
    O(n) rule-based classifier — fast and deterministic.
    Returns the best matching intent with which agent should handle it.
    """
    q = query.lower()
    best_score = 0
    best_intent = Intent.GENERAL_ADVICE
    best_agent  = "FinancialAnalystAgent"

    for keywords, intent, agent in _INTENT_RULES:
        score = sum(1 for kw in keywords if kw in q)
        if score > best_score:
            best_score = best_intent = None
            best_score = score
            best_intent = intent
            best_agent  = agent

    confidence = min(1.0, best_score / 3) if best_score > 0 else 0.3

    # ── Entity extraction ──────────────────────────────────────
    entities: dict = {}
    spending_cats = ["food", "rent", "transport", "medical", "entertainment",
                     "shopping", "groceries", "utilities", "insurance"]
    for cat in spending_cats:
        if cat in q:
            entities["category"] = cat
            break

    return ClassifiedIntent(
        intent=best_intent,
        confidence=confidence,
        entities=entities,
        agent=best_agent,
    )
