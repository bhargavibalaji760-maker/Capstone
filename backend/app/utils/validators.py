import re
from typing import Optional, List

def validate_age(age: int) -> bool:
    """Validates if the age is within a realistic human range (0-120)."""
    return 0 <= age <= 120

def validate_gender(gender: str) -> bool:
    """Validates gender input."""
    allowed = ["Male", "Female", "Non-binary", "Other", "All", "M", "F", "U"]
    return gender.strip().title() in allowed or gender in allowed

def validate_nct_id(nct_id: str) -> bool:
    """Validates ClinicalTrials.gov NCT ID format (e.g., NCT12345678)."""
    return bool(re.match(r'^NCT\d{8}$', nct_id.strip().upper()))

def clean_medical_text(text: Optional[str]) -> str:
    """Removes extra whitespace and non-standard characters from medical notes."""
    if not text:
        return ""
    # Standardize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove some common PDF artifacts or noise if needed
    return text.strip()

def extract_entities_from_string(text: str, delimiter: str = ",") -> List[str]:
    """Splits a string by delimiter and cleans each item (e.g., for list of conditions)."""
    if not text:
        return []
    return [item.strip() for item in text.split(delimiter) if item.strip()]
