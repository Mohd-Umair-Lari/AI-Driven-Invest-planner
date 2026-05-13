"""
agents/goal_planner.py
-----------------------
Handles goal planning, SIP calculation, and EMI queries.
Uses deterministic calculator tools, then asks LLM to explain.
"""
from typing import Any, Dict

from agents.base_agent import BaseAgent, AgentResult, Tool
from agents.tools.calculator import sip_future_value, emi_calculator, goal_feasibility
from ai.groq_client import generate_response


class GoalPlannerAgent(BaseAgent):
    name = "GoalPlannerAgent"
    description = "Plans financial goals, calculates SIPs, EMIs, and goal probability."

    def __init__(self):
        self.tools = [
            Tool("sip_calculator",      "Compute SIP future value",      sip_future_value,
                 ["monthly_amount", "annual_rate", "years"]),
            Tool("emi_calculator",      "Compute loan EMI",              emi_calculator,
                 ["principal", "annual_rate", "months"]),
            Tool("goal_feasibility",    "Check goal achievability",      goal_feasibility,
                 ["target_amount", "monthly_invest", "years"]),
        ]

    def run(
        self,
        query: str,
        user_context: Dict[str, Any],
        intent_entities: Dict[str, Any],
    ) -> AgentResult:

        income       = user_context.get("income", 0)
        invest_amt   = user_context.get("invest_amount", 0)
        target_amt   = user_context.get("target_amount", 0)
        target_months = user_context.get("target_months", 60)
        debt         = user_context.get("debt", 0)
        years        = round(target_months / 12, 1)

        # ── Run deterministic tools ─────────────────────────────
        calc_data = {}
        q = query.lower()

        if any(k in q for k in ["emi", "loan", "repay"]):
            calc_data = emi_calculator(debt, annual_rate=12.0, months=min(target_months, 60))
            tool_used = "emi_calculator"
        elif invest_amt > 0 and target_amt > 0:
            calc_data = goal_feasibility(target_amt, invest_amt, years)
            tool_used = "goal_feasibility"
        else:
            calc_data = sip_future_value(income * 0.2, annual_rate=12.0, years=years)
            tool_used = "sip_calculator"

        # ── Build explain prompt ────────────────────────────────
        prompt = (
            f"You are FinPass AI. Here are the exact calculated numbers for this user:\n\n"
            f"{calc_data}\n\n"
            f"User goal: {user_context.get('goal_name', 'Wealth Building')}\n"
            f"User question: {query}\n\n"
            f"Explain these numbers clearly in 2-3 sentences. Be encouraging. Reference exact ₹ values."
        )

        try:
            explanation = generate_response(prompt)
        except Exception as e:
            explanation = f"Goal projection: {calc_data}"

        return AgentResult(
            success=True,
            response=explanation,
            data=calc_data,
            tool_used=tool_used,
            agent_name=self.name,
        )
