from pydantic import BaseModel
from typing import List, Optional

class DocumentMetadata(BaseModel):
    file_name: str
    file_type: str
    page_number: Optional[int] = None
    slide_number: Optional[int] = None
    document_id: str
    chunk_id: Optional[str] = None

class DocumentChunk(BaseModel):
    text: str
    metadata: DocumentMetadata

class ConfigUpdateRequest(BaseModel):
    groq_api_key: Optional[str] = None
    pinecone_api_key: Optional[str] = None
