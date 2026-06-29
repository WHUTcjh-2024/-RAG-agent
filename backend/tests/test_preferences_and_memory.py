from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.agent.memory import AgentMemoryStore
from app.core.agent.slot_extractor import SlotExtractor
from app.core.retrieval.filters import product_matches_filters, structured_match_score


def test_preferences_drive_semantics_budget_and_exclusions() -> None:
    extractor = SlotExtractor()
    slots = extractor.extract("通勤简约，预算0.06元，不要蓝色")
    filters = extractor.to_filters(slots)
    assert filters["max_price"] == 0.06
    assert filters["exclude"] == ["Blue"]
    assert extractor.enrich_query("推荐衬衫", slots).endswith("简约 通勤")

    product = {
        "prod_name": "White office shirt",
        "product_type_name": "Shirt",
        "colour_group_name": "White",
        "price": "0.05",
    }
    assert product_matches_filters(product, {"category": "Shirt", "max_price": 0.06})
    assert not product_matches_filters(product, {"exclude": ["shirt"]})
    assert structured_match_score(product, {"category": "Shirt"}) == 1.0


def test_memory_survives_store_recreation(tmp_path: Path) -> None:
    database = tmp_path / "sessions.db"
    first = AgentMemoryStore(database)
    first.update_slots("session", {"color": "Red"})
    first.add_to_cart("session", "0000000001")
    first.add_user_message("session", "红色衬衫")

    restored = AgentMemoryStore(database).get("session")
    assert restored.slots == {"color": "Red"}
    assert restored.cart == ["0000000001"]
    assert restored.history.messages[0].content == "红色衬衫"
