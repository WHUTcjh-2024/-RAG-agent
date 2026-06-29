from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.chat import router as chat_router
from app.api.commerce import router as commerce_router
from app.api.products import router as products_router
from app.api.search import router as search_router


app = FastAPI(
    title="RAG Multimodal Shopping Agent",
    version="0.2.0-stage2",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(search_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(commerce_router, prefix="/api")

IMAGE_DIR = Path(__file__).resolve().parents[1] / "data" / "sample" / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=IMAGE_DIR), name="media")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "stage": "text-retrieval"}
