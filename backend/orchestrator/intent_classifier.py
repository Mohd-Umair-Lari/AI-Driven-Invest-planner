
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class Intent(str, Enum):

    SPENDING_QUERY       = "spending_query"
    BUDGET_ADVICE        = "budget_advice"
    EXPENSE_BREAKDOWN    = "expense_breakdown"

    INVESTMENT_QUERY     = "investment_query"
    PORTFOLIO_ANALYSIS   = "portfolio_analysis"
    MARKET_QUERY         = "market_query"

    GOAL_PLANNING        = "goal_planning"
    SIP_CALCULATION      = "sip_calculation"
    EMI_CALCULATION      = "emi_calculation"

    HEALTH_ANALYSIS      = "health_analysis"
    DEBT_ADVICE          = "debt_advice"

    GENERAL_ADVICE       = "general_advice"
    GREETING             = "greeting"

@dataclass
class ClassifiedIntent:
    intent: Intent
    confidence: float
    entities: dict
    agent: str

_INTENT_RULES: List[tuple] = [

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
