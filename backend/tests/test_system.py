"""
Test Patient and Trial Matching
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.matching import rules_engine
from app.services.nlp import text_processor
from app.utils import data_loader

def test_rules_engine():
    """Test the rules engine with sample data"""
    print("\n" + "="*50)
    print("🧪 Testing Rules Engine")
    print("="*50)
    
    # Sample patient data
    patient = {
        'age': 45,
        'gender': 'M',
        'diagnosis': 'Type 2 Diabetes'
    }
    
    # Trial rules
    trial_rules = {
        'min_age': 18,
        'max_age': 75,
        'required_gender': 'M',
        'inclusion_keywords': ['Diabetes', 'Type 2'],
        'exclusion_keywords': ['Heart Failure', 'Pregnancy']
    }
    
    result = rules_engine.apply_rules(patient, trial_rules)
    
    print(f"\n👤 Patient: {patient}")
    print(f"🏥 Trial Rules: {trial_rules}")
    print(f"\n📊 Results:")
    print(f"  Score: {result['score']}%")
    print(f"  Eligible: {result['eligible']}")
    print(f"  Checks Passed: {result['passed_checks']}/{result['total_checks']}")
    
    print(f"\n📋 Check Details:")
    for check in result['checks']:
        status = "✅" if check['passed'] else "❌"
        print(f"  {status} {check['check']}: {check['message']}")

def test_text_processor():
    """Test the NLP text processor"""
    print("\n" + "="*50)
    print("🧪 Testing NLP Text Processor")
    print("="*50)
    
    protocol_text = """
    Type 2 Diabetes Management Trial
    
    Inclusion Criteria:
    - Age 18 or older
    - Diagnosis: Type 2 Diabetes
    - HbA1c > 7.5%
    
    Exclusion Criteria:
    - Pregnancy
    - History of cardiac failure
    - Severe kidney disease
    """
    
    result = text_processor.parse_protocol(protocol_text)
    
    print(f"\n📄 Protocol Text: {protocol_text[:100]}...")
    print(f"\n📊 Extracted Information:")
    print(f"  Inclusion Keywords: {result.get('inclusion_keywords', [])}")
    print(f"  Exclusion Keywords: {result.get('exclusion_keywords', [])}")
    print(f"  Age Range: {result.get('min_age', 'N/A')}-{result.get('max_age', 'N/A')}")

def test_data_loader():
    """Test the data loader with real CSV data"""
    print("\n" + "="*50)
    print("🧪 Testing Data Loader with Real Data")
    print("="*50)
    
    # Load patient demographics
    patients = data_loader.load_patient_demographics()
    print(f"\n📊 Loaded {len(patients)} patient records")
    print(f"   Columns: {list(patients.columns)}")
    
    # Load treatments
    treatments = data_loader.load_patient_treatments()
    print(f"\n💊 Loaded {len(treatments)} treatment records")
    print(f"   Columns: {list(treatments.columns)}")
    
    # Get sample patient
    if len(patients) > 0:
        sample_id = patients.iloc[0]['subject_id']
        patient = data_loader.get_patient_by_id(sample_id)
        print(f"\n👤 Sample Patient (ID: {sample_id}):")
        for key, value in patient.items():
            print(f"   {key}: {value}")
    
    # Test criteria filtering
    print(f"\n🔍 Testing criteria filtering...")
    matching = data_loader.get_conditions_for_trial(['Diabetes'], [])
    print(f"   Found {len(matching)} patients with 'Diabetes' diagnosis")

if __name__ == "__main__":
    try:
        test_data_loader()
        test_text_processor()
        test_rules_engine()
        
        print("\n" + "="*50)
        print("✅ All tests completed successfully!")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
