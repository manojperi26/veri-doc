import re
import unicodedata

def clean_text(text: str) -> str:
    """
    Cleans raw text extracted from documents.
    Normalizes unicode, standardizes line endings, removes redundant whitespace,
    and preserves structural elements like headings and bullets.
    """
    if not text:
        return ""
    
    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)
    
    # Standardize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove redundant spaces but preserve newlines
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Remove more than 2 consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Strip leading/trailing whitespace
    return text.strip()
