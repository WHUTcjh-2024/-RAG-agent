"""Lightweight LangChain-based shopping agent."""

__all__ = ["ShoppingAgentOrchestrator"]


def __getattr__(name: str):
    if name == "ShoppingAgentOrchestrator":
        from app.core.agent.orchestrator import ShoppingAgentOrchestrator

        return ShoppingAgentOrchestrator
    raise AttributeError(name)
