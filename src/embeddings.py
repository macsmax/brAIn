"""Local embedding model for semantic search."""

import os
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_DIR = os.path.join(os.environ.get("BRAIN_DATA_DIR", "data"), "models")

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        os.makedirs(CACHE_DIR, exist_ok=True)
        _model = SentenceTransformer(MODEL_NAME, cache_folder=CACHE_DIR)
    return _model


def embed(text: str) -> bytes:
    """Return embedding as raw float32 bytes for SQLite storage."""
    vec = _get_model().encode(text, normalize_embeddings=True)
    return np.array(vec, dtype=np.float32).tobytes()


def cosine_similarity(a: bytes, b: bytes) -> float:
    """Cosine similarity between two float32 byte vectors (pre-normalized)."""
    va = np.frombuffer(a, dtype=np.float32)
    vb = np.frombuffer(b, dtype=np.float32)
    return float(np.dot(va, vb))
