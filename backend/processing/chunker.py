import re
from typing import List, Dict, Any
from api.schemas import DocumentChunk, DocumentMetadata
from config import settings

def chunk_text(text: str, metadata: DocumentMetadata) -> List[DocumentChunk]:
    """
    Structure-aware chunking.
    Attempts to split by paragraphs and preserve groupings like bullets.
    """
    if not text:
        return []
        
    paragraphs = re.split(r'\n\n+', text)
    chunks = []
    current_chunk_text = ""
    chunk_index = 0
    
    for para in paragraphs:
        # If adding this paragraph exceeds chunk size, and current_chunk is not empty
        if len(current_chunk_text) + len(para) > settings.CHUNK_SIZE and current_chunk_text:
            # Save current chunk
            chunk_meta = metadata.model_copy(deep=True)
            chunk_meta.chunk_id = f"{metadata.document_id}_{metadata.page_number or 0}_{chunk_index}"
            chunks.append(DocumentChunk(text=current_chunk_text.strip(), metadata=chunk_meta))
            
            # Start new chunk with overlap
            # Find the last few sentences or characters for overlap
            overlap_text = current_chunk_text[-settings.CHUNK_OVERLAP:]
            # Try to snap to the nearest word boundary
            space_idx = overlap_text.find(' ')
            if space_idx != -1:
                overlap_text = overlap_text[space_idx+1:]
                
            current_chunk_text = overlap_text + "\n\n" + para
            chunk_index += 1
        else:
            if current_chunk_text:
                current_chunk_text += "\n\n" + para
            else:
                current_chunk_text = para
                
    if current_chunk_text:
        chunk_meta = metadata.model_copy(deep=True)
        chunk_meta.chunk_id = f"{metadata.document_id}_{metadata.page_number or 0}_{chunk_index}"
        chunks.append(DocumentChunk(text=current_chunk_text.strip(), metadata=chunk_meta))
        
    return chunks
