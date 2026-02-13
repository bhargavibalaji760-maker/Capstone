"""
LLM Service Module - Handle advanced NLP tasks using LangChain and Hugging Face
"""
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.core.config import settings

class PatientInfo(BaseModel):
    name: str = Field(description="Patient full name")
    age: int = Field(description="Patient age")
    gender: str = Field(description="Patient gender (M, F, or U)")
    primary_condition: str = Field(description="Main clinical diagnosis or condition")
    clinical_notes: str = Field(description="Summary of relevant medical history")

def get_llm():
    """Initialize the LLM connection"""
    if not settings.HF_API_TOKEN:
        return None
    
    try:
        return HuggingFaceEndpoint(
            repo_id=settings.DEFAULT_MODEL,
            huggingfacehub_api_token=settings.HF_API_TOKEN,
            task="text-generation",
            max_new_tokens=512,
            temperature=0.1
        )
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        return None

def extract_patient_info(text: str) -> Dict[str, Any]:
    """Use LLM to extract structured patient information from clinical text"""
    llm = get_llm()
    if not llm:
        return None  # Fallback to regex in text_processor

    parser = JsonOutputParser(pydantic_object=PatientInfo)

    prompt = PromptTemplate(
        template="""You are a medical data extraction assistant. 
Extract patient information from the following clinical note text.
If a field is unknown, use 'Unknown' or 0 for age.

Text: {text}

{format_instructions}""",
        input_variables=["text"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    try:
        chain = prompt | llm | parser
        return chain.invoke({"text": text})
    except Exception as e:
        print(f"LLM extraction error: {e}")
        return None

def get_match_explanation(patient_data: Dict[str, Any], trial_data: Dict[str, Any], eligible: bool) -> str:
    """Generate a natural language explanation for the trial matching result"""
    llm = get_llm()
    if not llm:
        return "AI Insight unavailable. Please configure a Hugging Face token."

    status = "ELIGIBLE" if eligible else "INELIGIBLE"
    
    prompt = PromptTemplate(
        template="""You are a clinical recruitment specialist. 
Explain why a patient is {status} for the clinical trial based on the data below.
Be concise and focus on the key matching or conflicting criteria.

Patient Data:
- Age: {age}
- Gender: {gender}
- Condition: {condition}
- Notes: {notes}

Trial Data:
- Title: {trial_title}
- Inclusion: {inclusion}
- Exclusion: {exclusion}

Explanation (max 3 sentences):""",
        input_variables=["status", "age", "gender", "condition", "notes", "trial_title", "inclusion", "exclusion"]
    )

    try:
        input_data = {
            "status": status,
            "age": patient_data.get('age'),
            "gender": patient_data.get('gender'),
            "condition": patient_data.get('primary_condition') or patient_data.get('diagnosis'),
            "notes": patient_data.get('clinical_notes'),
            "trial_title": trial_data.get('title'),
            "inclusion": trial_data.get('inclusion'),
            "exclusion": trial_data.get('exclusion')
        }
        
        # Simple invocation without complex chain if it's just text
        response = llm.invoke(prompt.format(**input_data))
        return response.strip()
    except Exception as e:
        return f"Could not generate AI explanation: {str(e)}"
