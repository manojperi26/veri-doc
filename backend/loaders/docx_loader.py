import io
from docx import Document
from typing import List
from api.schemas import DocumentChunk, DocumentMetadata
from processing.cleaner import clean_text
from processing.chunker import chunk_text

def load_docx(file_bytes: bytes, file_name: str, document_id: str) -> List[DocumentChunk]:
    chunks = []
    
    try:
        doc = Document(io.BytesIO(file_bytes))
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
            
        text = "\n".join(full_text)
        cleaned_text = clean_text(text)
        
        if cleaned_text:
            metadata = DocumentMetadata(
                file_name=file_name,
                file_type="docx",
                document_id=document_id
            )
            # docx doesn't easily have page numbers natively in python-docx
            chunks = chunk_text(cleaned_text, metadata)
            
    except Exception as e:
        print(f"Failed to process DOCX {file_name}: {e}")
        
    return chunks
