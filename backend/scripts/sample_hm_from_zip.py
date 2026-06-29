"""Create a small H&M product/image sample directly from the official ZIP.

The ZIP is treated as an immutable source. It is never extracted in full.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import random
import shutil
import sys
import tempfile
from collections import defaultdict, deque
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile


BALANCE_COLUMNS = (
    "product_group_name",
    "product_type_name",
    "colour_group_name",
)


def log(message: str) -> None:
    print(message, flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read the official H&M ZIP in place, sample products that have images, "
            "and extract only the selected images."
        )
    )
    parser.add_argument("--zip_path", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    parser.add_argument("--sample_size", type=int, default=5000)
    parser.add_argument(
        "--with_transactions",
        action="store_true",
        help="Also stream transactions_train.csv and retain rows for sampled products.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used inside balanced groups (default: 42).",
    )
    return parser.parse_args()


def normalize_member_name(name: str) -> str:
    return name.replace("\\", "/").lstrip("./")


def find_csv_member(names: list[str], filename: str) -> str:
    matches = [
        name
        for name in names
        if PurePosixPath(normalize_member_name(name)).name.casefold()
        == filename.casefold()
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one {filename!r} in ZIP, found {len(matches)}."
        )
    return matches[0]


def canonical_image_path(member_name: str) -> str | None:
    normalized = normalize_member_name(member_name)
    parts = PurePosixPath(normalized).parts
    try:
        image_index = next(
            index for index, part in enumerate(parts) if part.casefold() == "images"
        )
    except StopIteration:
        return None
    relative = PurePosixPath(*parts[image_index:]).as_posix()
    if not relative.casefold().endswith((".jpg", ".jpeg")):
        return None
    return relative


def normalize_article_id(value: str | None) -> str:
    article_id = (value or "").strip()
    return article_id.zfill(10) if article_id.isdigit() else article_id


def read_articles(
    archive: ZipFile,
    member_name: str,
    image_members: dict[str, str],
) -> tuple[list[dict[str, str]], list[str]]:
    with archive.open(member_name, "r") as raw:
        with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text:
            reader = csv.DictReader(text)
            if not reader.fieldnames:
                raise RuntimeError("articles.csv has no header.")
            required = {"article_id", *BALANCE_COLUMNS}
            missing = sorted(required.difference(reader.fieldnames))
            if missing:
                raise RuntimeError(
                    "articles.csv is missing required columns: " + ", ".join(missing)
                )

            rows: list[dict[str, str]] = []
            seen_ids: set[str] = set()
            for row in reader:
                article_id = normalize_article_id(row.get("article_id"))
                if not article_id or article_id in seen_ids:
                    continue
                expected_image = f"images/{article_id[:3]}/{article_id}.jpg"
                if expected_image not in image_members:
                    continue
                row["article_id"] = article_id
                row["image_path"] = expected_image
                rows.append(row)
                seen_ids.add(article_id)

            fieldnames = list(reader.fieldnames)
            if "image_path" not in fieldnames:
                fieldnames.append("image_path")
            return rows, fieldnames


def balanced_sample(
    rows: list[dict[str, str]], sample_size: int, seed: int
) -> list[dict[str, str]]:
    if sample_size <= 0:
        raise ValueError("--sample_size must be greater than zero.")
    if len(rows) < sample_size:
        raise RuntimeError(
            f"Only {len(rows)} products have matching images; cannot sample {sample_size}."
        )

    rng = random.Random(seed)
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = tuple((row.get(column) or "__MISSING__").strip() for column in BALANCE_COLUMNS)
        grouped[key].append(row)

    keys = list(grouped)
    rng.shuffle(keys)
    buckets: dict[tuple[str, str, str], deque[dict[str, str]]] = {}
    for key in keys:
        rng.shuffle(grouped[key])
        buckets[key] = deque(grouped[key])

    active = deque(keys)
    selected: list[dict[str, str]] = []
    while active and len(selected) < sample_size:
        key = active.popleft()
        selected.append(buckets[key].popleft())
        if buckets[key]:
            active.append(key)

    rng.shuffle(selected)
    return selected


def replace_images_atomically(
    archive: ZipFile,
    selected: list[dict[str, str]],
    image_members: dict[str, str],
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".hm_images_", dir=out_dir))
    staging_images = staging / "images"
    try:
        for index, row in enumerate(selected, start=1):
            relative = row["image_path"]
            destination = staging / Path(*PurePosixPath(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(image_members[relative], "r") as source:
                with destination.open("wb") as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024)
            if index % 500 == 0 or index == len(selected):
                log(f"      extracted {index}/{len(selected)} images")

        final_images = out_dir / "images"
        if final_images.exists():
            shutil.rmtree(final_images)
        staging_images.replace(final_images)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def write_csv_atomic(
    path: Path, rows: list[dict[str, str]], fieldnames: list[str]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def filter_transactions(
    archive: ZipFile,
    member_name: str,
    article_ids: set[str],
    output_path: Path,
) -> int:
    temporary = output_path.with_name(output_path.name + ".tmp")
    matched = 0
    with archive.open(member_name, "r") as raw:
        with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text:
            reader = csv.DictReader(text)
            if not reader.fieldnames or "article_id" not in reader.fieldnames:
                raise RuntimeError("transactions_train.csv has no article_id column.")
            with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=reader.fieldnames)
                writer.writeheader()
                for row_number, row in enumerate(reader, start=1):
                    if normalize_article_id(row.get("article_id")) in article_ids:
                        writer.writerow(row)
                        matched += 1
                    if row_number % 5_000_000 == 0:
                        log(
                            f"      scanned {row_number:,} transactions; "
                            f"matched {matched:,}"
                        )
    os.replace(temporary, output_path)
    return matched


def verify_output(out_dir: Path, expected_count: int) -> None:
    article_path = out_dir / "articles_sample.csv"
    if not article_path.is_file():
        raise RuntimeError(f"Missing output file: {article_path}")
    with article_path.open("r", encoding="utf-8-sig", newline="") as handle:
        article_count = sum(1 for _ in csv.DictReader(handle))
    image_files = [
        path
        for path in (out_dir / "images").rglob("*")
        if path.is_file() and path.suffix.casefold() in {".jpg", ".jpeg"}
    ]
    empty_images = sum(1 for path in image_files if path.stat().st_size == 0)
    log(f"      articles_sample.csv rows: {article_count}")
    log(f"      extracted image files:     {len(image_files)}")
    if article_count != expected_count or len(image_files) != expected_count:
        raise RuntimeError(
            "Verification failed: article and image counts must both equal "
            f"{expected_count}."
        )
    if empty_images:
        raise RuntimeError(f"Verification failed: {empty_images} images are empty.")


def main() -> int:
    args = parse_args()
    zip_path = args.zip_path.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()

    log("[1/7] Validating arguments and source ZIP")
    if not zip_path.is_file():
        raise FileNotFoundError(f"H&M ZIP not found: {zip_path}")
    if zip_path.suffix.casefold() != ".zip":
        raise ValueError(f"--zip_path must point to a ZIP file: {zip_path}")
    out_dir.mkdir(parents=True, exist_ok=True)
    log(f"      source: {zip_path}")
    log(f"      output: {out_dir}")
    log("      full ZIP extraction: disabled")

    try:
        with ZipFile(zip_path, "r") as archive:
            log("[2/7] Indexing ZIP members without extracting them")
            names = archive.namelist()
            articles_member = find_csv_member(names, "articles.csv")
            image_members: dict[str, str] = {}
            for member in names:
                canonical = canonical_image_path(member)
                if canonical:
                    image_members.setdefault(canonical, member)
            log(f"      image members found: {len(image_members):,}")

            log("[3/7] Reading articles.csv directly from ZIP")
            eligible, fieldnames = read_articles(
                archive, articles_member, image_members
            )
            log(f"      products with matching images: {len(eligible):,}")

            log("[4/7] Selecting a diversity-balanced product sample")
            selected = balanced_sample(eligible, args.sample_size, args.seed)
            unique_combinations = {
                tuple((row.get(column) or "").strip() for column in BALANCE_COLUMNS)
                for row in selected
            }
            log(f"      selected products: {len(selected):,}")
            log(f"      unique balance combinations: {len(unique_combinations):,}")

            log("[5/7] Extracting only selected product images")
            replace_images_atomically(
                archive, selected, image_members, out_dir
            )
            write_csv_atomic(out_dir / "articles_sample.csv", selected, fieldnames)

            log("[6/7] Handling optional transactions")
            if args.with_transactions:
                transactions_member = find_csv_member(
                    names, "transactions_train.csv"
                )
                matched = filter_transactions(
                    archive,
                    transactions_member,
                    {row["article_id"] for row in selected},
                    out_dir / "transactions_sample.csv",
                )
                log(f"      saved transaction rows: {matched:,}")
            else:
                log("      skipped (enable with --with_transactions)")

    except BadZipFile as error:
        raise RuntimeError(f"Invalid or incomplete ZIP: {zip_path}") from error

    log("[7/7] Verifying sample outputs")
    verify_output(out_dir, args.sample_size)
    log("SUCCESS: H&M sample metadata and images are ready.")
    log(
        "NEXT: python -c \"import csv,pathlib; "
        "p=pathlib.Path(r'" + str(out_dir) + "'); "
        "print('rows=',sum(1 for _ in csv.DictReader(open(p/'articles_sample.csv',encoding='utf-8-sig')))); "
        "print('images=',sum(1 for x in (p/'images').rglob('*.jpg')))\""
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr, flush=True)
        raise SystemExit(1)
