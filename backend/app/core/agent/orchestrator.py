from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.agent.memory import AgentMemoryStore
from app.core.agent.planner import AgentPlanner
from app.core.agent.slot_extractor import SlotExtractor
from app.core.agent.tool_registry import CommerceToolset, ToolRegistry
from app.core.llm import GroundedRecommendationGenerator


@dataclass
class ToolTrace:
    tool: str
    input: dict[str, Any]
    summary: str


@dataclass
class AgentResponse:
    session_id: str
    intent: str
    answer: str
    products: list[dict[str, Any]] = field(default_factory=list)
    comparison: list[dict[str, Any]] = field(default_factory=list)
    cart: list[dict[str, Any]] = field(default_factory=list)
    order: dict[str, Any] | None = None
    slots: dict[str, Any] = field(default_factory=dict)
    tool_trace: list[ToolTrace] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "intent": self.intent,
            "answer": self.answer,
            "products": self.products,
            "comparison": self.comparison,
            "cart": self.cart,
            "order": self.order,
            "slots": self.slots,
            "tool_trace": [trace.__dict__ for trace in self.tool_trace],
        }


class ShoppingAgentOrchestrator:
    def __init__(
        self,
        text_retriever,
        image_retriever,
        hybrid_retriever,
        memory: AgentMemoryStore | None = None,
        reason_generator: GroundedRecommendationGenerator | None = None,
    ) -> None:
        self.memory = memory or AgentMemoryStore()
        self.slot_extractor = SlotExtractor()
        self.reason_generator = reason_generator or GroundedRecommendationGenerator()
        self.toolset = CommerceToolset(
            text_retriever=text_retriever,
            image_retriever=image_retriever,
            hybrid_retriever=hybrid_retriever,
            memory=self.memory,
        )
        self.registry: ToolRegistry = self.toolset.build_registry()
        self.planner = AgentPlanner(self.registry.tools)

    @staticmethod
    def classify_intent(message: str, has_image: bool) -> str:
        text = message.strip()
        if any(term in text for term in ("下单", "结算", "提交订单")):
            return "checkout"
        if any(term in text for term in ("移出购物车", "删除购物车")):
            return "remove_from_cart"
        if any(term in text for term in ("加入购物车", "加到购物车", "加购")):
            return "add_to_cart"
        if any(term in text for term in ("查看购物车", "购物车里", "我的购物车")):
            return "view_cart"
        if any(term in text for term in ("对比", "比较", "哪个好", "哪件更")):
            return "compare"
        if has_image and text:
            return "hybrid_search"
        if has_image:
            return "image_search"
        return "text_recommendation"

    def _resolve_product_ids(self, session_id: str, message: str) -> list[str]:
        state = self.memory.get(session_id)
        product_ids = re.findall(r"(?<!\d)(\d{10})(?!\d)", message)
        for ordinal in re.findall(r"第\s*(\d+)\s*(?:件|个|款)?", message):
            index = int(ordinal) - 1
            if 0 <= index < len(state.last_results):
                product_ids.append(state.last_results[index])
        return list(dict.fromkeys(product_ids))

    @staticmethod
    def _trace(tool: str, arguments: dict[str, Any], result: Any) -> ToolTrace:
        if isinstance(result, dict) and "results" in result:
            summary = f"returned {len(result['results'])} products"
        elif isinstance(result, dict) and "cart" in result:
            summary = f"cart contains {len(result['cart'])} products"
        else:
            summary = "completed"
        safe_input = {
            key: (Path(value).name if key == "image_path" else value)
            for key, value in arguments.items()
        }
        return ToolTrace(tool=tool, input=safe_input, summary=summary)

    def _invoke(
        self, traces: list[ToolTrace], tool: str, arguments: dict[str, Any]
    ) -> Any:
        result = self.registry.invoke(tool, arguments)
        traces.append(self._trace(tool, arguments, result))
        return result

    def _recommendation_answer(
        self,
        session_id: str,
        message: str,
        products: list[dict[str, Any]],
        slots: dict[str, Any],
    ) -> str:
        intro, reasons = self.reason_generator.generate(
            user_query=message,
            products=products,
            slots=slots,
            history=self.memory.recent_history(session_id),
        )
        for product in products:
            product_id = str(product["article_id"])
            if product_id in reasons:
                product["reason"] = reasons[product_id]
        return intro

    def handle(
        self,
        message: str,
        session_id: str,
        image_path: str | None = None,
    ) -> AgentResponse:
        message = message.strip()
        if not message and not image_path:
            raise ValueError("Message or image is required.")
        self.memory.add_user_message(session_id, message or "[上传图片]")
        traces: list[ToolTrace] = []
        extracted = self.slot_extractor.extract(message)
        if extracted:
            preference_result = self._invoke(
                traces,
                "update_user_preference",
                {"session_id": session_id, "slots": extracted},
            )
            slots = preference_result["slots"]
        else:
            slots = dict(self.memory.get(session_id).slots)
        filters = self.slot_extractor.to_filters(slots)
        retrieval_query = self.slot_extractor.enrich_query(message, slots)
        intent = self.planner.choose(
            message,
            bool(image_path),
            lambda: self.classify_intent(message, bool(image_path)),
        )
        response = AgentResponse(
            session_id=session_id,
            intent=intent,
            answer="",
            slots=slots,
            tool_trace=traces,
        )

        if intent in {"text_recommendation", "image_search", "hybrid_search"}:
            if intent == "hybrid_search":
                result = self._invoke(
                    traces,
                    "hybrid_search",
                    {
                        "query": retrieval_query,
                        "image_path": str(image_path),
                        "filters": filters,
                        "top_k": 5,
                    },
                )
            elif intent == "image_search":
                result = self._invoke(
                    traces,
                    "search_products_by_image",
                    {
                        "image_path": str(image_path),
                        "filters": filters,
                        "top_k": 5,
                    },
                )
            else:
                result = self._invoke(
                    traces,
                    "search_products_by_text",
                    {"query": retrieval_query, "filters": filters, "top_k": 5},
                )
            response.products = result["results"]
            self.memory.set_last_results(
                session_id,
                [str(product["article_id"]) for product in response.products],
            )
            response.answer = self._recommendation_answer(
                session_id, message, response.products, slots
            )

        elif intent == "compare":
            product_ids = self._resolve_product_ids(session_id, message)
            if len(product_ids) < 2:
                response.answer = "请说明要对比的两到三件商品，例如“对比第1件和第3件”。"
            else:
                result = self._invoke(
                    traces,
                    "compare_products",
                    {"product_ids": product_ids[:3]},
                )
                response.comparison = result["products"]
                response.answer = "已按真实商品字段整理对比结果。"

        elif intent in {"add_to_cart", "remove_from_cart"}:
            product_ids = self._resolve_product_ids(session_id, message)
            if not product_ids:
                response.answer = "请说明要操作哪件商品，例如“把第1件加入购物车”。"
            else:
                tool = intent
                result = self._invoke(
                    traces,
                    tool,
                    {"session_id": session_id, "product_id": product_ids[0]},
                )
                response.cart = result["cart"]
                response.answer = (
                    "已加入购物车。" if intent == "add_to_cart" else "已从购物车移除。"
                )

        elif intent == "view_cart":
            result = self._invoke(
                traces, "view_cart", {"session_id": session_id}
            )
            response.cart = result["cart"]
            response.answer = (
                f"购物车中共有 {len(response.cart)} 件商品。"
                if response.cart
                else "购物车目前为空。"
            )

        elif intent == "checkout":
            result = self._invoke(traces, "checkout", {"session_id": session_id})
            response.order = result["order"]
            response.answer = result["message"]

        self.memory.add_ai_message(session_id, response.answer)
        return response
