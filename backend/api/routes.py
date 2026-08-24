import os
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Query
from fastapi.concurrency import run_in_threadpool
from typing import Optional
from pydantic import BaseModel, Field
from services import rag_service
from services.session_store import session_store
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_SESSION_ID_LENGTH = 128
SUPPORTED_FILE_TYPES = {"pdf", "docx", "pptx", "txt"}

def get_session_id(x_session_id: Optional[str] = Header(None, alias="X-Session-ID"), session_id: Optional[str] = Query(None)) -> str:
    value = x_session_id or session_id
    if value and value.strip():
        sid = value.strip()
        if len(sid) > MAX_SESSION_ID_LENGTH:
            raise HTTPException(status_code=400, detail="Session ID is too long.")
        return sid
    return "default"

class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4_000)

class ChatResponse(BaseModel):
    answer: str
    citations: list
    debug: dict = None

class ConfigKeysRequest(BaseModel):
    groq_api_key: Optional[str] = Field(default=None, max_length=1_024)
    huggingface_api_key: Optional[str] = Field(default=None, max_length=1_024)

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None)
):
    sid = get_session_id(x_session_id, session_id)
    try:
        contents = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Document exceeds the 25 MB upload limit.")

        file_ext = Path(file.filename or "").suffix.lower().lstrip(".")
        if file_ext not in SUPPORTED_FILE_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported file format")
            
        doc = await run_in_threadpool(
            rag_service.process_document, contents, file.filename or "document", file_ext, sid
        )
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Document upload failed")
        raise HTTPException(status_code=500, detail="Unable to process the document.") from e

@router.get("/documents")
async def get_documents(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None)
):
    sid = get_session_id(x_session_id, session_id)
    return rag_service.get_documents(session_id=sid)

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None)
):
    sid = get_session_id(x_session_id, session_id)
    rag_service.delete_document(doc_id, session_id=sid)
    return {"status": "success"}

@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None)
):
    sid = get_session_id(x_session_id, session_id)
    try:
        result = await run_in_threadpool(rag_service.chat, req.query, sid)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat request failed")
        raise HTTPException(status_code=500, detail="Unable to generate an answer right now.") from e

@router.post("/session/reset")
async def reset_session(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None)
):
    sid = get_session_id(x_session_id, session_id)
    rag_service.reset_session(session_id=sid)
    return {"status": "success"}

@router.post("/chat/clear")
async def clear_chat(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None)
):
    sid = get_session_id(x_session_id, session_id)
    rag_service.clear_chat(session_id=sid)
    return {"status": "success"}

@router.get("/documents/{doc_id}/summary")
async def get_summary(
    doc_id: str,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None)
):
    sid = get_session_id(x_session_id, session_id)
    return rag_service.get_document_summary(doc_id, session_id=sid)

@router.get("/documents/questions")
async def get_questions(
    doc_id: str = None,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None)
):
    sid = get_session_id(x_session_id, session_id)
    return rag_service.get_document_questions(doc_id, session_id=sid)

@router.get("/health")
async def health():
    return {"status": "ok"}

# --- API Key Configuration ---

@router.get("/config/status")
async def config_status(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None)
):
    sid = get_session_id(x_session_id, session_id)
    session = session_store.get_session(sid)
    groq_ok = bool(session.groq_api_key or settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY"))
    huggingface_ok = bool(session.huggingface_api_key or settings.HUGGINGFACE_API_KEY or os.environ.get("HUGGINGFACE_API_KEY"))
    return {
        "groq_configured": groq_ok,
        "huggingface_configured": huggingface_ok,
    }

@router.post("/config/keys")
async def update_keys(
    req: ConfigKeysRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None)
):
    sid = get_session_id(x_session_id, session_id)
    session = session_store.get_session(sid)
    try:
        if req.groq_api_key and req.groq_api_key.strip():
            session.groq_api_key = req.groq_api_key.strip()
        if req.huggingface_api_key and req.huggingface_api_key.strip():
            session.huggingface_api_key = req.huggingface_api_key.strip()

        groq_ok = bool(session.groq_api_key or settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY"))
        huggingface_ok = bool(session.huggingface_api_key or settings.HUGGINGFACE_API_KEY or os.environ.get("HUGGINGFACE_API_KEY"))

        return {
            "status": "success",
            "groq_configured": groq_ok,
            "huggingface_configured": huggingface_ok,
        }
    except Exception as e:
        logger.exception("API key update failed")
        raise HTTPException(status_code=500, detail="Unable to save API keys.") from e
