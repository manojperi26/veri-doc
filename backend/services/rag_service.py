from typing import List, Dict, Any, Optional
from services.session_store import session_store
from retrieval import hybrid_retriever, embedder, reranker
from intelligence import compressor, generator, summarizer
from loaders import pdf_loader, docx_loader, pptx_loader, txt_loader
import uuid

def process_document(file_bytes: bytes, file_name: str, file_type: str, session_id: str = "default"):
    session = session_store.get_session(session_id)
    doc_id = str(uuid.uuid4())
    
    # 1. Load & Chunk
    chunks = []
    if file_type == "pdf":
        chunks = pdf_loader.load_pdf(file_bytes, file_name, doc_id)
    elif file_type in ["doc", "docx"]:
        chunks = docx_loader.load_docx(file_bytes, file_name, doc_id)
    elif file_type in ["ppt", "pptx"]:
        chunks = pptx_loader.load_pptx(file_bytes, file_name, doc_id)
    else: # txt
        chunks = txt_loader.load_txt(file_bytes, file_name, doc_id)
        
    if not chunks:
        raise ValueError("Could not extract text from document.")
        
    # 2. Embed
    texts = [c.text for c in chunks]
    embeddings = embedder.get_embeddings(texts)
    
    # 3. Store Dense (In-Memory Vector Store for this Session)
    session.vector_store.upsert_chunks(chunks, embeddings)
    
    # 4. Store Sparse (BM25 for this Session)
    session.bm25_store.add_chunks(chunks)
    
    # Calculate page count roughly for metadata
    pages = set([c.metadata.page_number or c.metadata.slide_number or 1 for c in chunks])
    
    session.documents[doc_id] = {
        "id": doc_id,
        "name": file_name,
        "type": file_type,
        "pages": len(pages),
        "status": "Ready",
        "sample_text": texts[0] if texts else ""
    }
    
    return session.documents[doc_id]

def get_documents(session_id: str = "default"):
    session = session_store.get_session(session_id)
    return list(session.documents.values())

def delete_document(doc_id: str, session_id: str = "default"):
    session = session_store.get_session(session_id)
    if doc_id in session.documents:
        session.vector_store.delete_by_document(doc_id)
        session.bm25_store.delete_by_document(doc_id)
        del session.documents[doc_id]

def reset_session(session_id: str = "default"):
    session_store.reset_session(session_id)

def clear_chat(session_id: str = "default"):
    session = session_store.get_session(session_id)
    session.memory.clear()

def chat(query: str, session_id: str = "default") -> dict:
    session = session_store.get_session(session_id)
    # Search using the user's exact wording. Rewriting every question with an
    # LLM can silently change its meaning before document retrieval.
    search_query = query
    depth = 8
    qtype = "Document-grounded"

    hybrid_results = hybrid_retriever.retrieve(search_query, top_k=15, session=session)
    reranked = reranker.rerank(search_query, hybrid_results, top_k=depth)
    compressed = compressor.compress_context(search_query, reranked, session=session)
    result = generator.generate_answer(query, compressed, session=session)
    
    # Update Memory
    session.memory.add_user_message(query)
    session.memory.add_ai_message(result["answer"])
    
    return {
        "answer": result["answer"],
        "citations": result["citations"],
        "debug": {
            "query_type": qtype,
            "retrieval_depth": depth,
            "hybrid_results": len(hybrid_results),
            "reranked_chunks": len(reranked),
            "compressed_chunks": len(compressed),
            "retrieved_sources": compressed
        }
    }

def get_document_summary(doc_id: str, session_id: str = "default"):
    session = session_store.get_session(session_id)
    doc = session.documents.get(doc_id)
    if not doc:
        return {}
    return summarizer.generate_summary(doc["sample_text"], session=session)

def get_document_questions(doc_id: str = None, session_id: str = "default"):
    session = session_store.get_session(session_id)
    text = ""
    if doc_id and doc_id in session.documents:
        text = session.documents[doc_id]["sample_text"]
    elif session.documents:
        text = list(session.documents.values())[0]["sample_text"]
        
    if text:
        return summarizer.generate_questions(text, session=session)
    return []
