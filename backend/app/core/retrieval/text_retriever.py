from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from app.core.retrieval.filters import product_matches_filters
from app.core.text_encoder import create_text_encoder


class TextRetriever:
    def __init__(self, index_dir: str | Path) -> None:
        self.index_dir = Path(index_dir).resolve()
        metadata_path = self.index_dir / "metadata.json"
        embeddings_path = self.index_dir / "embeddings.npy"
        products_path = self.index_dir / "products.jsonl"
        for path in (metadata_path, embeddings_path, products_path):
            if not path.is_file():
                raise FileNotFoundError(
                    f"Text index is incomplete; missing {path}. "
                    "Run backend\\scripts\\build_text_index.py first."
                )

        self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.embeddings = np.load(embeddings_path, mmap_mode="r")
        with products_path.open("r", encoding="utf-8") as handle:
            self.products = [json.loads(line) for line in handle if line.strip()]

        if self.embeddings.ndim != 2:
            raise RuntimeError("Text embeddings must be a two-dimensional matrix.")
        if len(self.products) != self.embeddings.shape[0]:
            raise RuntimeError("Product metadata and embedding counts do not match.")
        expected_dimension = int(self.metadata["dimension"])
        if self.embeddings.shape[1] != expected_dimension:
            raise RuntimeError("Embedding dimension does not match metadata.json.")

        self.encoder = create_text_encoder(
            backend=self.metadata["backend"],
            model_name=self.metadata.get("model", ""),
            dimension=expected_dimension,
        )

    def _candidate_indices(self, filters: dict[str, str | list[str]]) -> np.ndarray:
        if not filters:
            return np.arange(len(self.products), dtype=np.int64)
        indices = [
            index
            for index, product in enumerate(self.products)
            if product_matches_filters(product, filters)
        ]
        return np.asarray(indices, dtype=np.int64)

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, str | list[str]] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        query = query.strip()
        if not query:
            raise ValueError("Search query cannot be empty.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        candidate_indices = self._candidate_indices(filters or {})
        total_candidates = int(candidate_indices.size)
        if total_candidates == 0:
            return [], 0

        query_vector = self.encoder.encode([query])[0]
        candidate_vectors = np.asarray(self.embeddings[candidate_indices])
        scores = candidate_vectors @ query_vector
        result_count = min(top_k, total_candidates)
        if result_count == total_candidates:
            local_order = np.argsort(-scores)
        else:
            partition = np.argpartition(-scores, result_count - 1)[:result_count]
            local_order = partition[np.argsort(-scores[partition])]

        results: list[dict[str, Any]] = []
        for local_index in local_order[:result_count]:
            product_index = int(candidate_indices[local_index])
            product = dict(self.products[product_index])
            product["score"] = round(float(scores[local_index]), 6)
            product["reason"] = "文本语义相似度与结构化筛选匹配"
            results.append(product)
        return results, total_candidates
