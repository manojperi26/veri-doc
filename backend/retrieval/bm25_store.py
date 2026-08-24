from rank_bm25 import BM25Okapi
from typing import List, Dict, Any, Optional
from api.schemas import DocumentChunk
import string

def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text.split()

class BM25Store:
    def __init__(self):
        self._chunks: List[DocumentChunk] = []
        self._bm25: Optional[BM25Okapi] = None

    def add_chunks(self, chunks: List[DocumentChunk]):
        self._chunks.extend(chunks)
        self.rebuild_index()

    def rebuild_index(self):
        if not self._chunks:
            self._bm25 = None
            return
        tokenized_corpus = [_tokenize(chunk.text) for chunk in self._chunks]
        self._bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query: str, top_k: int = 10, document_id: Optional[str] = None) -> List[Dict]:
        if not self._bm25 or not self._chunks:
            return []
            
        tokenized_query = _tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)
        
        results = []
        for i, score in enumerate(scores):
            chunk = self._chunks[i]
            if document_id and chunk.metadata.document_id != document_id:
                continue
            meta = chunk.metadata.model_dump(exclude_none=True)
            results.append({
                "chunk_id": chunk.metadata.chunk_id,
                "score": float(score),
                "text": chunk.text,
                "metadata": meta
            })
                
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_by_document(self, document_id: str):
        self._chunks = [c for c in self._chunks if c.metadata.document_id != document_id]
        self.rebuild_index()

    def clear_all(self):
        self._chunks = []
        self._bm25 = None

# Default singleton instance for backward compatibility & simple single-user usage
default_bm25_store = BM25Store()

def add_chunks(chunks: List[DocumentChunk]):
    default_bm25_store.add_chunks(chunks)

def rebuild_index():
    default_bm25_store.rebuild_index()

def search(query: str, top_k: int = 10, document_id: Optional[str] = None) -> List[Dict]:
    return default_bm25_store.search(query, top_k=top_k, document_id=document_id)

def delete_by_document(document_id: str):
    default_bm25_store.delete_by_document(document_id)

def clear_all():
    default_bm25_store.clear_all()

def reset():
    default_bm25_store.clear_all()
