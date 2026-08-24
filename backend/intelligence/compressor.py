from typing import List, Dict, Optional, Any

def compress_context(query: str, chunks: List[Dict], session: Optional[Any] = None) -> List[Dict]:
    """
    Return the best reranked chunks without asking another LLM to rewrite them.

    Rewriting evidence can omit answer-bearing text or misclassify relevant
    content. The answer model receives the original source text and cites it.
    """
    if not chunks:
        return chunks
        
    return chunks[:5]
