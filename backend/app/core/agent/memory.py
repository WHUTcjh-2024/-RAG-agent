from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from langchain_core.chat_history import InMemoryChatMessageHistory


@dataclass
class SessionState:
    history: InMemoryChatMessageHistory = field(default_factory=InMemoryChatMessageHistory)
    slots: dict[str, Any] = field(default_factory=dict)
    cart: list[str] = field(default_factory=list)
    last_results: list[str] = field(default_factory=list)


class AgentMemoryStore:
    """Thread-safe in-process memory for a local single-user demo."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._lock = RLock()

    def get(self, session_id: str) -> SessionState:
        with self._lock:
            return self._sessions.setdefault(session_id, SessionState())

    def update_slots(self, session_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            state = self.get(session_id)
            for key, value in updates.items():
                if value in (None, "", []):
                    continue
                if key == "avoid":
                    existing = list(state.slots.get("avoid", []))
                    for item in value if isinstance(value, list) else [value]:
                        if item not in existing:
                            existing.append(item)
                    state.slots[key] = existing
                else:
                    state.slots[key] = value
            return dict(state.slots)

    def set_last_results(self, session_id: str, product_ids: list[str]) -> None:
        with self._lock:
            self.get(session_id).last_results = list(product_ids)

    def add_to_cart(self, session_id: str, product_id: str) -> list[str]:
        with self._lock:
            cart = self.get(session_id).cart
            if product_id not in cart:
                cart.append(product_id)
            return list(cart)

    def remove_from_cart(self, session_id: str, product_id: str) -> list[str]:
        with self._lock:
            cart = self.get(session_id).cart
            if product_id in cart:
                cart.remove(product_id)
            return list(cart)

    def clear_cart(self, session_id: str) -> list[str]:
        with self._lock:
            state = self.get(session_id)
            previous = list(state.cart)
            state.cart.clear()
            return previous

    def add_user_message(self, session_id: str, content: str) -> None:
        self.get(session_id).history.add_user_message(content)

    def add_ai_message(self, session_id: str, content: str) -> None:
        self.get(session_id).history.add_ai_message(content)

    def recent_history(self, session_id: str, limit: int = 8) -> list[dict[str, str]]:
        messages = self.get(session_id).history.messages[-limit:]
        return [
            {
                "role": "user" if message.type == "human" else "assistant",
                "content": str(message.content),
            }
            for message in messages
        ]
