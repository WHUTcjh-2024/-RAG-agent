from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data_utils import SAMPLE_DIR, read_csv, write_csv


PROFILE_FIELDS = (
    ("prod_name", "商品名"),
    ("product_type_name", "商品类型"),
    ("product_group_name", "商品大类"),
    ("colour_group_name", "颜色"),
    ("perceived_colour_master_name", "主色系"),
    ("graphical_appearance_name", "图案"),
    ("garment_group_name", "服装组"),
    ("department_name", "部门"),
    ("section_name", "分区"),
    ("detail_desc", "商品描述"),
    ("price", "数据集价格"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build H&M product text profiles.")
    parser.add_argument(
        "--input_csv", type=Path, default=SAMPLE_DIR / "products_clean.csv"
    )
    parser.add_argument(
        "--output_csv", type=Path, default=SAMPLE_DIR / "product_profiles.csv"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(f"[1/3] Reading cleaned products: {args.input_csv.resolve()}", flush=True)
    fields, rows = read_csv(args.input_csv.resolve())
    if "article_id" not in fields:
        raise RuntimeError("Input CSV must contain article_id.")

    print("[2/3] Building text_profile", flush=True)
    for row in rows:
        row["text_profile"] = "\n".join(
            f"{label}：{value.strip()}"
            for field, label in PROFILE_FIELDS
            if (value := row.get(field)) and value.strip()
        )
    empty_profiles = sum(not row["text_profile"] for row in rows)
    if empty_profiles:
        raise RuntimeError(f"Generated {empty_profiles} empty text profiles.")

    output_fields = fields + (["text_profile"] if "text_profile" not in fields else [])
    print(f"[3/3] Writing: {args.output_csv.resolve()}", flush=True)
    write_csv(args.output_csv.resolve(), rows, output_fields)
    print(f"SUCCESS: generated {len(rows):,} product profiles", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr, flush=True)
        raise SystemExit(1)
