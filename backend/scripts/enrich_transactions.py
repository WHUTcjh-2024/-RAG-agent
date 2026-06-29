"""Enrich the selected catalog with real transaction price and popularity signals."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
from collections import defaultdict
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


BACKEND_DIR = Path(__file__).resolve().parents[1]
SAMPLE_DIR = BACKEND_DIR / "data" / "sample"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip_path", type=Path, required=True)
    parser.add_argument("--sample_csv", type=Path, default=SAMPLE_DIR / "articles_sample.csv")
    return parser.parse_args()


def update_csv(path: Path, stats: dict[str, tuple[int, float]]) -> None:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    maximum = max((count for count, _ in stats.values()), default=0)
    denominator = math.log1p(maximum) or 1.0
    for row in rows:
        count, price_sum = stats.get(row["article_id"], (0, 0.0))
        row["popularity_score"] = f"{math.log1p(count) / denominator:.8f}"
        row["price"] = f"{price_sum / count:.8f}" if count else ""
    for field in ("price", "popularity_score"):
        if field not in fields:
            fields.append(field)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def refresh_index_metadata(index_dir: Path, profiles: dict[str, dict[str, str]]) -> None:
    path = index_dir / "products.jsonl"
    if not path.is_file():
        return
    products = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    for product in products:
        source = profiles.get(str(product.get("article_id")))
        if source:
            product["price"] = source.get("price", "")
            product["popularity_score"] = source.get("popularity_score", "0")
    temporary = path.with_suffix(".jsonl.tmp")
    temporary.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in products), encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    args = parse_args()
    with args.sample_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        selected = {row["article_id"] for row in csv.DictReader(handle)}
    counts: dict[str, int] = defaultdict(int)
    totals: dict[str, float] = defaultdict(float)
    with ZipFile(args.zip_path) as archive:
        members = [name for name in archive.namelist() if PurePosixPath(name).name == "transactions_train.csv"]
        if len(members) != 1:
            raise RuntimeError("transactions_train.csv not found uniquely in ZIP")
        with archive.open(members[0]) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text:
            for index, row in enumerate(csv.DictReader(text), start=1):
                article_id = (row.get("article_id") or "").zfill(10)
                if article_id in selected:
                    try:
                        price = float(row.get("price") or 0)
                    except ValueError:
                        continue
                    counts[article_id] += 1
                    totals[article_id] += price
                if index % 5_000_000 == 0:
                    print(f"scanned={index:,} matched={sum(counts.values()):,}", flush=True)
    stats = {item: (counts[item], totals[item]) for item in selected}
    for name in ("articles_sample.csv", "products_clean.csv", "product_profiles.csv"):
        update_csv(SAMPLE_DIR / name, stats)
    with (SAMPLE_DIR / "product_profiles.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        profiles = {row["article_id"]: row for row in csv.DictReader(handle)}
    store = BACKEND_DIR / "data" / "vector_store"
    refresh_index_metadata(store / "text", profiles)
    refresh_index_metadata(store / "image", profiles)
    print(f"enriched_products={sum(counts[item] > 0 for item in selected):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
