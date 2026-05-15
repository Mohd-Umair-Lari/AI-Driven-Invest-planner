
import re
from typing import Dict, List, Any
from orchestrator.intent_classifier import Intent

def _extract_suggestions(text: str) -> List[str]:

    patterns = [
        r"^\s*[-•]\s+(.+)$",
        r"^\s*\d+\.\s+(.+)$",
    ]
    suggestions = []
    for line in text.split("\n"):
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                tip = match.group(1).strip()
                if 10 < len(tip) < 200:
                    suggestions.append(tip)
    return suggestions[:4]

def format_response(
    raw_response: str,
    intent: Intent,
    context_used: str,
) -> Dict[str, Any]:

    suggestions = _extract_suggestions(raw_response)

    cleaned = re.sub(r"\n{3,}", "\n\n", raw_response).strip()

    return {
        "response":     cleaned,
        "suggestions":  suggestions,
        "intent":       intent.value,
        "context_used": context_used,
    }
