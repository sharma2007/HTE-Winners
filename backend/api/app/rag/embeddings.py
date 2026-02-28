from __future__ import annotations

import hashlib
import math
import random

from app.config import settings


def embed_text(text: str) -> list[float]:
    """
    Hackathon-light embeddings.
    - mock: deterministic pseudo-random vector (stable across runs)
    - local: not implemented by default (kept minimal for MVP)
    """
    mode = (settings.embeddings_mode or "mock").lower()
    if mode != "mock":
        raise RuntimeError("EMBEDDINGS_MODE=local not implemented in this MVP; use EMBEDDINGS_MODE=mock")

    dim = int(settings.vector_dim)
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)
    vec = [rng.uniform(-1.0, 1.0) for _ in range(dim)]
    # L2 normalize for cosine distance
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]

