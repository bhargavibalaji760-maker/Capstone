import re
import os
from typing import List, Dict

def sanitize_pdf_text(text: str) -> str:
    """
    Post-processing for PDF extracted text.
    Fixes common ligatures, Removes control characters and excess newlines.
    """
    # Fix common PDF artifacts
    text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl').replace('ﬀ', 'ff')
    # Remove non-printable characters
    text = "".join(char for char in text if char.isprintable() or char == '\n')
    # Collapse multiple newlines/spaces
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

def get_file_extension(filename: str) -> str:
    """Safely extracts file extension."""
    return os.path.splitext(filename)[1].lower()

def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    """
    Splits large text into chunks for LLM processing, 
    attempting to break at sentence or paragraph boundaries.
    """
    if len(text) <= max_chars:
        return [text]
        
    chunks = []
    while text:
        if len(text) <= max_chars:
            chunks.append(text)
            break
            
        # Try to find a good breaking point (paragraph then sentence)
        boundary = text.rfind('\n\n', 0, max_chars)
        if boundary == -1:
            boundary = text.rfind('. ', 0, max_chars)
        
        if boundary == -1:
            boundary = max_chars
        else:
            boundary += 1 # Include the period or newline
            
        chunks.append(text[:boundary].strip())
        text = text[boundary:].strip()
        
    return chunks

def extract_metadata_from_filename(filename: str) -> Dict[str, str]:
    """Attempts to guess trial ID or patient name from filename."""
    metadata = {}
    # Find NCT ID
    nct_match = re.search(r'NCT\d{8}', filename, re.I)
    if nct_match:
        metadata['trial_id'] = nct_match.group(0).upper()
        
    return metadata
