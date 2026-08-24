import threading
from typing import List, Optional
import numpy as np

_model = None
_lock = threading.Lock()

def get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return _model

def reset_model():
    global _model
    with _lock:
        _model = None

def get_embedding(text: str) -> List[float]:
    model = get_model()
    if not model:
        raise RuntimeError("Embedding model is not loaded.")
    embedding = model.encode(text)
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    return embedding.tolist()

def get_embeddings(texts: List[str]) -> List[List[float]]:
    model = get_model()
    if not model:
        raise RuntimeError("Embedding model is not loaded.")
    embeddings = model.encode(texts)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = np.divide(embeddings, norms, out=np.zeros_like(embeddings), where=norms!=0)
    return embeddings.tolist()
