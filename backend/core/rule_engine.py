from typing import List
from core.financial_state import FinancialState
from core.market_state import MarketState
from core.insight import InsightFactory

class RuleEngine:
    def evaluate(self, financial: FinancialState, market: MarketState) -> List:
        insights = []

        insights.extend(self._volatility_risk_rule(financial, market))
        insights.extend(self._liquidity_rule(financial))
        insights.extend(self._debt_rule(financial))
        insights.extend(self._stability_rule(financial))

        return insights

    def _volatility_risk_rule(self, financial: FinancialState, market: MarketState) -> List:
        insights = []
        volatility = market.aggregate_magnitude("volatility")
        confidence = market.confidence_score("volatility")

        if volatility > 0.6 and financial.risk_score < 0.4:
            insights.append(
                InsightFactory.threat(
                    message="Elevated market volatility may impact low-risk portfolios",
                    severity="high",
                    impact_area="risk",
                    confidence=confidence
                )
            )

        return insights

    def _liquidity_rule(self, financial: FinancialState) -> List:
        insights = []

        if financial.liquidity_ratio() < 3:
            insights.append(
                InsightFactory.threat(
                    message="Low liquidity buffer detected relative to monthly expenses",
                    severity="medium",
                    impact_area="liquidity",
                    confidence=0.8
                )
            )

        return insights

    def _debt_rule(self, financial: FinancialState) -> List:
        insights = []

        if financial.debt_to_income() > 0.5:
            insights.append(
                InsightFactory.threat(
                    message="High debt-to-income ratio may reduce financial flexibility",
                    severity="high",
                    impact_area="stability",
                    confidence=0.85
                )
            )

        return insights

    def _stability_rule(self, financial: FinancialState) -> List:
        insights = []

        score = financial.stability_score()

        if score >= 0.75:
            insights.append(
                InsightFactory.stability(
                    message="Overall financial position appears stable",
                    severity="low",
                    impact_area="stability",
                    confidence=0.9
                )
            )

        if score < 0.4:
            insights.append(
                InsightFactory.threat(
                    message="Overall financial stability is under pressure",
                    severity="high",
                    impact_area="stability",
                    confidence=0.9
                )
            )

        return insights