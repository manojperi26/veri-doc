import io
from pypdf import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
from typing import List
from api.schemas import DocumentChunk, DocumentMetadata
from processing.cleaner import clean_text
from processing.chunker import chunk_text

def load_pdf(file_bytes: bytes, file_name: str, document_id: str) -> List[DocumentChunk]:
    chunks = []
    
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            page_num = i + 1
            
            # Fallback to OCR if text is extremely short or empty
            if not text or len(text.strip()) < 50:
                try:
                    # Convert page to image
                    # Note: convert_from_bytes extracts all pages, so we need to process specific page if possible
                    # To be efficient, just convert the whole doc and pick the page, or use a workaround.
                    # For simplicity, convert all pages if needed, but it's better to just convert the specific page.
                    images = convert_from_bytes(file_bytes, first_page=page_num, last_page=page_num)
                    if images:
                        text = pytesseract.image_to_string(images[0])
                except Exception as e:
                    print(f"OCR failed for {file_name} page {page_num}: {e}")
            
            cleaned_text = clean_text(text)
            if cleaned_text:
                metadata = DocumentMetadata(
                    file_name=file_name,
                    file_type="pdf",
                    page_number=page_num,
                    document_id=document_id
                )
                page_chunks = chunk_text(cleaned_text, metadata)
                chunks.extend(page_chunks)
    except Exception as e:
        print(f"Failed to process PDF {file_name}: {e}")
        
    return chunks
