from typing import List
from api.schemas import DocumentChunk, DocumentMetadata
from processing.cleaner import clean_text
from processing.chunker import chunk_text

def load_txt(file_bytes: bytes, file_name: str, document_id: str) -> List[DocumentChunk]:
    chunks = []
    
    try:
        text = file_bytes.decode('utf-8')
        cleaned_text = clean_text(text)
        
        if cleaned_text:
            metadata = DocumentMetadata(
                file_name=file_name,
                file_type="txt",
                document_id=document_id
            )
            chunks = chunk_text(cleaned_text, metadata)
            
    except Exception as e:
        print(f"Failed to process TXT {file_name}: {e}")
        
    return chunks
