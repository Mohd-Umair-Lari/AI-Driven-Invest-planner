from core.rule_engine import RuleEngine
from core.market_state import MarketState
from adapter.market_adapter import MockVolatilityAdapter

class IntelligenceService:
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.market_state = MarketState()
        self.market_adapter = MockVolatilityAdapter()

    def run(self, financial_state):
        signal = self.market_adapter.fetch()
        self.market_state.add_signal(signal)

        insights = self.rule_engine.evaluate(
            financial=financial_state,
            market=self.market_state
        )

        return [i.to_dict() for i in insights]