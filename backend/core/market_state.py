from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class MarketSignal:
    signal_type: str
    magnitude: float
    direction: str
    confidence: float
    timestamp: datetime

class MarketState:
    def __init__(self):
        self.signals: List[MarketSignal] = []

    def add_signal(self, signal: MarketSignal):
        self.signals.append(signal)

    def recent_signals(self, signal_type: str, window: int = 5) -> List[MarketSignal]:
        filtered = [s for s in self.signals if s.signal_type == signal_type]
        return filtered[-window:]

    def aggregate_magnitude(self, signal_type: str) -> float:
        signals = self.recent_signals(signal_type)
        if not signals:
            return 0.0
        return round(sum(s.magnitude for s in signals) / len(signals), 3)

    def dominant_direction(self, signal_type: str) -> str:
        signals = self.recent_signals(signal_type)
        if not signals:
            return "neutral"
        score = sum(1 if s.direction == "up" else -1 for s in signals)
        if score > 0:
            return "up"
        if score < 0:
            return "down"
        return "neutral"

    def confidence_score(self, signal_type: str) -> float:
        signals = self.recent_signals(signal_type)
        if not signals:
            return 0.0
        return round(sum(s.confidence for s in signals) / len(signals), 3)

    def snapshot(self) -> dict:
        summary = {}
        types = set(s.signal_type for s in self.signals)
        for t in types:
            summary[t] = {
                "magnitude": self.aggregate_magnitude(t),
                "direction": self.dominant_direction(t),
                "confidence": self.confidence_score(t)
            }
        return summary