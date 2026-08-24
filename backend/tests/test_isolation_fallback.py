import pytest
from fastapi.testclient import TestClient as APIClient
import os
import sys
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["TESTING"] = "1"

from main import app
from services.session_store import session_store
from services import rag_service
from retrieval import embedder, reranker
from intelligence import llm
from config import settings

api_client = APIClient(app)

@pytest.fixture(autouse=True)
def reset_all_state():
    session_store.clear_all()
    embedder.reset_model()
    reranker.reset_model()
    settings.GROQ_API_KEY = ""
    settings.HUGGINGFACE_API_KEY = ""
    yield
    session_store.clear_all()
    embedder.reset_model()
    reranker.reset_model()

# 1. Health check does not trigger lazy ML model loading
def test_health_check_does_not_load_models():
    assert embedder._model is None
    assert reranker._model is None
    
    response = api_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
    assert embedder._model is None
    assert reranker._model is None

# 2. Session isolation for documents
def test_session_document_isolation():
    session_store.clear_all()
    
    doc_a = rag_service.process_document(b"Content for session A", "docA.txt", "txt", session_id="session_A")
    doc_b = rag_service.process_document(b"Content for session B", "docB.txt", "txt", session_id="session_B")
    
    docs_a = rag_service.get_documents(session_id="session_A")
    docs_b = rag_service.get_documents(session_id="session_B")
    
    assert len(docs_a) == 1
    assert docs_a[0]["name"] == "docA.txt"
    
    assert len(docs_b) == 1
    assert docs_b[0]["name"] == "docB.txt"

# 3. Session isolation for conversation memory
def test_session_memory_isolation():
    session_a = session_store.get_session("session_A")
    session_b = session_store.get_session("session_B")
    
    session_a.memory.add_user_message("Hello from A")
    session_b.memory.add_user_message("Hello from B")
    
    assert session_a.memory.get_history() == [{"role": "user", "content": "Hello from A"}]
    assert session_b.memory.get_history() == [{"role": "user", "content": "Hello from B"}]

# 4. Session isolation for BM25 and Vector stores
def test_session_retrieval_store_isolation():
    rag_service.process_document(b"Python programming guide for beginners", "python.txt", "txt", session_id="session_A")
    rag_service.process_document(b"JavaScript web development basics", "js.txt", "txt", session_id="session_A")
    rag_service.process_document(b"Database SQL query optimization", "sql.txt", "txt", session_id="session_A")

    rag_service.process_document(b"Cooking recipes and baking cakes", "cooking.txt", "txt", session_id="session_B")
    
    session_a = session_store.get_session("session_A")
    session_b = session_store.get_session("session_B")
    
    bm25_a = session_a.bm25_store.search("Python")
    bm25_b = session_b.bm25_store.search("Python")
    
    # Session A's top BM25 result must be python.txt with positive score
    assert len(bm25_a) == 3
    assert bm25_a[0]["metadata"]["file_name"] == "python.txt"
    assert bm25_a[0]["score"] > 0
    
    # Session B's BM25 search must NOT return any documents from Session A
    assert all(item["metadata"]["file_name"] != "python.txt" for item in bm25_b)
    assert all(item["metadata"]["file_name"] == "cooking.txt" for item in bm25_b)
    assert bm25_b[0]["score"] == 0.0

    # Vector store isolation check
    q_emb = embedder.get_embedding("Python")
    vec_b = session_b.vector_store.search(q_emb)
    assert all(item["metadata"]["file_name"] == "cooking.txt" for item in vec_b)

# 5. Config / Key isolation per session
def test_config_keys_session_isolation():
    res_a = api_client.post("/api/config/keys", json={"groq_api_key": "key_A"}, headers={"X-Session-ID": "session_A"})
    assert res_a.status_code == 200
    
    sess_a = session_store.get_session("session_A")
    sess_b = session_store.get_session("session_B")
    
    assert sess_a.groq_api_key == "key_A"
    assert sess_b.groq_api_key is None

# 6. AI Provider Fallback System (Groq -> Hugging Face)
def test_ai_fallback_groq_success():
    messages = [{"role": "user", "content": "Hello"}]
    settings.GROQ_API_KEY = "test_groq_key"
    
    with patch("intelligence.llm._call_groq", return_value="Groq Answer") as mock_groq, \
         patch("intelligence.llm._call_huggingface", return_value="Hugging Face Answer") as mock_huggingface:
        
        ans = llm.chat_completion(messages, session=None)
        assert ans == "Groq Answer"
        mock_groq.assert_called_once()
        mock_huggingface.assert_not_called()

def test_ai_fallback_groq_failed_huggingface_success():
    messages = [{"role": "user", "content": "Hello"}]
    settings.GROQ_API_KEY = "test_groq_key"
    settings.HUGGINGFACE_API_KEY = "test_huggingface_key"
    
    with patch("intelligence.llm._call_groq", side_effect=RuntimeError("Groq Rate Limit Exceeded")), \
         patch("intelligence.llm._call_huggingface", return_value="Hugging Face Answer") as mock_huggingface:
        
        ans = llm.chat_completion(messages, session=None)
        assert ans == "Hugging Face Answer"
        mock_huggingface.assert_called_once()

def test_ai_fallback_both_failed():
    messages = [{"role": "user", "content": "Hello"}]
    settings.GROQ_API_KEY = "key1"
    settings.HUGGINGFACE_API_KEY = "key2"
    
    with patch("intelligence.llm._call_groq", side_effect=RuntimeError("Groq Quota Exceeded")), \
         patch("intelligence.llm._call_huggingface", side_effect=RuntimeError("Hugging Face Quota Exceeded")):
        
        with pytest.raises(RuntimeError) as exc_info:
            llm.chat_completion(messages, session=None)
            
        assert "temporarily unavailable" in str(exc_info.value).lower()

def test_ai_fallback_every_new_request_tries_groq_first():
    messages = [{"role": "user", "content": "Req 1"}]
    settings.GROQ_API_KEY = "groq_key"
    settings.HUGGINGFACE_API_KEY = "huggingface_key"
    
    # Request 1 fails Groq, succeeds Hugging Face
    with patch("intelligence.llm._call_groq", side_effect=RuntimeError("Groq Rate Limit")), \
         patch("intelligence.llm._call_huggingface", return_value="Hugging Face Answer"):
        ans1 = llm.chat_completion(messages, session=None)
        assert ans1 == "Hugging Face Answer"
        
    # Request 2 SHOULD TRY GROQ AGAIN FIRST
    with patch("intelligence.llm._call_groq", return_value="Groq Answer 2") as mock_groq_2, \
         patch("intelligence.llm._call_huggingface", return_value="Hugging Face Answer 2") as mock_huggingface_2:
        ans2 = llm.chat_completion(messages, session=None)
        assert ans2 == "Groq Answer 2"
        mock_groq_2.assert_called_once()
        mock_huggingface_2.assert_not_called()
