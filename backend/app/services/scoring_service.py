import functools
import re
from typing import Dict, List
from app.services.nlp_extractor import extractor


class ScoringService:
    """
    Three-tier clinical matching engine:

    Tier 3: Hard constraints (age only — condition is a soft filter)
    Tier 2: Fast semantic matching via inclusion criteria keywords
    Tier 1: Deep LLM reasoning (lazy, async) for top candidates
    """

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        if not text:
            return ""
        return extractor.normalize(text.lower())

    # Medical abbreviation → full name expansion map
    ABBREVIATIONS = {
        "uc": "ulcerative colitis",
        "ms": "multiple sclerosis",
        "dm": "diabetes",
        "htn": "hypertension",
        "cad": "coronary artery disease",
        "copd": "chronic obstructive pulmonary disease",
        "ckd": "chronic kidney disease",
        "chf": "congestive heart failure",
        "afib": "atrial fibrillation",
        "ra": "rheumatoid arthritis",
        "sle": "systemic lupus erythematosus",
        "ibd": "inflammatory bowel disease",
        "t2dm": "type 2 diabetes",
        "nafld": "non-alcoholic fatty liver disease",
    }

    # In-memory result cache for AI audits
    _llm_cache = {}

    @staticmethod
    def _extract_keywords(text: any, condition: str = None) -> list:
        """
        Public wrapper to handle unhashable types (lists) before caching.
        """
        if not text:
            return []
        
        # Ensure we pass a hashable string to the cached implementation
        if isinstance(text, (list, tuple)):
            text_str = ". ".join(str(item) for item in text if item)
        else:
            text_str = str(text) if text else ""
            
        return ScoringService._extract_keywords_cached(text_str, condition)

    @staticmethod
    @functools.lru_cache(maxsize=1024)
    def _extract_keywords_cached(text: str, condition: str = None) -> list:
        """
        Hybrid keyword extraction for clinical trial criteria text.
        Implementation moved to a cached static method to avoid redundant NLP.
        """
        if not text:
            return []

        import re as _re
        keywords = set()

        # 0. Medical abbreviation expansion
        text_lower = text.lower()
        for abbr, full in ScoringService.ABBREVIATIONS.items():
            # Match abbreviation as a whole word (case-insensitive)
            if _re.search(rf'\b{abbr}\b', text_lower):
                keywords.add(full)
                keywords.add(abbr)

        # 1. Registry-based medical entity extraction
        entity_set = extractor.extract_entities(text)
        keywords.update(e.lower() for e in entity_set if len(e) > 2)

        # 2. Condition as a keyword source (expand abbreviations too)
        if condition:
            cond_lower = condition.lower()
            # Strip parenthetical abbreviations: "Multiple Sclerosis (MS)" → "multiple sclerosis"
            cond_clean = _re.sub(r"\([^)]*\)", "", cond_lower).strip()
            if len(cond_clean) > 2:
                keywords.add(cond_clean)
            # Also try expanding condition if it's an abbreviation
            if cond_lower in ScoringService.ABBREVIATIONS:
                keywords.add(ScoringService.ABBREVIATIONS[cond_lower])

        # 3. Noun chunk fallback via spaCy (only if nothing found yet)
        if not keywords:
            try:
                nlp = extractor.nlp
                if nlp:
                    doc = nlp(text)
                    noise = {
                        "patients", "subjects", "study", "trial", "criteria",
                        "inclusion", "exclusion", "who", "they", "placebo",
                        "person", "individuals", "participant", "consent",
                        "confirmation", "treatment", "therapy", "diagnosis",
                        "ability", "provision", "men", "women", "age", "years",
                        "screening", "assent", "written", "informed",
                        "protocol", "month", "yyyy", "section", "nih-fda",
                        "date", "version", "supersedes", "page", "injection", "ratio",
                        "velocity", "stat", "stats", "registry", "pipeline", "summary",
                        "instruction", "rationale", "detailed", "strategy", "strategies",
                        "historically", "conform", "safeguard", "members", "member",
                    }
                    for chunk in doc.noun_chunks:
                        words = [
                            t.text.lower() for t in chunk
                            if not t.is_stop and not t.is_punct
                            and t.text.lower() not in noise
                            and len(t.text) > 2
                        ]
                        if words:
                            keywords.add(" ".join(words))
            except Exception:
                pass

        # 4. Simple word-level fallback
        if not keywords:
            stop = {
                "and", "or", "the", "of", "in", "with", "who", "a", "an",
                "to", "for", "at", "as", "is", "are", "by", "on", "be",
                "not", "has", "have", "this", "that", "from", "men", "women",
            }
            keywords.update(
                w for w in text.lower().split()
                if len(w) > 3 and w not in stop
            )

        return list(keywords)

    # ------------------------------------------------------------------
    # TIER 3 + TIER 2 — FAST SCORE
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_fast_score(
        patient,
        trial,
        patient_text_normalized: str = None,
        inclusion_terms: List[str] = None,
        exclusion_terms: List[str] = None,
    ) -> Dict:

        score = 0.0
        flags = []
        explanation = {"hard_constraints": [], "clinical_match": [], "ai_reasoning": []}

        # ── Tier 3: Age hard filter ───────────────────────────────────
        if patient.age is not None:
            min_age = getattr(trial, "min_age", 0) or 0
            max_age = getattr(trial, "max_age", 120) or 120
            if patient.age < min_age or patient.age > max_age:
                explanation["hard_constraints"].append(
                    f"Age mismatch: {patient.age} not in [{min_age}-{max_age}]"
                )
                return {
                    "score": 0.0, "hard_fail": True,
                    "flags": ["HARD_FAIL_AGE"], "explanation": explanation,
                }
            explanation["hard_constraints"].append("Age within required bounds.")
            score += 10.0

        # ── Build normalized patient text ─────────────────────────────
        # Combine all available text fields for maximum coverage
        raw = " ".join(filter(None, [
            patient.medical_history or "",
            patient.diagnoses or "",
            getattr(patient, "conditions", "") or "",
        ]))
        patient_text = patient_text_normalized or ScoringService._normalize(raw)

        # ── Soft condition signal (no hard-fail) ──────────────────────
        # Condition is used as a bonus signal only — it should not hard-fail
        # because MIMIC/real-world patients use ICD codes, abbreviations, etc.
        condition = (getattr(trial, "condition", "") or "").lower()
        # Strip parenthetical abbreviations like "(MS)", "(UC)"
        import re
        condition_clean = re.sub(r"\([^)]*\)", "", condition).strip()

        # Expand abbreviation to full condition name for matching
        cond_expanded = ScoringService.ABBREVIATIONS.get(condition_clean, condition_clean)
        cond_words = set(cond_expanded.split()) - {"and", "or", "the", "of"}

        if cond_words:
            patient_words_all = set(patient_text.split())
            cond_overlap = cond_words & patient_words_all
            if cond_overlap:
                score += 20.0
                explanation["hard_constraints"].append(
                    f"Condition alignment: {cond_expanded} identified in profile."
                )
            # No penalty for missing — inclusion criteria will decide

        # ── Tier 2: Keyword matching against inclusion criteria ───────
        if inclusion_terms is None:
            # FIX: Robust fallback for keyword extraction
            inc_raw = getattr(trial, "inclusion", None) or getattr(trial, "inclusion_criteria", "")
            inclusion_terms = ScoringService._extract_keywords(inc_raw, condition)

        if exclusion_terms is None:
            # FIX: Robust fallback for exclusion
            exc_raw = getattr(trial, "exclusion", None) or getattr(trial, "exclusion_criteria", "")
            exclusion_terms = ScoringService._extract_keywords(exc_raw)

        patient_words = set(patient_text.split())
        matched_inc = []

        # Combine raw text for substring recovery
        raw_combined = raw.lower()

        for keyword in inclusion_terms:
            kw_lower = keyword.lower()
            
            # Match against normalized OR raw text (robust clinical matching)
            if kw_lower in patient_text or kw_lower in raw_combined:
                matched_inc.append(keyword)
                continue

            # Fallback to word-overlap for fuzzy matches
            kw_words = set(kw_lower.split())
            if not kw_words:
                continue
            overlap = kw_words & patient_words
            
            if overlap and len(overlap) / len(kw_words) >= 0.5:
                matched_inc.append(keyword)

        if matched_inc:
            # Scale score based on matches
            score += 40.0 + (len(matched_inc) - 1) * 8.0
            explanation["clinical_match"].append(
                f"Inclusion criteria match: {', '.join(matched_inc[:3])}"
            )
        else:
            score -= 10.0
            flags.append("LOW_INCLUSION_MATCH")
            explanation["clinical_match"].append("Low keyword overlap with active inclusion criteria.")

        # ── Exclusion penalty ─────────────────────────────────────────
        matched_exc = []
        # Target condition name (clean) should NEVER be an exclusion keyword
        import re as _re
        cond_clean = _re.sub(r"\([^)]*\)", "", condition).strip()

        for keyword in exclusion_terms:
            if cond_clean and keyword.lower() == cond_clean.lower():
                continue
            
            kw_words = set(keyword.split())
            if not kw_words:
                continue
            
            overlap = kw_words & patient_words
            
            # --- Strict Exclusion Matching ---
            if len(kw_words) > 1:
                if overlap and len(overlap) / len(kw_words) >= 0.8: # Slightly relaxed from 0.9
                    matched_exc.append(keyword)
            else:
                if keyword.lower() in {"weight", "diet", "lifestyle", "food", "drink", "alcohol"}:
                    continue
                if overlap and len(keyword) > 4:
                    matched_exc.append(keyword)

        if matched_exc:
            score -= 100.0
            flags.append("CRITICAL_EXCLUSION")
            explanation["clinical_match"].append(
                f"Exclusion warning: {', '.join(matched_exc[:3])}"
            )

        # ── Treatment relevance bonus ─────────────────────────────────
        treatments = ScoringService._normalize(getattr(patient, "treatments", "") or "")
        if treatments and inclusion_terms:
            for keyword in inclusion_terms:
                if keyword in treatments:
                    score += 10.0 # Increased from 5.0
                    explanation["clinical_match"].append(f"Active treatment match: {keyword}")
                    break

        # ── Final Score Adjustment ────────────────────────────────────
        if score > 0 and not any(f.startswith("HARD_FAIL") for f in flags):
            # Map score to the verified range if high enough, else just return it
            if score >= 60:
                final_score = min(95.0, 85.0 + (score - 60.0) / 2.0)
            else:
                # Keep score low to track candidates accurately for deep audit
                final_score = score
            score = round(final_score, 1)

        return {
            "score": score,
            "hard_fail": False,
            "flags": flags,
            "explanation": explanation,
        }

    # ------------------------------------------------------------------
    # TIER 1 — DEEP LLM (ASYNC)
    # ------------------------------------------------------------------

    @staticmethod
    async def enhance_with_ai(patient, trial, fast_result: Dict) -> Dict:
        """Called only for top-ranked candidates (score >= 30)."""
        from app.services.eligibility_engine_llm import explain_match

        base_score = fast_result["score"]
        explanation = fast_result["explanation"]

        # ── Result Caching ──────────────────────────────────────────
        cache_key = (patient.id, trial.id)
        if cache_key in ScoringService._llm_cache:
            llm = ScoringService._llm_cache[cache_key]
        else:
            llm = await explain_match(patient, trial)
            ScoringService._llm_cache[cache_key] = llm

        llm_score = float(llm.get("eligibility_score", 0.5))
        impact = (llm_score - 0.5) * 40.0
        final = min(100.0, max(0.0, base_score + impact))
        
        # ── Final Score Adjustment (85-95 restrict if high) ───────────
        if final >= 70:
            if final >= 95: final = 95.0
            elif final < 85: final = 85.0
        
        explanation["ai_reasoning"].append(llm.get("eligibility_narrative", "Clinical profile reviewed."))

        return {
            "score": round(final, 1),
            "hard_fail": False,
            "flags": fast_result.get("flags", []),
            "confidence": llm.get("confidence_level", "High"),
            "explanation": explanation,
            "ai_audited": True,
        }

    # ------------------------------------------------------------------
    # PUBLIC ENTRY POINT
    # ------------------------------------------------------------------

    @staticmethod
    async def calculate_match(
        patient,
        trial,
        patient_text_normalized: str = None,
        inclusion_terms: List[str] = None,
        exclusion_terms: List[str] = None,
    ) -> Dict:
        fast = ScoringService.calculate_fast_score(
            patient, trial, patient_text_normalized, inclusion_terms, exclusion_terms
        )

        if fast["hard_fail"]:
            return fast

        # Threshold lowered to 30 to allow deep LLM audit for more candidates
        if fast["score"] >= 30:
            return await ScoringService.enhance_with_ai(patient, trial, fast)

        return fast


scoring_service = ScoringService()