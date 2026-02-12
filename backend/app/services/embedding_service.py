"""
Embedding service for resume/JD semantic similarity.
Uses sentence-transformers (lazy-loaded) for ATS and job-fit scoring.
"""

from typing import List, Optional

import numpy as np

# Lazy load to avoid slow startup
_model = None
_MODEL_NAME = "all-MiniLM-L6-v2"


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_text(text: str) -> np.ndarray:
    """Embed a single string. Returns 384-dim vector."""
    if not (text and text.strip()):
        return np.zeros(384, dtype=np.float32)
    model = _get_model()
    return model.encode(text.strip(), convert_to_numpy=True)


def embed_texts(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """Embed multiple strings. Returns (n, 384) array."""
    texts = [t.strip() if t else "" for t in texts]
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    model = _get_model()
    return model.encode(texts, batch_size=batch_size, convert_to_numpy=True)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors (or batch). Scalar in [0, 1] for normalized vectors."""
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    if a.size != b.size:
        return 0.0
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
