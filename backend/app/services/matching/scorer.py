import random

def calculate_match_score(patient_data, trial_criteria):
    """
    MOCK FUNCTION: Returns a random score between 60 and 95.
    Real logic will compare Patient Attributes vs Trial Rules.
    """
    score = random.randint(60, 99)
    reason = "Patient meets age and diagnosis criteria. No exclusions found."
    
    if score < 70:
        reason = "Potential conflict with current medication."
        
    return score, reason
