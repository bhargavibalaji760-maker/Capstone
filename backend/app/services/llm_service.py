import os
import json
import re
from typing import Dict, Any
from app.core.config import settings
import ollama


def get_match_reasoning(
    patient_data: Dict[str, Any],
    trial_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Uses local Llama 3 via Ollama to generate clinician-level explainable reasoning.
    STRICT, NON-HALLUCINATING, JSON-ONLY output.
    """

    # Defensive normalization
    inclusion = trial_data.get("inclusion_criteria") or trial_data.get("inclusion") or ""
    exclusion = trial_data.get("exclusion_criteria") or trial_data.get("exclusion") or ""
    condition = trial_data.get("condition") or "Not specified"

    prompt = f"""
You are a clinical trial eligibility auditor.

TASK:
Evaluate the patient ONLY against the provided trial criteria.

STRICT RULES:
- Do NOT invent eligibility rules.
- Do NOT generalize.
- Do NOT assume missing data implies eligibility.
- If evidence is insufficient, state it clearly.
- Base reasoning ONLY on provided text.

TRIAL CONDITION:
{condition}

INCLUSION CRITERIA:
{inclusion}

EXCLUSION CRITERIA:
{exclusion}

PATIENT DATA:
Age: {patient_data.get('age')}
Gender: {patient_data.get('gender')}
Diagnoses / History: {patient_data.get('medical_history') or patient_data.get('diagnoses')}
Current Treatments: {patient_data.get('treatments') or patient_data.get('medications')}

OUTPUT:
Return ONLY valid JSON in the following schema:

{{
  "eligibility_decision": "Eligible | Ineligible | Uncertain",
  "eligibility_score_boost": number, 
  "hard_exclusion_triggered": boolean,
  "triggered_rules": [string],
  "clinical_reasoning": string,
  "confidence": "Low | Medium | High"
}}

SCORING RULES:
- Eligible → score between +5 and +20
- Ineligible → score between -20 and -5
- Uncertain → score between -3 and +3
"""

    try:
        client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        response = client.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}],
            format="json"
        )

        raw = response.get("message", {}).get("content", "{}")
        data = json.loads(raw)

        return {
            "decision": data.get("eligibility_decision", "Uncertain"),
            "score_boost": float(data.get("eligibility_score_boost", 0.0)),
            "hard_exclusion": bool(data.get("hard_exclusion_triggered", False)),
            "rules": data.get("triggered_rules", []),
            "reasoning": data.get(
                "clinical_reasoning",
                "Eligibility assessed using available protocol criteria."
            ),
            "confidence": data.get("confidence", "Medium")
        }

    except Exception as e:
        # SAFE FALLBACK — NEVER HALLUCINATE
        return {
            "decision": "Uncertain",
            "score_boost": 0.0,
            "hard_exclusion": False,
            "rules": [],
            "reasoning": (
                "[Rules Engine Fallback] "
                "AI reasoning unavailable. Eligibility retained based on "
                "baseline semantic matching only."
            ),
            "confidence": "Low"
        }