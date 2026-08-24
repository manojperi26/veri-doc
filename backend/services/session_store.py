import threading
from typing import Dict, Any, Optional
from retrieval.bm25_store import BM25Store
from retrieval.vector_store import VectorStore
from memory.conversation import ConversationMemory

class UserSession:
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.documents: Dict[str, dict] = {}
        self.memory: ConversationMemory = ConversationMemory()
        self.vector_store: VectorStore = VectorStore()
        self.bm25_store: BM25Store = BM25Store()
        self.groq_api_key: Optional[str] = None
        self.huggingface_api_key: Optional[str] = None

class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}
        self._lock = threading.Lock()

    def get_session(self, session_id: str = "default") -> UserSession:
        sid = session_id.strip() if session_id and session_id.strip() else "default"
        with self._lock:
            if sid not in self._sessions:
                self._sessions[sid] = UserSession(sid)
            return self._sessions[sid]

    def reset_session(self, session_id: str = "default"):
        sid = session_id.strip() if session_id and session_id.strip() else "default"
        with self._lock:
            if sid in self._sessions:
                del self._sessions[sid]

    def clear_all(self):
        with self._lock:
            self._sessions.clear()

session_store = SessionStore()
