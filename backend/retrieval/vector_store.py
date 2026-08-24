from typing import List, Dict, Any, Optional
from api.schemas import DocumentChunk
import numpy as np

class VectorStore:
    def __init__(self):
        self._chunks: List[Dict[str, Any]] = []

    def upsert_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        if len(chunks) != len(embeddings):
            raise ValueError("Each document chunk must have exactly one embedding.")

        for chunk, embedding in zip(chunks, embeddings):
            meta = chunk.metadata.model_dump(exclude_none=True)
            meta["text"] = chunk.text
            emb_arr = np.array(embedding, dtype=np.float32)
            norm = np.linalg.norm(emb_arr)
            if norm > 0:
                emb_arr = emb_arr / norm
            
            self._chunks.append({
                "chunk_id": chunk.metadata.chunk_id,
                "vector": emb_arr,
                "text": chunk.text,
                "metadata": meta
            })

    def search(self, query_embedding: List[float], top_k: int = 10, filter_dict: Optional[Dict] = None) -> List[Dict]:
        if not self._chunks:
            return []
        
        q_vec = np.array(query_embedding, dtype=np.float32)
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm

        doc_id_filter = filter_dict.get("document_id") if filter_dict else None
        
        candidates = []
        for item in self._chunks:
            if doc_id_filter and item["metadata"].get("document_id") != doc_id_filter:
                continue
            
            score = float(np.dot(q_vec, item["vector"]))
            candidates.append({
                "chunk_id": item["chunk_id"],
                "score": score,
                "text": item["text"],
                "metadata": {k: v for k, v in item["metadata"].items() if k != "text"}
            })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

    def delete_by_document(self, document_id: str):
        self._chunks = [item for item in self._chunks if item["metadata"].get("document_id") != document_id]

    def clear_all(self):
        self._chunks = []

# Default singleton instance for backward compatibility
default_vector_store = VectorStore()

def upsert_chunks(chunks: List[DocumentChunk], embeddings: List[List[float]]):
    default_vector_store.upsert_chunks(chunks, embeddings)

def search(query_embedding: List[float], top_k: int = 10, filter_dict: Optional[Dict] = None) -> List[Dict]:
    return default_vector_store.search(query_embedding, top_k=top_k, filter_dict=filter_dict)

def delete_by_document(document_id: str):
    default_vector_store.delete_by_document(document_id)

def clear_all():
    default_vector_store.clear_all()

def reset():
    default_vector_store.clear_all()
