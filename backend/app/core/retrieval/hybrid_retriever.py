from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from app.core.retrieval.filters import product_matches_filters, structured_match_score
from app.core.retrieval.image_retriever import ImageRetriever
from app.core.retrieval.text_retriever import TextRetriever


TEXT_WEIGHT = 0.30
IMAGE_WEIGHT = 0.45
STRUCTURED_WEIGHT = 0.15
POPULARITY_WEIGHT = 0.10


def normalize_cosine(scores: np.ndarray) -> np.ndarray:
    return np.clip((scores.astype(np.float32) + 1.0) / 2.0, 0.0, 1.0)


def normalize_popularity(values: np.ndarray) -> np.ndarray:
    values = np.maximum(values.astype(np.float32), 0.0)
    if values.size == 0:
        return values
    if float(values.max()) <= 1.0:
        return np.clip(values, 0.0, 1.0)
    transformed = np.log1p(values)
    maximum = float(transformed.max())
    return transformed / maximum if maximum > 0 else np.zeros_like(transformed)


class HybridRetriever:
    def __init__(
        self,
        text_index_dir: str | Path,
        image_index_dir: str | Path,
        image_device: str = "auto",
    ) -> None:
        self.text_retriever = TextRetriever(text_index_dir)
        self.image_retriever = ImageRetriever(image_index_dir, device=image_device)

        self.text_positions = {
            str(product.get("article_id", "")): index
            for index, product in enumerate(self.text_retriever.products)
            if product.get("article_id")
        }
        self.image_positions = {
            str(product.get("article_id", "")): index
            for index, product in enumerate(self.image_retriever.products)
            if product.get("article_id")
        }
        common_ids = self.text_positions.keys() & self.image_positions.keys()
        if not common_ids:
            raise RuntimeError("Text and image indexes have no common article_id values.")
        self.common_ids = sorted(common_ids)

    @staticmethod
    def _parse_popularity(product: dict[str, Any]) -> float:
        try:
            return float(product.get("popularity_score") or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def search(
        self,
        query: str,
        image: Image.Image,
        top_k: int = 10,
        filters: dict[str, str | list[str]] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        query = query.strip()
        if not query:
            raise ValueError("Hybrid search query cannot be empty.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")
        applied_filters = filters or {}

        candidate_ids = [
            article_id
            for article_id in self.common_ids
            if product_matches_filters(
                self.image_retriever.products[self.image_positions[article_id]],
                applied_filters,
            )
        ]
        total_candidates = len(candidate_ids)
        if total_candidates == 0:
            return [], 0

        text_query = self.text_retriever.encoder.encode([query], batch_size=1)[0]
        image_query = self.image_retriever.encoder.encode([image], batch_size=1)[0]
        text_indices = np.asarray(
            [self.text_positions[article_id] for article_id in candidate_ids],
            dtype=np.int64,
        )
        image_indices = np.asarray(
            [self.image_positions[article_id] for article_id in candidate_ids],
            dtype=np.int64,
        )
        text_raw = np.asarray(self.text_retriever.embeddings[text_indices]) @ text_query
        image_raw = np.asarray(self.image_retriever.embeddings[image_indices]) @ image_query
        text_scores = normalize_cosine(text_raw)
        image_scores = normalize_cosine(image_raw)

        # Exact structured matches score above partial matches. With no structured
        # request this component is zero instead of adding a constant to every item.
        structured_scores = np.asarray(
            [
                structured_match_score(
                    self.image_retriever.products[self.image_positions[article_id]],
                    applied_filters,
                )
                for article_id in candidate_ids
            ],
            dtype=np.float32,
        )
        popularity_scores = normalize_popularity(
            np.asarray(
                [
                    self._parse_popularity(
                        self.image_retriever.products[self.image_positions[article_id]]
                    )
                    for article_id in candidate_ids
                ],
                dtype=np.float32,
            )
        )
        final_scores = (
            TEXT_WEIGHT * text_scores
            + IMAGE_WEIGHT * image_scores
            + STRUCTURED_WEIGHT * structured_scores
            + POPULARITY_WEIGHT * popularity_scores
        )

        result_count = min(top_k, total_candidates)
        if result_count == total_candidates:
            order = np.argsort(-final_scores)
        else:
            partition = np.argpartition(-final_scores, result_count - 1)[:result_count]
            order = partition[np.argsort(-final_scores[partition])]

        results: list[dict[str, Any]] = []
        for index in order[:result_count]:
            article_id = candidate_ids[int(index)]
            product = dict(
                self.image_retriever.products[self.image_positions[article_id]]
            )
            text_score = float(text_scores[index])
            image_score = float(image_scores[index])
            product.update(
                {
                    "score": round(float(final_scores[index]), 6),
                    "text_score": round(text_score, 6),
                    "image_score": round(image_score, 6),
                    "structured_score": round(float(structured_scores[index]), 6),
                    "popularity_score": round(float(popularity_scores[index]), 6),
                    "reason": (
                        "图片相似度贡献更高"
                        if image_score >= text_score
                        else "文本语义匹配贡献更高"
                    ),
                }
            )
            results.append(product)
        return results, total_candidates
