"""
orchestrator/response_formatter.py
------------------------------------
Normalizes raw LLM output into a structured frontend-ready dict.
Extracts actionable suggestions from the response text.
"""
import re
from typing import Dict, List, Any
from orchestrator.intent_classifier import Intent


def _extract_suggestions(text: str) -> List[str]:
    """
    Pull out bullet points or numbered list items as quick-action suggestions.
    """
    patterns = [
        r"^\s*[-•]\s+(.+)$",      # bullet points
        r"^\s*\d+\.\s+(.+)$",     # numbered list
    ]
    suggestions = []
    for line in text.split("\n"):
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                tip = match.group(1).strip()
                if 10 < len(tip) < 200:
                    suggestions.append(tip)
    return suggestions[:4]   # max 4 suggestions


def format_response(
    raw_response: str,
    intent: Intent,
    context_used: str,
) -> Dict[str, Any]:
    """
    Returns a consistent response envelope the frontend can always rely on.
    """
    suggestions = _extract_suggestions(raw_response)

    # Clean response: strip excessive whitespace
    cleaned = re.sub(r"\n{3,}", "\n\n", raw_response).strip()

    return {
        "response":     cleaned,
        "suggestions":  suggestions,
        "intent":       intent.value,
        "context_used": context_used,
    }
