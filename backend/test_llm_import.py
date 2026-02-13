import sys
import os

# Add current directory to path so app can be imported
sys.path.append(os.getcwd())

try:
    from app.services.nlp import llm_service
    print("SUCCESS: llm_service imported correctly")
    
    # Test getting LLM (will fail if no token, but should at least import)
    llm = llm_service.get_llm()
    print("SUCCESS: get_llm function executed")
except Exception as e:
    print(f"FAILURE: llm_service import test failed - {e}")
    import traceback
    traceback.print_exc()
