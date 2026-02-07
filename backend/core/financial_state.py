from dataclasses import dataclass
from typing import Dict

@dataclass
class FinancialState:
    income: float
    expenses: float
    savings: float
    debt: float
    risk_score: float
    investment_exposure: float
    goal_horizon_months: int
    emergency_fund_months: float

    def liquidity_ratio(self) -> float:
        if self.expenses == 0:
            return 0.0
        return self.savings / self.expenses

    def debt_to_income(self) -> float:
        if self.income == 0:
            return 0.0
        return self.debt / self.income

    def stability_score(self) -> float:
        liquidity = min(self.liquidity_ratio() / 6, 1)
        debt_penalty = min(self.debt_to_income(), 1)
        emergency = min(self.emergency_fund_months / 6, 1)

        score = (
            0.4 * liquidity +
            0.3 * emergency +
            0.3 * (1 - debt_penalty)
        )

        return round(score, 3)

    def to_vector(self) -> list:
        return [
            self.income,
            self.expenses,
            self.savings,
            self.debt,
            self.risk_score,
            self.investment_exposure,
            self.goal_horizon_months,
            self.emergency_fund_months,
            self.liquidity_ratio(),
            self.debt_to_income(),
            self.stability_score()
        ]

    def to_dict(self) -> Dict:
        return {
            "income": self.income,
            "expenses": self.expenses,
            "savings": self.savings,
            "debt": self.debt,
            "risk_score": self.risk_score,
            "investment_exposure": self.investment_exposure,
            "goal_horizon_months": self.goal_horizon_months,
            "emergency_fund_months": self.emergency_fund_months,
            "liquidity_ratio": self.liquidity_ratio(),
            "debt_to_income": self.debt_to_income(),
            "stability_score": self.stability_score()
        }