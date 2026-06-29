from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.chat import get_orchestrator


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


@router.post("/checkout")
def checkout(request: SessionRequest) -> dict:
    return invoke("checkout", {"session_id": request.session_id})
