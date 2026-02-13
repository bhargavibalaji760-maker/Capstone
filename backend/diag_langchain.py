import importlib.util
import sys

def check_import(module_name):
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            print(f"FOUND: {module_name}")
            return True
        else:
            print(f"NOT FOUND: {module_name}")
            return False
    except Exception as e:
        print(f"ERROR checking {module_name}: {e}")
        return False

print(f"Python version: {sys.version}")
check_import("langchain")
check_import("langchain_core")
check_import("langchain_community")
check_import("langchain_huggingface")

try:
    from langchain.output_parsers import ResponseSchema, StructuredOutputParser
    print("SUCCESS: imported from langchain.output_parsers")
except Exception as e:
    print(f"FAILURE: import from langchain.output_parsers - {e}")

try:
    from langchain_core.output_parsers import ResponseSchema, StructuredOutputParser
    print("SUCCESS: imported from langchain_core.output_parsers")
except Exception as e:
    print(f"FAILURE: import from langchain_core.output_parsers - {e}")

try:
    from langchain_community.output_parsers import ResponseSchema, StructuredOutputParser
    print("SUCCESS: imported from langchain_community.output_parsers")
except Exception as e:
    print(f"FAILURE: import from langchain_community.output_parsers - {e}")

try:
    import langchain
    print(f"Langchain file: {langchain.__file__}")
except Exception as e:
    print(f"Error getting langchain path: {e}")
