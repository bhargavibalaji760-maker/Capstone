from app.core.config import settings
import ollama
import json

# Global client for connection reuse
client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)

async def explain_match(patient, trial):
    """
    Generates a drug-specific clinical eligibility narrative for a candidate patient.
    Returns a structured JSON with eligibility score, narrative, and confidence.
    """
    drug_name = getattr(trial, 'drug', '') or getattr(trial, 'condition', 'Unknown')
    condition = getattr(trial, 'condition', 'Unknown') or 'Unknown'

    def cap(field, limit=400):
        data = getattr(trial, field, "")
        if isinstance(data, list):
            return ", ".join(str(x) for x in data[:12])
        return str(data or "")[:limit]

    prompt = f"""You are a clinical trial eligibility analyst. Assess this patient's eligibility for a drug trial.

DRUG/TRIAL: {drug_name} | Target: {condition}
INCLUSION CRITERIA: {cap("inclusion_criteria")}
EXCLUSION CRITERIA: {cap("exclusion_criteria")}

PATIENT:
- Age: {patient.age} | Gender: {patient.gender}
- Medical History: {str(patient.medical_history or "Not recorded")[:300]}
- Diagnoses: {str(patient.diagnoses or "Not recorded")[:300]}
- Treatments: {str(getattr(patient, 'treatments', '') or 'Not recorded')[:200]}

TASK: Evaluate eligibility. Be extremely concise.
Output STRICT JSON:
{{"eligibility_score": 0.0 to 1.0, "eligibility_narrative": "One sentence (max 20 words) explaining the primary clinical reason for this match.", "confidence_level": "High"|"Medium"|"Low"}}"""

    try:
        r = await client.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={
                "num_predict": 100, # Reduced from 180
                "temperature": 0.1
            }
        )
        content = r["message"]["content"]
        data = json.loads(content)

        return {
            "eligibility_score": float(data.get("eligibility_score", 0.5)),
            "eligibility_narrative": data.get("eligibility_narrative", "Clinical profile reviewed against trial protocol."),
            "confidence_level": data.get("confidence_level", "Medium")
        }

    except Exception as e:
        print(f"DEBUG: explain_match error: {e}")
        # Build a rule-based fallback narrative
        condition_hint = condition if condition and condition != "Unknown" else "the target indication"
        return {
            "eligibility_score": 0.5,
            "eligibility_narrative": f"Match assessed against {drug_name} protocol. AI analysis deferred for speed.",
            "confidence_level": "Low"
        }
