"""
agents/base_agent.py
---------------------
Abstract base class for all FinPass AI agents.
Every agent: receives classified intent + user context → returns AgentResult.
Tool-calling compatible: agents pick tools from their registry.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Tool:
    """A callable tool available to an agent."""
    name: str
    description: str
    fn: Callable
    required_keys: List[str] = field(default_factory=list)

    def run(self, **kwargs) -> Any:
        return self.fn(**kwargs)


@dataclass
class AgentResult:
    """Standardized output from any agent."""
    success: bool
    response: str
    data: Dict[str, Any] = field(default_factory=dict)
    tool_used: Optional[str] = None
    agent_name: str = ""


class BaseAgent(ABC):
    """
    Base class. Subclass and implement `run()`.
    """
    name: str = "BaseAgent"
    description: str = ""
    tools: List[Tool] = []

    def get_tool(self, name: str) -> Optional[Tool]:
        return next((t for t in self.tools if t.name == name), None)

    @abstractmethod
    def run(
        self,
        query: str,
        user_context: Dict[str, Any],
        intent_entities: Dict[str, Any],
    ) -> AgentResult:
        """Each agent implements its own reasoning logic."""
        ...

    def _safe_run_tool(self, tool_name: str, **kwargs) -> Any:
        tool = self.get_tool(tool_name)
        if not tool:
            return None
        try:
            return tool.run(**kwargs)
        except Exception as e:
            return {"error": str(e)}
