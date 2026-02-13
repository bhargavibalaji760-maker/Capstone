"""
Formatters Module - Format data for display
"""

def format_patient_info(patient_dict):
    """Format patient information for display"""
    if not patient_dict:
        return {}
    
    return {
        "ID": patient_dict.get('subject_id', 'N/A'),
        "Gender": patient_dict.get('gender', 'N/A'),
        "Age": round(float(patient_dict.get('age', 0)), 1),
        "Diagnosis": patient_dict.get('diagnosis', 'N/A'),
        "Insurance": patient_dict.get('insurance', 'N/A'),
        "Deceased": "Yes" if patient_dict.get('deceased') else "No"
    }

def format_conditions(conditions_dict):
    """Format conditions and medications"""
    if not conditions_dict:
        return {"Conditions": "N/A", "Medications": "N/A"}
    
    conditions = conditions_dict.get('conditions', 'N/A')
    medications = conditions_dict.get('medications', 'N/A')
    
    # Split by pipe if present
    if isinstance(conditions, str):
        conditions = [c.strip() for c in conditions.split('|')]
    if isinstance(medications, str):
        medications = [m.strip() for m in medications.split('|')]
    
    return {
        "Conditions": conditions,
        "Medications": medications
    }

def format_trial_info(trial_dict):
    """Format trial information"""
    if not trial_dict:
        return {}
    
    return {
        "NCT ID": trial_dict.get('nct_id', 'N/A'),
        "Title": trial_dict.get('title', 'N/A'),
        "Inclusion Criteria": trial_dict.get('inclusion_criteria', 'N/A'),
        "Exclusion Criteria": trial_dict.get('exclusion_criteria', 'N/A')
    }
