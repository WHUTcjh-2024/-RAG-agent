from __future__ import annotations

import re
from typing import Any


COLOR_TERMS = {
    "白色": "White",
    "白": "White",
    "黑色": "Black",
    "黑": "Black",
    "蓝色": "Blue",
    "蓝": "Blue",
    "红色": "Red",
    "红": "Red",
    "绿色": "Green",
    "绿": "Green",
    "灰色": "Grey",
    "灰": "Grey",
    "米色": "Beige",
    "粉色": "Pink",
    "粉": "Pink",
    "黄色": "Yellow",
    "黄": "Yellow",
    "棕色": "Brown",
    "紫色": "Purple",
}

CATEGORY_TERMS = {
    "连衣裙": "Dress",
    "衬衫": "Shirt",
    "t恤": "T-shirt",
    "T恤": "T-shirt",
    "外套": "Jacket",
    "夹克": "Jacket",
    "卫衣": "Sweater",
    "毛衣": "Sweater",
    "牛仔裤": "Trousers",
    "裤子": "Trousers",
    "长裤": "Trousers",
    "短裤": "Shorts",
    "半身裙": "Skirt",
    "裙子": "Skirt",
    "上衣": "Top",
}

STYLE_TERMS = ("简约", "休闲", "正式", "运动", "宽松", "修身", "复古", "通勤")
SCENARIO_TERMS = ("上课", "通勤", "约会", "运动", "旅行", "面试", "日常", "聚会")


class SlotExtractor:
    def extract(self, text: str) -> dict[str, Any]:
        normalized = text.strip()
        slots: dict[str, Any] = {}
        for term, value in sorted(COLOR_TERMS.items(), key=lambda item: -len(item[0])):
            if term in normalized:
                slots["color"] = value
                break
        for term, value in sorted(CATEGORY_TERMS.items(), key=lambda item: -len(item[0])):
            if term in normalized:
                slots["category"] = value
                break
        styles = [term for term in STYLE_TERMS if term in normalized]
        if styles:
            slots["style"] = styles
        scenarios = [term for term in SCENARIO_TERMS if term in normalized]
        if scenarios:
            slots["scenario"] = scenarios[-1]

        budget_match = re.search(
            r"(?:预算|不超过|最多|低于|以内)\s*(\d+(?:\.\d+)?)\s*(?:元|块|数据价)?",
            normalized,
        ) or re.search(r"(\d+(?:\.\d+)?)\s*(?:元|块|数据价)", normalized)
        if budget_match:
            slots["budget"] = float(budget_match.group(1))

        avoid_clauses = [
            match.strip("，。,. ")
            for match in re.findall(
                r"(?:不要|不想要|避免)([^，。,.；;]+)", normalized
            )
            if match.strip("，。,. ")
        ]
        avoid: list[str] = []
        for clause in avoid_clauses:
            translated = [
                value
                for term, value in {**COLOR_TERMS, **CATEGORY_TERMS}.items()
                if term in clause
            ]
            avoid.extend(translated or [clause])
        avoid = list(dict.fromkeys(avoid))
        if avoid:
            slots["avoid"] = avoid
        return slots

    @staticmethod
    def to_filters(slots: dict[str, Any]) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if slots.get("color"):
            filters["color"] = str(slots["color"])
        if slots.get("category"):
            filters["category"] = str(slots["category"])
        if slots.get("budget") is not None:
            filters["max_price"] = float(slots["budget"])
        if slots.get("avoid"):
            filters["exclude"] = list(slots["avoid"])
        return filters

    @staticmethod
    def enrich_query(text: str, slots: dict[str, Any]) -> str:
        """Add soft preferences to the semantic query without inventing catalog facts."""
        additions: list[str] = []
        for key in ("style", "scenario"):
            value = slots.get(key)
            values = value if isinstance(value, list) else [value]
            for item in values:
                if item and str(item) not in additions:
                    additions.append(str(item))
        return " ".join([text.strip(), *additions]).strip()
