import threading
from typing import List, Dict, Optional

_model = None
_lock = threading.Lock()

def get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                try:
                    from sentence_transformers import CrossEncoder
                    _model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                except Exception as e:
                    print(f"Warning: Failed to load cross-encoder model: {e}")
                    _model = None
    return _model

def reset_model():
    global _model
    with _lock:
        _model = None

def rerank(query: str, results: List[Dict], top_k: int = 8) -> List[Dict]:
    if not results:
        return results[:top_k]
        
    model = get_model()
    if not model:
        return results[:top_k]
        
    pairs = [[query, res["text"]] for res in results]
    scores = model.predict(pairs)
    
    for i, score in enumerate(scores):
        results[i]["rerank_score"] = float(score)
        
    results.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
    return results[:top_k]
