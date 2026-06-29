from __future__ import annotations

from typing import Any


FILTER_COLUMNS = {
    "color": ("colour_group_name", "perceived_colour_master_name"),
    "category": (
        "product_type_name",
        "product_group_name",
        "garment_group_name",
    ),
    "product_group_name": ("product_group_name",),
    "product_type_name": ("product_type_name",),
    "colour_group_name": ("colour_group_name",),
    "garment_group_name": ("garment_group_name",),
}


def product_matches_filter(
    product: dict[str, Any], key: str, requested: str | list[str]
) -> bool:
    columns = FILTER_COLUMNS.get(key, (key,))
    values = requested if isinstance(requested, list) else [requested]
    normalized_requests = [
        str(value).strip().casefold() for value in values if str(value).strip()
    ]
    if not normalized_requests:
        return True
    actual_values = [
        str(product.get(column, "")).strip().casefold() for column in columns
    ]
    return any(
        requested_value in actual_value
        for requested_value in normalized_requests
        for actual_value in actual_values
    )


def product_matches_filters(
    product: dict[str, Any], filters: dict[str, str | list[str]]
) -> bool:
    return all(
        product_matches_filter(product, key, requested)
        for key, requested in filters.items()
    )
