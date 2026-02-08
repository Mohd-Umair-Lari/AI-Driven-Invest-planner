import requests
from datetime import datetime
from core.market_state import MarketSignal

class MarketAPIAdapter:
    def fetch(self):
        raise NotImplementedError


class VolatilityIndexAdapter(MarketAPIAdapter):
    def __init__(self, api_url: str):
        self.api_url = api_url

    def fetch(self):
        response = requests.get(self.api_url, timeout=5)
        data = response.json()

        value = float(data.get("value", 0))
        change = float(data.get("change", 0))

        direction = "up" if change > 0 else "down" if change < 0 else "neutral"
        magnitude = min(abs(change) / 10, 1)
        confidence = 0.9

        return MarketSignal(
            signal_type="volatility",
            magnitude=round(magnitude, 3),
            direction=direction,
            confidence=confidence,
            timestamp=datetime.utcnow()
        )
    
class MockVolatilityAdapter(MarketAPIAdapter):
    def fetch(self):
        return MarketSignal(
            signal_type="volatility",
            magnitude=0.7,
            direction="up",
            confidence=0.85,
            timestamp=datetime.utcnow()
        )