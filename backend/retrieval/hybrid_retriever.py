from typing import Any, List, Dict, Optional
from retrieval import vector_store, bm25_store, embedder
import numpy as np

DENSE_WEIGHT = 0.6
BM25_WEIGHT = 0.4

def min_max_normalize(scores: List[float]) -> List[float]:
    if not scores:
        return []
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [1.0] * len(scores)
    return [(s - min_score) / (max_score - min_score) for s in scores]

def retrieve(query: str, top_k: int = 15, document_id: Optional[str] = None, session: Optional[Any] = None) -> List[Dict]:
    # Determine which stores to search
    v_store = session.vector_store if session and hasattr(session, 'vector_store') else vector_store.default_vector_store
    b_store = session.bm25_store if session and hasattr(session, 'bm25_store') else bm25_store.default_bm25_store

    # 1. Get query embedding
    query_emb = embedder.get_embedding(query)
    
    # 2. Dense retrieval via vector store
    filter_dict = {"document_id": document_id} if document_id else None
    dense_results = v_store.search(query_emb, top_k=top_k, filter_dict=filter_dict)
    
    # 3. BM25 retrieval
    bm25_results = b_store.search(query, top_k=top_k, document_id=document_id)
    
    # Merge
    combined = {}
    
    dense_scores = [r["score"] for r in dense_results]
    bm25_scores = [r["score"] for r in bm25_results]
    
    norm_dense = min_max_normalize(dense_scores)
    norm_bm25 = min_max_normalize(bm25_scores)
    
    for i, res in enumerate(dense_results):
        cid = res["chunk_id"]
        combined[cid] = {
            "chunk_id": cid,
            "text": res["text"],
            "metadata": res["metadata"],
            "dense_score": norm_dense[i],
            "bm25_score": 0.0,
            "method": "Dense"
        }
        
    for i, res in enumerate(bm25_results):
        cid = res["chunk_id"]
        if cid in combined:
            combined[cid]["bm25_score"] = norm_bm25[i]
            combined[cid]["method"] = "Hybrid"
        else:
            combined[cid] = {
                "chunk_id": cid,
                "text": res["text"],
                "metadata": res["metadata"],
                "dense_score": 0.0,
                "bm25_score": norm_bm25[i],
                "method": "BM25"
            }
            
    # Calculate hybrid score
    final_results = []
    for cid, data in combined.items():
        hybrid_score = (data["dense_score"] * DENSE_WEIGHT) + (data["bm25_score"] * BM25_WEIGHT)
        data["score"] = hybrid_score
        final_results.append(data)
        
    final_results.sort(key=lambda x: x["score"], reverse=True)
    return final_results[:top_k]
