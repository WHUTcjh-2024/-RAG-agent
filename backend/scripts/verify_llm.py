from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app  # noqa: F401 - loads local ignored environment configuration
from langchain_core.tools import StructuredTool

from app.core.agent.planner import AgentPlanner
from app.core.llm import GroundedRecommendationGenerator


def search_products_by_text(query: str) -> dict:
    """Search real catalog products using a text query."""
    return {"query": query}


def main() -> int:
    planner = AgentPlanner([StructuredTool.from_function(search_products_by_text)])
    intent = planner.choose("推荐白色通勤衬衫", False, lambda: "fallback")
    fallback_intro = "根据你的需求，我从真实商品库中筛出了这些候选。"
    intro, reasons = GroundedRecommendationGenerator().generate(
        user_query="推荐白色通勤衬衫",
        products=[{
            "article_id": "0100000001", "prod_name": "White Shirt",
            "product_type_name": "Shirt", "colour_group_name": "White",
            "detail_desc": "Cotton office shirt",
        }],
        slots={"color": "White", "scenario": "通勤"},
        history=[],
    )
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "planner_intent": intent,
        "tool_call_ok": intent == "text_recommendation",
        "structured_generation_ok": intro != fallback_intro,
        "grounded_ids": sorted(reasons),
        "grounding_ok": set(reasons) == {"0100000001"},
    }
    path = BACKEND_DIR / "evaluation" / "llm_report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(report[key] for key in ("tool_call_ok", "structured_generation_ok", "grounding_ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
