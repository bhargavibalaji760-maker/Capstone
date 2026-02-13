def extract_criteria(text: str):
    """
    MOCK FUNCTION: In the final version, this will use spaCy.
    Currently returns dummy data for testing the UI.
    """
    return {
        "inclusion": ["Age >= 18", "Diagnosis: Type 2 Diabetes"],
        "exclusion": ["Pregnancy", "History of Heart Failure"]
    }
