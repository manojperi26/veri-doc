import pytest
from fastapi.testclient import TestClient as APIClient
import os
import sys

# Ensure backend root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["TESTING"] = "1"

from main import app
from processing.cleaner import clean_text
from processing.chunker import chunk_text
from api.schemas import DocumentMetadata, DocumentChunk
from retrieval.bm25_store import _tokenize, BM25Store, clear_all as bm25_clear_all
from retrieval.vector_store import clear_all as vector_clear_all
from retrieval.hybrid_retriever import min_max_normalize
from retrieval import hybrid_retriever
from intelligence import generator
from services.session_store import session_store
from typing import get_type_hints

api_client = APIClient(app)

@pytest.fixture(autouse=True)
def reset_test_state():
    session_store.clear_all()
    bm25_clear_all()
    vector_clear_all()
    yield
    session_store.clear_all()
    bm25_clear_all()
    vector_clear_all()

def test_health_check():
    response = api_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_invalid_chat_and_session_id_are_rejected():
    assert api_client.post("/api/chat", json={"query": ""}).status_code == 422
    response = api_client.get("/api/documents", headers={"X-Session-ID": "x" * 129})
    assert response.status_code == 400

def test_legacy_office_formats_are_rejected_before_processing():
    response = api_client.post(
        "/api/documents/upload",
        files={"file": ("legacy.doc", b"not a DOCX file", "application/msword")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file format"

def test_hybrid_retriever_annotations_resolve():
    assert "session" in get_type_hints(hybrid_retriever.retrieve)

def test_generator_uses_extractive_fallback_when_provider_refuses(monkeypatch):
    monkeypatch.setattr(
        generator,
        "chat_completion",
        lambda *args, **kwargs: '{"classification":"not_in_document","answer":"","source_ids":[]}',
    )
    context = [{
        "chunk_id": "cv-1",
        "text": "Languages: Python, C++, Java, SQL. Tools: PyTorch, FastAPI, Streamlit. Soft Skills: Problem-Solving, Teamwork.",
        "metadata": {"file_name": "cv.pdf", "page_number": 1},
    }]

    result = generator.generate_answer("What skills does Manoj have?", context)

    assert "Python" in result["answer"]
    assert "FastAPI" in result["answer"]
    assert result["citations"][0]["source_file"] == "cv.pdf"

def test_generator_returns_normal_grounded_answer_and_scope_status(monkeypatch):
    context = [{
        "chunk_id": "cv-1",
        "text": "Manoj knows Python and FastAPI.",
        "metadata": {"file_name": "cv.pdf", "page_number": 1},
    }]
    monkeypatch.setattr(
        generator,
        "chat_completion",
        lambda *args, **kwargs: '{"classification":"answer","answer":"Manoj knows Python and FastAPI.","source_ids":["source_0"]}',
    )
    answer = generator.generate_answer("What technologies does Manoj know?", context)
    assert answer["answer"] == "Manoj knows Python and FastAPI."
    assert answer["citations"] == [{"source_file": "cv.pdf", "page": 1, "chunk_id": "cv-1"}]

    monkeypatch.setattr(
        generator,
        "chat_completion",
        lambda *args, **kwargs: '{"classification":"out_of_scope","answer":"","source_ids":[]}',
    )
    out_of_scope = generator.generate_answer("What is the weather today?", context)
    assert out_of_scope["answer"] == generator.OUT_OF_SCOPE_ANSWER

def test_clean_text():
    raw_text = "This  is   a\n\n\n\ntest.\r\nNew line."
    cleaned = clean_text(raw_text)
    assert "This is a" in cleaned
    assert "\n\ntest.\nNew line." in cleaned

def test_chunk_text():
    import config
    orig_size = config.settings.CHUNK_SIZE
    config.settings.CHUNK_SIZE = 50
    
    meta = DocumentMetadata(file_name="test.txt", file_type="txt", document_id="doc1")
    text = "Paragraph 1 is here.\n\nParagraph 2 is slightly longer than the others.\n\nParagraph 3."
    
    chunks = chunk_text(text, meta)
    
    config.settings.CHUNK_SIZE = orig_size
    
    assert len(chunks) > 1
    assert chunks[0].metadata.document_id == "doc1"
    assert chunks[0].metadata.chunk_id == "doc1_0_0"
    
def test_bm25_tokenize():
    tokens = _tokenize("Hello, World! Testing 123.")
    assert tokens == ["hello", "world", "testing", "123"]

def test_min_max_normalize():
    scores = [1.0, 5.0, 10.0]
    norm = min_max_normalize(scores)
    assert norm[0] == 0.0
    assert norm[-1] == 1.0
    assert abs(norm[1] - 0.4444) < 0.001
    
    norm = min_max_normalize([5.0, 5.0])
    assert norm == [1.0, 1.0]

def test_bm25_integration():
    store = BM25Store()
    
    meta1 = DocumentMetadata(file_name="f1", file_type="txt", document_id="d1", chunk_id="c1")
    meta2 = DocumentMetadata(file_name="f2", file_type="txt", document_id="d2", chunk_id="c2")
    meta3 = DocumentMetadata(file_name="f3", file_type="txt", document_id="d3", chunk_id="c3")
    
    c1 = DocumentChunk(text="The quick brown fox", metadata=meta1)
    c2 = DocumentChunk(text="Jumps over the lazy dog", metadata=meta2)
    c3 = DocumentChunk(text="An unrelated document about cats and mice", metadata=meta3)
    
    store.add_chunks([c1, c2, c3])
    
    res = store.search("fox")
    assert len(res) == 3
    assert res[0]["chunk_id"] == "c1"
    assert res[0]["score"] > res[1]["score"]
