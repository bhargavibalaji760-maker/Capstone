"""
Text Processor Module - Clean and process text from documents
"""
import re
import io
import PyPDF2
from app.services.nlp import llm_service

def extract_text_from_pdf(file_bytes):
    """Extract raw text from a PDF file"""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def parse_patient_from_text(text):
    """
    Parse patient details from extracted text
    Heuristics to find Name, Age, Gender, and Diagnosis
    """
    # Attempt LLM extraction first if configured
    llm_result = llm_service.extract_patient_info(text)
    if llm_result:
        return llm_result
        
    cleaned = text.strip()
    
    # Heuristic for Name (often near 'Name:' or at start)
    name_match = re.search(r'Name:\s*([A-Za-z\s]+)', cleaned, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else "Unknown Patient"
    
    # Heuristic for Age
    age_match = re.search(r'Age:\s*(\d+)', cleaned, re.IGNORECASE)
    age = int(age_match.group(1)) if age_match else 0
    
    # Heuristic for Gender
    gender_match = re.search(r'Gender:\s*(M|F|Male|Female)', cleaned, re.IGNORECASE)
    gender = gender_match.group(1)[0].upper() if gender_match else "U"
    
    # Heuristic for Diagnosis
    # Look for common headers or keywords
    diag_match = re.search(r'(?:Diagnosis|Condition|Assessment):\s*([^\n.]+)', cleaned, re.IGNORECASE)
    diagnosis = diag_match.group(1).strip() if diag_match else "General Clinical Condition"
    
    # Clinical Notes (everything else or specific section)
    notes = cleaned[:500] + "..." if len(cleaned) > 500 else cleaned
    
    return {
        "name": name,
        "age": age,
        "gender": gender,
        "primary_condition": diagnosis,
        "clinical_notes": notes
    }

def clean_text(text):
    """Clean text by removing special characters and normalizing"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep letters, numbers, and basic punctuation
    text = re.sub(r'[^\w\s\-.,;]', '', text)
    return text.strip()

def extract_criteria_from_text(text):
    """
    Extract inclusion and exclusion criteria from text
    MOCK: Real implementation would use spaCy NER
    """
    cleaned_text = clean_text(text)
    
    # Simple heuristic: look for keywords
    inclusion_keywords = []
    exclusion_keywords = []
    
    # Common inclusion patterns
    if any(keyword in cleaned_text.lower() for keyword in ['diabetes', 'type 2']):
        inclusion_keywords.append('Diabetes')
    if any(keyword in cleaned_text.lower() for keyword in ['hypertension', 'high blood pressure']):
        inclusion_keywords.append('Hypertension')
    if any(keyword in cleaned_text.lower() for keyword in ['age 18', '18 years', 'adult']):
        inclusion_keywords.append('Age >= 18')
    
    # Common exclusion patterns
    if any(keyword in cleaned_text.lower() for keyword in ['pregnancy', 'pregnant']):
        exclusion_keywords.append('Pregnancy')
    if any(keyword in cleaned_text.lower() for keyword in ['cardiac', 'heart failure', 'myocardial']):
        exclusion_keywords.append('Cardiac Disease')
    if any(keyword in cleaned_text.lower() for keyword in ['kidney', 'renal', 'esrd']):
        exclusion_keywords.append('Renal Disease')
    
    return {
        "inclusion_keywords": inclusion_keywords if inclusion_keywords else ["General Population"],
        "exclusion_keywords": exclusion_keywords
    }

def extract_age_range(text):
    """Extract age range from text"""
    cleaned_text = clean_text(text)
    
    # Look for age patterns like "18-65" or "18 to 65"
    age_pattern = r'(\d+)\s*(?:to|-)\s*(\d+)'
    matches = re.findall(age_pattern, cleaned_text)
    
    if matches:
        min_age = int(matches[0][0])
        max_age = int(matches[0][1])
        return {"min_age": min_age, "max_age": max_age}
    
    # Look for just minimum age
    min_pattern = r'(?:age|minimum|min)\s+(\d+)'
    min_matches = re.findall(min_pattern, cleaned_text, re.IGNORECASE)
    if min_matches:
        return {"min_age": int(min_matches[0])}
    
    return {}

def parse_protocol(protocol_text):
    """Parse full protocol and extract all relevant information"""
    criteria = extract_criteria_from_text(protocol_text)
    age_info = extract_age_range(protocol_text)
    
    result = {
        "inclusion_keywords": criteria.get("inclusion_keywords", []),
        "exclusion_keywords": criteria.get("exclusion_keywords", [])
    }
    result.update(age_info)
    
    return result
