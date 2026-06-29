from __future__ import annotations

from typing import Protocol, Sequence

import numpy as np
from PIL import Image


DEFAULT_CLIP_MODEL = "openai/clip-vit-base-patch32"


class ImageEncoder(Protocol):
    dimension: int

    def encode(self, images: Sequence[Image.Image], batch_size: int = 32) -> np.ndarray:
        ...


class TransformersClipImageEncoder:
    def __init__(self, model_name: str = DEFAULT_CLIP_MODEL, device: str = "auto") -> None:
        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor
        except ImportError as error:
            raise RuntimeError(
                "CLIP dependencies are missing. Run: "
                "python -m pip install -r backend\\requirements.txt"
            ) from error

        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.torch = torch
        self.device = device
        self.model_name = model_name
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model = CLIPModel.from_pretrained(model_name).to(device)
        self.model.eval()
        self.dimension = int(self.model.config.projection_dim)

    def encode(self, images: Sequence[Image.Image], batch_size: int = 32) -> np.ndarray:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")
        batches: list[np.ndarray] = []
        for start in range(0, len(images), batch_size):
            batch = [image.convert("RGB") for image in images[start : start + batch_size]]
            inputs = self.processor(images=batch, return_tensors="pt")
            pixel_values = inputs["pixel_values"].to(self.device)
            with self.torch.inference_mode():
                features = self.model.get_image_features(pixel_values=pixel_values)
                # transformers 5.x returns BaseModelOutputWithPooling here,
                # while 4.x returns a Tensor. Accept both public APIs.
                if not self.torch.is_tensor(features):
                    if getattr(features, "image_embeds", None) is not None:
                        features = features.image_embeds
                    elif getattr(features, "pooler_output", None) is not None:
                        features = features.pooler_output
                    else:
                        raise RuntimeError(
                            "Unsupported CLIP image feature output: "
                            f"{type(features).__name__}"
                        )
                features = features / features.norm(dim=-1, keepdim=True).clamp(min=1e-12)
            batches.append(features.detach().cpu().numpy().astype(np.float32))
        if not batches:
            return np.empty((0, self.dimension), dtype=np.float32)
        return np.concatenate(batches, axis=0)


class PixelImageEncoder:
    """Small deterministic image encoder for smoke tests, not production retrieval."""

    def __init__(self, image_size: int = 16) -> None:
        self.image_size = image_size
        self.dimension = image_size * image_size * 3

    def encode(self, images: Sequence[Image.Image], batch_size: int = 32) -> np.ndarray:
        del batch_size
        vectors = []
        for image in images:
            resized = image.convert("RGB").resize(
                (self.image_size, self.image_size), Image.Resampling.BILINEAR
            )
            vector = np.asarray(resized, dtype=np.float32).reshape(-1) / 255.0
            norm = float(np.linalg.norm(vector))
            if norm > 0:
                vector /= norm
            vectors.append(vector)
        if not vectors:
            return np.empty((0, self.dimension), dtype=np.float32)
        return np.stack(vectors).astype(np.float32)


def create_image_encoder(
    backend: str,
    model_name: str = DEFAULT_CLIP_MODEL,
    device: str = "auto",
    dimension: int | None = None,
) -> ImageEncoder:
    normalized = backend.strip().casefold().replace("_", "-")
    if normalized == "transformers-clip":
        return TransformersClipImageEncoder(model_name=model_name, device=device)
    if normalized == "pixel":
        if dimension is None:
            return PixelImageEncoder()
        image_size = round((dimension / 3) ** 0.5)
        if image_size * image_size * 3 != dimension:
            raise ValueError(f"Invalid pixel encoder dimension: {dimension}")
        return PixelImageEncoder(image_size=image_size)
    raise ValueError(f"Unsupported image embedding backend: {backend}")
