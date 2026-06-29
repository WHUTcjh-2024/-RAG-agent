from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from langchain_core.tools import BaseTool, StructuredTool
from PIL import Image

from app.core.agent.memory import AgentMemoryStore


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, name: str, description: str, function: Callable[..., Any]) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = StructuredTool.from_function(
            func=function,
            name=name,
            description=description,
        )

    def invoke(self, name: str, arguments: dict[str, Any]) -> Any:
        try:
            tool = self._tools[name]
        except KeyError as error:
            raise KeyError(f"Unknown tool: {name}") from error
        return tool.invoke(arguments)

    @property
    def tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    @property
    def names(self) -> list[str]:
        return list(self._tools)


class CommerceToolset:
    def __init__(
        self,
        text_retriever,
        image_retriever,
        hybrid_retriever,
        memory: AgentMemoryStore,
    ) -> None:
        self.text_retriever = text_retriever
        self.image_retriever = image_retriever
        self.hybrid_retriever = hybrid_retriever
        self.memory = memory
        products = list(text_retriever.products) + list(image_retriever.products)
        self.catalog = {
            str(product["article_id"]): dict(product)
            for product in products
            if product.get("article_id")
        }

    def build_registry(self) -> ToolRegistry:
        registry = ToolRegistry()
        registry.register(
            "search_products_by_text",
            "Search real catalog products using text and structured filters.",
            self.search_products_by_text,
        )
        registry.register(
            "search_products_by_image",
            "Search visually similar real products from an uploaded local image.",
            self.search_products_by_image,
        )
        registry.register(
            "hybrid_search",
            "Fuse text, uploaded image, structured filters, and popularity.",
            self.hybrid_search,
        )
        registry.register(
            "get_product_detail",
            "Return one real catalog product by article_id.",
            self.get_product_detail,
        )
        registry.register(
            "compare_products",
            "Compare two or three real products using catalog fields only.",
            self.compare_products,
        )
        registry.register(
            "add_to_cart",
            "Add one real catalog product to the session cart.",
            self.add_to_cart,
        )
        registry.register(
            "remove_from_cart",
            "Remove one product from the session cart.",
            self.remove_from_cart,
        )
        registry.register(
            "view_cart",
            "Return current session cart products.",
            self.view_cart,
        )
        registry.register(
            "checkout",
            "Create a simulated local order and clear the cart; no payment occurs.",
            self.checkout,
        )
        registry.register(
            "update_user_preference",
            "Update structured preference slots for the current session.",
            self.update_user_preference,
        )
        return registry

    def search_products_by_text(
        self, query: str, filters: dict[str, str], top_k: int = 5
    ) -> dict[str, Any]:
        results, total = self.text_retriever.search(query, top_k, filters)
        return {"results": results, "total_candidates": total}

    def search_products_by_image(
        self, image_path: str, filters: dict[str, str], top_k: int = 5
    ) -> dict[str, Any]:
        with Image.open(image_path) as source:
            source.load()
            results, total = self.image_retriever.search(
                source.convert("RGB"), top_k, filters
            )
        return {"results": results, "total_candidates": total}

    def hybrid_search(
        self,
        query: str,
        image_path: str,
        filters: dict[str, str],
        top_k: int = 5,
    ) -> dict[str, Any]:
        with Image.open(image_path) as source:
            source.load()
            results, total = self.hybrid_retriever.search(
                query, source.convert("RGB"), top_k, filters
            )
        return {"results": results, "total_candidates": total}

    def get_product_detail(self, product_id: str) -> dict[str, Any]:
        product = self.catalog.get(product_id)
        if product is None:
            raise ValueError(f"Unknown product_id: {product_id}")
        return dict(product)

    def compare_products(self, product_ids: list[str]) -> dict[str, Any]:
        unique_ids = list(dict.fromkeys(product_ids))
        if not 2 <= len(unique_ids) <= 3:
            raise ValueError("compare_products requires two or three product IDs.")
        fields = (
            "article_id",
            "prod_name",
            "product_type_name",
            "product_group_name",
            "colour_group_name",
            "garment_group_name",
            "detail_desc",
            "image_path",
        )
        products = []
        for product_id in unique_ids:
            product = self.get_product_detail(product_id)
            products.append({field: product.get(field, "") for field in fields})
        return {"products": products}

    def _cart_products(self, session_id: str) -> list[dict[str, Any]]:
        return [
            dict(self.catalog[product_id])
            for product_id in self.memory.get(session_id).cart
            if product_id in self.catalog
        ]

    def add_to_cart(self, session_id: str, product_id: str) -> dict[str, Any]:
        self.get_product_detail(product_id)
        self.memory.add_to_cart(session_id, product_id)
        return {"cart": self._cart_products(session_id)}

    def remove_from_cart(self, session_id: str, product_id: str) -> dict[str, Any]:
        self.memory.remove_from_cart(session_id, product_id)
        return {"cart": self._cart_products(session_id)}

    def view_cart(self, session_id: str) -> dict[str, Any]:
        return {"cart": self._cart_products(session_id)}

    def checkout(self, session_id: str) -> dict[str, Any]:
        products = self._cart_products(session_id)
        if not products:
            return {"success": False, "message": "购物车为空", "order": None}
        self.memory.clear_cart(session_id)
        return {
            "success": True,
            "message": "模拟下单成功，不涉及真实支付",
            "order": {
                "order_id": f"LOCAL-{uuid4().hex[:12].upper()}",
                "status": "simulated",
                "items": products,
            },
        }

    def update_user_preference(
        self, session_id: str, slots: dict[str, Any]
    ) -> dict[str, Any]:
        return {"slots": self.memory.update_slots(session_id, slots)}
