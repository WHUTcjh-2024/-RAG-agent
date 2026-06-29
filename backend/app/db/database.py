from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "sqlite" / "app.db"


def get_db_path() -> Path:
    configured = os.getenv("SQLITE_PATH", "").strip()
    return Path(configured).resolve() if configured else DEFAULT_DB_PATH.resolve()


def connect() -> sqlite3.Connection:
    path = get_db_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"SQLite catalog not found: {path}. Run backend\\scripts\\build_sqlite.py."
        )
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def product_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    product = dict(row)
    relative = str(product.get("image_path", "")).replace("\\", "/")
    product["image_url"] = (
        "/media/" + relative.removeprefix("images/") if relative else ""
    )
    return product
