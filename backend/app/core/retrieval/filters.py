from __future__ import annotations

from typing import Any


FILTER_COLUMNS = {
    "color": ("colour_group_name", "perceived_colour_master_name"),
    "category": ("product_type_name", "product_group_name", "garment_group_name"),
    "product_group_name": ("product_group_name",),
    "product_type_name": ("product_type_name",),
    "colour_group_name": ("colour_group_name",),
    "garment_group_name": ("garment_group_name",),
    "index_group_name": ("index_group_name",),
}
SEARCHABLE_COLUMNS = (
    "prod_name", "product_type_name", "product_group_name", "graphical_appearance_name",
    "colour_group_name", "garment_group_name", "detail_desc", "text_profile",
)


def _values(requested: Any) -> list[str]:
    values = requested if isinstance(requested, list) else [requested]
    return [str(value).strip().casefold() for value in values if str(value).strip()]


def product_matches_filter(product: dict[str, Any], key: str, requested: Any) -> bool:
    if key == "max_price":
        raw_price = product.get("price")
        if raw_price in (None, ""):
            return False  # Never claim a missing real price satisfies a budget.
        try:
            return float(raw_price) <= float(requested)
        except (TypeError, ValueError):
            return False
    if key == "exclude":
        haystack = " ".join(str(product.get(column, "")) for column in SEARCHABLE_COLUMNS).casefold()
        return not any(value in haystack for value in _values(requested))
    columns = FILTER_COLUMNS.get(key, (key,))
    normalized_requests = _values(requested)
    if not normalized_requests:
        return True
    actual_values = [str(product.get(column, "")).strip().casefold() for column in columns]
    return any(value in actual for value in normalized_requests for actual in actual_values)


def product_matches_filters(product: dict[str, Any], filters: dict[str, Any]) -> bool:
    return all(product_matches_filter(product, key, requested) for key, requested in filters.items())


def structured_match_score(product: dict[str, Any], filters: dict[str, Any]) -> float:
    """Reward exact field matches; exclusions and unavailable prices do not add free score."""
    scores: list[float] = []
    for key, requested in filters.items():
        if key == "exclude":
            scores.append(1.0 if product_matches_filter(product, key, requested) else 0.0)
            continue
        if key == "max_price":
            if product.get("price") in (None, ""):
                scores.append(0.0)
            else:
                scores.append(1.0 if product_matches_filter(product, key, requested) else 0.0)
            continue
        columns = FILTER_COLUMNS.get(key, (key,))
        wanted = _values(requested)
        actual = [str(product.get(column, "")).strip().casefold() for column in columns]
        exact = any(value == item for value in wanted for item in actual)
        scores.append(1.0 if exact else 0.7 if product_matches_filter(product, key, requested) else 0.0)
    return sum(scores) / len(scores) if scores else 0.0
