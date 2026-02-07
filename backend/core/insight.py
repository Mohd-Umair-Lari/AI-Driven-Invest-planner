from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Insight:
    category: str
    severity: str
    impact_area: str
    confidence_score: float
    message: str
    created_at: datetime
    explanation_ref: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "severity": self.severity,
            "impact_area": self.impact_area,
            "confidence_score": round(self.confidence_score, 3),
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "explanation_ref": self.explanation_ref
        }


class InsightFactory:
    @staticmethod
    def threat(message: str, severity: str, impact_area: str, confidence: float):
        return Insight(
            category="threat",
            severity=severity,
            impact_area=impact_area,
            confidence_score=confidence,
            message=message,
            created_at=datetime.utcnow()
        )

    @staticmethod
    def opportunity(message: str, severity: str, impact_area: str, confidence: float):
        return Insight(
            category="opportunity",
            severity=severity,
            impact_area=impact_area,
            confidence_score=confidence,
            message=message,
            created_at=datetime.utcnow()
        )

    @staticmethod
    def behavior(message: str, severity: str, impact_area: str, confidence: float):
        return Insight(
            category="behavior",
            severity=severity,
            impact_area=impact_area,
            confidence_score=confidence,
            message=message,
            created_at=datetime.utcnow()
        )

    @staticmethod
    def stability(message: str, severity: str, impact_area: str, confidence: float):
        return Insight(
            category="stability",
            severity=severity,
            impact_area=impact_area,
            confidence_score=confidence,
            message=message,
            created_at=datetime.utcnow()
        )