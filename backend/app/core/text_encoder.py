from __future__ import annotations

import hashlib
import re
from typing import Protocol, Sequence

import numpy as np


DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class TextEncoder(Protocol):
    dimension: int

    def encode(self, texts: Sequence[str], batch_size: int = 64) -> np.ndarray:
        ...


class SentenceTransformerEncoder:
    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "sentence-transformers is not installed. Run: "
                "python -m pip install -r backend\\requirements.txt"
            ) from error
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        if hasattr(self.model, "get_embedding_dimension"):
            dimension = self.model.get_embedding_dimension()
        else:
            dimension = self.model.get_sentence_embedding_dimension()
        if dimension is None:
            raise RuntimeError(f"Cannot determine embedding dimension for {model_name}.")
        self.dimension = int(dimension)

    def encode(self, texts: Sequence[str], batch_size: int = 64) -> np.ndarray:
        vectors = self.model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=len(texts) > batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return np.asarray(vectors, dtype=np.float32)


class HashingTextEncoder:
    """Dependency-free lexical encoder for deterministic smoke tests only."""

    def __init__(self, dimension: int = 384) -> None:
        if dimension <= 0:
            raise ValueError("Hashing encoder dimension must be positive.")
        self.dimension = dimension

    @staticmethod
    def _features(text: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", text.casefold()).strip()
        tokens = re.findall(r"[\w]+", normalized, flags=re.UNICODE)
        compact = normalized.replace(" ", "")
        char_ngrams = [
            compact[index : index + size]
            for size in (2, 3)
            for index in range(max(0, len(compact) - size + 1))
        ]
        return tokens + char_ngrams

    def encode(self, texts: Sequence[str], batch_size: int = 64) -> np.ndarray:
        del batch_size
        matrix = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row_index, text in enumerate(texts):
            for feature in self._features(text):
                digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
                bucket = int.from_bytes(digest, "little") % self.dimension
                matrix[row_index, bucket] += 1.0
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        np.divide(matrix, norms, out=matrix, where=norms > 0)
        return matrix


def create_text_encoder(
    backend: str,
    model_name: str = DEFAULT_MODEL,
    dimension: int | None = None,
) -> TextEncoder:
    normalized = backend.strip().casefold().replace("_", "-")
    if normalized == "sentence-transformers":
        return SentenceTransformerEncoder(model_name=model_name)
    if normalized == "hashing":
        return HashingTextEncoder(dimension=dimension or 384)
    raise ValueError(f"Unsupported text embedding backend: {backend}")
