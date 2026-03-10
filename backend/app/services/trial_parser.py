# app/services/trial_parser.py

import json
import asyncio
import ollama
import re
from app.core.config import settings

async def parse_trial_with_llama(inclusion: str, exclusion: str = ""):
    """
    Asynchronously parses clinical trial sections using a Clinical Auditor persona.
    Can accept combined context or separate sections.
    """
    
    inclusion_text = inclusion
    exclusion_text = exclusion
    
    # Handle cases where exclusion might be empty but inclusion contains both
    if not exclusion and "EXCLUSION:" in inclusion:
        parts = inclusion.split("EXCLUSION:")
        inclusion_text = parts[0].replace("INCLUSION:", "").strip()
        exclusion_text = parts[1].strip()

    loop = asyncio.get_event_loop()

    async def run_ollama():
        messages = [
            {"role": "system", "content": """
Clinical Trial Protocol Parser: Extract specific medical meta-data into a flat JSON object.

RULES:
1. INCLUSION/EXCLUSION: Extract ONLY the **Top 8** most critical medical points. Use short phrases (Max 8 words per point). e.g., "Active Ulcerative Colitis ≥ 3 months", "Age 18-80", "No prior colectomy". 
2. NO SENTENCES: Do NOT extract full sentences, legal boilerplate, or conversational filler.
3. MIN/MAX AGE: Extract as integers (e.g., 18).
4. GENDER: Must be "Male", "Female", or "All".
5. DRUG NAME: The primary study drug molecule name.
6. CONDITION: The primary disease state being studied.

SCHEMA:
{
 "inclusion_criteria": ["str"],
 "exclusion_criteria": ["str"],
 "min_age": int | null,
 "max_age": int | null,
 "gender": "str",
 "drug_name": "str",
 "drug_description": "str",
 "target_condition": "str"
}"""},
            {"role": "user", "content": f"Extract the Top 8 high-utility criteria points from these sections:\n\nINCLUSION:\n{inclusion_text[:1500]}\n\nEXCLUSION:\n{exclusion_text[:1500]}"}
        ]

        client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)
        return await client.chat(
            model="llama3",
            messages=messages,
            format="json",
            options={
                "num_predict": 384,
                "temperature": 0.1
            }
        )

    try:
        response = await run_ollama()
        raw = response["message"]["content"]
        
        print("\n🧠 RAW LLAMA AUDITOR RESPONSE:\n", raw)
        
        # Safe JSON parse
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            raise ValueError("No valid JSON block found in Llama response")
            
        parsed = json.loads(match.group())
        
        return {
            "inclusion_criteria": parsed.get("inclusion_criteria", []),
            "exclusion_criteria": parsed.get("exclusion_criteria", []),
            "min_age": parsed.get("min_age"),
            "max_age": parsed.get("max_age"),
            "gender": parsed.get("gender", "All"),
            "drug_name": parsed.get("drug_name", "Unknown"),
            "drug_description": parsed.get("drug_description", ""),
            "target_condition": parsed.get("target_condition", "Unknown")
        }

    except Exception as e:
        print(f"❌ Llama Auditor failure: {e}")
        # Return raw text as fallback — upstream will use raw extraction text
        return {
            "drug_name": "Unknown",
            "drug_description": "",
            "target_condition": "Unknown",
            "inclusion_criteria": [],
            "exclusion_criteria": [],
            "min_age": 18,
            "max_age": 80,
            "gender": "All"
        }