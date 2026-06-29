from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data_utils import (
    PRODUCT_FIELDS,
    SAMPLE_DIR,
    clean_text,
    normalize_article_id,
    read_csv,
    resolve_image_path,
    write_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean sampled H&M article fields.")
    parser.add_argument(
        "--input_csv", type=Path, default=SAMPLE_DIR / "articles_sample.csv"
    )
    parser.add_argument(
        "--output_csv", type=Path, default=SAMPLE_DIR / "products_clean.csv"
    )
    parser.add_argument("--image_root", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_csv = args.input_csv.resolve()
    image_root = (args.image_root or input_csv.parent).resolve()
    print(f"[1/3] Reading sampled articles: {input_csv}", flush=True)
    fields, rows = read_csv(input_csv)
    required = {"article_id", "prod_name", "product_type_name", "image_path"}
    missing_fields = sorted(required.difference(fields))
    if missing_fields:
        raise RuntimeError("Missing required fields: " + ", ".join(missing_fields))

    print("[2/3] Normalizing fields and removing invalid rows", flush=True)
    cleaned = []
    seen: set[str] = set()
    skipped_duplicate = 0
    skipped_invalid = 0
    for row in rows:
        article_id = normalize_article_id(row.get("article_id"))
        image_path = clean_text(row.get("image_path")).replace("\\", "/")
        if not article_id or not image_path or not resolve_image_path(
            image_root, image_path
        ).is_file():
            skipped_invalid += 1
            continue
        if article_id in seen:
            skipped_duplicate += 1
            continue
        output = {field: clean_text(row.get(field)) for field in PRODUCT_FIELDS}
        output["article_id"] = article_id
        output["image_path"] = image_path
        output["popularity_score"] = clean_text(row.get("popularity_score")) or "0"
        output["price"] = clean_text(row.get("price"))
        cleaned.append(output)
        seen.add(article_id)

    if not cleaned:
        raise RuntimeError("No valid products remain after cleaning.")
    print(f"[3/3] Writing: {args.output_csv.resolve()}", flush=True)
    write_csv(args.output_csv.resolve(), cleaned, list(PRODUCT_FIELDS))
    print(
        f"SUCCESS: input={len(rows):,}, output={len(cleaned):,}, "
        f"duplicates_removed={skipped_duplicate}, invalid_removed={skipped_invalid}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr, flush=True)
        raise SystemExit(1)
