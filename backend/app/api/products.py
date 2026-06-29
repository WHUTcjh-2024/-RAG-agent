from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.db.database import connect, product_to_dict


router = APIRouter(tags=["products"])


@router.get("/products")
def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    category: str | None = Query(default=None),
    color: str | None = Query(default=None),
    group: str | None = Query(default=None),
    index_group: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
) -> dict:
    clauses: list[str] = []
    parameters: list[object] = []
    if category:
        clauses.append("product_type_name LIKE ?")
        parameters.append(f"%{category.strip()}%")
    if color:
        clauses.append("colour_group_name LIKE ?")
        parameters.append(f"%{color.strip()}%")
    if group:
        clauses.append("product_group_name LIKE ?")
        parameters.append(f"%{group.strip()}%")
    if index_group:
        clauses.append("index_group_name = ?")
        parameters.append(index_group.strip())
    if search:
        clauses.append("(prod_name LIKE ? OR detail_desc LIKE ?)")
        value = f"%{search.strip()}%"
        parameters.extend((value, value))
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    offset = (page - 1) * page_size
    try:
        with connect() as connection:
            total = connection.execute(
                "SELECT COUNT(*) FROM products" + where, parameters
            ).fetchone()[0]
            rows = connection.execute(
                "SELECT * FROM products"
                + where
                + " ORDER BY article_id LIMIT ? OFFSET ?",
                [*parameters, page_size, offset],
            ).fetchall()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [product_to_dict(row) for row in rows],
    }


@router.get("/products/{article_id}")
def get_product(article_id: str) -> dict:
    try:
        with connect() as connection:
            row = connection.execute(
                "SELECT * FROM products WHERE article_id = ?", (article_id,)
            ).fetchone()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product_to_dict(row)
