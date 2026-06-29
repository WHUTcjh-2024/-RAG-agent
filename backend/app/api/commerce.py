from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.chat import get_memory, get_orchestrator
from app.db.database import connect, product_to_dict


router = APIRouter(tags=["commerce"])


class CompareRequest(BaseModel):
    product_ids: list[str] = Field(min_length=2, max_length=3)


class CartRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    product_id: str = Field(min_length=1, max_length=32)


class SessionRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)


def invoke(tool: str, arguments: dict):
    try:
        return get_orchestrator().registry.invoke(tool, arguments)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except (FileNotFoundError, RuntimeError) as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/compare")
def compare(request: CompareRequest) -> dict:
    return invoke("compare_products", {"product_ids": request.product_ids})


@router.post("/cart/add")
def add_to_cart(request: CartRequest) -> dict:
    return invoke(
        "add_to_cart",
        {"session_id": request.session_id, "product_id": request.product_id},
    )


@router.post("/cart/remove")
def remove_from_cart(request: CartRequest) -> dict:
    return invoke(
        "remove_from_cart",
        {"session_id": request.session_id, "product_id": request.product_id},
    )


@router.post("/cart")
def view_cart(request: SessionRequest) -> dict:
    return invoke("view_cart", {"session_id": request.session_id})


@router.post("/session")
def session_state(request: SessionRequest) -> dict:
    memory = get_memory()
    state = memory.get(request.session_id)
    cart: list[dict] = []
    if state.cart:
        placeholders = ",".join("?" for _ in state.cart)
        try:
            with connect() as connection:
                rows = connection.execute(
                    f"SELECT * FROM products WHERE article_id IN ({placeholders})", state.cart
                ).fetchall()
            by_id = {row["article_id"]: product_to_dict(row) for row in rows}
            cart = [by_id[item] for item in state.cart if item in by_id]
        except FileNotFoundError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
    return {
        "session_id": request.session_id,
        "slots": dict(state.slots),
        "cart": cart,
        "history": memory.recent_history(request.session_id, limit=50),
    }


@router.post("/checkout")
def checkout(request: SessionRequest) -> dict:
    return invoke("checkout", {"session_id": request.session_id})
