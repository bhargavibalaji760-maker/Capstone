"""
Rules Engine - Apply eligibility rules to patient data
"""
from app.utils.data_loader import get_patient_conditions

def check_age_criteria(age, min_age=None, max_age=None):
    """Check if patient age meets criteria"""
    if age == 0:  # Newborn or invalid
        return False, "Invalid age"
    
    if min_age and age < min_age:
        return False, f"Age {age} below minimum {min_age}"
    
    if max_age and age > max_age:
        return False, f"Age {age} exceeds maximum {max_age}"
    
    return True, f"Age {age} is within range"

def check_gender_criteria(patient_gender, required_gender=None):
    """Check if patient gender meets criteria"""
    if not required_gender:
        return True, "No gender restriction"
    
    if patient_gender.upper() == required_gender.upper():
        return True, f"Gender {patient_gender} matches requirement"
    
    return False, f"Gender {patient_gender} does not match requirement {required_gender}"

def check_diagnosis_inclusion(diagnosis, inclusion_keywords):
    """Check if patient diagnosis meets inclusion criteria"""
    if not inclusion_keywords:
        return True, "No diagnosis restriction"
    
    for keyword in inclusion_keywords:
        if keyword.lower() in diagnosis.lower():
            return True, f"Diagnosis contains '{keyword}'"
    
    return False, f"Diagnosis does not contain required keywords"

def check_diagnosis_exclusion(diagnosis, exclusion_keywords):
    """Check if patient diagnosis violates exclusion criteria"""
    if not exclusion_keywords:
        return True, "No exclusion restrictions"
    
    for keyword in exclusion_keywords:
        if keyword.lower() in diagnosis.lower():
            return False, f"Diagnosis contains excluded keyword '{keyword}'"
    
    return True, "No excluded conditions found"

def apply_rules(patient_data, trial_rules):
    """
    Apply trial rules to patient data and calculate score
    
    patient_data: dict with patient info
    trial_rules: dict with inclusion/exclusion rules
    """
    checks = []
    passed_checks = 0
    total_checks = 0
    
    # Age Check
    if 'min_age' in trial_rules or 'max_age' in trial_rules:
        total_checks += 1
        age = patient_data.get('age', 0)
        passed, msg = check_age_criteria(
            age,
            trial_rules.get('min_age'),
            trial_rules.get('max_age')
        )
        checks.append({"check": "Age", "passed": passed, "message": msg})
        if passed:
            passed_checks += 1
    
    # Gender Check
    if 'required_gender' in trial_rules:
        total_checks += 1
        passed, msg = check_gender_criteria(
            patient_data.get('gender', ''),
            trial_rules.get('required_gender')
        )
        checks.append({"check": "Gender", "passed": passed, "message": msg})
        if passed:
            passed_checks += 1
    
    # Inclusion Diagnosis Check
    if 'inclusion_keywords' in trial_rules:
        total_checks += 1
        passed, msg = check_diagnosis_inclusion(
            patient_data.get('diagnosis', ''),
            trial_rules.get('inclusion_keywords', [])
        )
        checks.append({"check": "Inclusion Criteria", "passed": passed, "message": msg})
        if passed:
            passed_checks += 1
    
    # Exclusion Diagnosis Check
    if 'exclusion_keywords' in trial_rules:
        total_checks += 1
        passed, msg = check_diagnosis_exclusion(
            patient_data.get('diagnosis', ''),
            trial_rules.get('exclusion_keywords', [])
        )
        checks.append({"check": "Exclusion Criteria", "passed": passed, "message": msg})
        if passed:
            passed_checks += 1
    
    # Calculate score
    score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    return {
        "score": round(score, 2),
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "checks": checks,
        "eligible": score >= 75  # Eligible if >= 75%
    }
