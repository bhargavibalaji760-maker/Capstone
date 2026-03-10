# import spacy (moved to lazy loader)
import re
import functools
from typing import Set, Dict

class NLPExtractor:
    _nlp = None
    _profile_cache: Dict[int, str] = {} # patient_id -> normalized_text

    def __init__(self):
        # Lazy load spaCy to avoid overhead during frequent re-initialization
        self.registry = {
            "dm": "diabetes",
            "htn": "hypertension",
            "cad": "coronary artery disease",
            "copd": "chronic obstructive pulmonary disease",
            "ckd": "chronic kidney disease",
            "afib": "atrial fibrillation",
            "uc": "ulcerative colitis",
            "nafld": "non-alcoholic fatty liver disease",
            "ms": "multiple sclerosis"
        }

        keywords = set(self.registry.keys()) | set(self.registry.values())
        # Expand known conditions for matching
        keywords.update([
            "cancer", "stroke", "asthma", "anemia", "sepsis", "obesity", 
            "ulcerative colitis", "colitis", "liver", "cirrhosis", "diabetes", 
            "heart", "lung", "kidney", "renal", "cardiac", "pulmonary"
        ])

        # Clean punctuation from keywords and sort by length for better regex matching
        safe_keywords = [re.escape(k) for k in sorted(keywords, key=len, reverse=True)]
        self.pattern = re.compile(rf"\b({'|'.join(safe_keywords)})\b", re.I)

        # Words spaCy marks as stopwords but are medically significant
        self.medical_stopword_overrides = {
            "multiple", "chronic", "acute", "severe", "moderate", "primary",
            "secondary", "active", "stable", "progressive", "relapsing",
            "advanced", "early", "late", "major", "minor", "general",
            "total", "partial", "complete", "full", "negative", "positive",
        }

    @property
    def nlp(self):
        if NLPExtractor._nlp is None:
            try:
                import spacy
                # Load only what we absolutely need
                NLPExtractor._nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
            except:
                NLPExtractor._nlp = False # Marker for failed load
        return NLPExtractor._nlp if NLPExtractor._nlp is not False else None

    @functools.lru_cache(maxsize=2048)
    def normalize(self, text: str) -> str:
        if not text:
            return ""
        nlp = self.nlp
        if not nlp:
            # Fallback: remove non-alphanumeric (except spaces) and lowercase
            return re.sub(r'[^\w\s]', '', text.lower())

        doc = nlp.make_doc(text.lower())
        return " ".join(
            t.text for t in doc
            if (not t.is_stop or t.text in self.medical_stopword_overrides)
            and not t.is_punct
        )

    def normalize_batch(self, patients: list) -> list:
        """
        Takes a list of Patient objects and returns a list of normalized strings.
        Uses in-memory cache to skip already processed profiles.
        """
        results = [None] * len(patients)
        to_process_indices = []
        to_process_texts = []

        for i, p in enumerate(patients):
            if p.id in self._profile_cache:
                results[i] = self._profile_cache[p.id]
            else:
                raw_text = " ".join(filter(None, [
                    p.medical_history or "",
                    p.diagnoses or "",
                    getattr(p, "conditions", "") or "",
                    getattr(p, "treatments", "") or ""
                ]))
                to_process_indices.append(i)
                to_process_texts.append(raw_text)

        if to_process_texts:
            if not self.nlp:
                batch_results = [re.sub(r'[^\w\s]', '', t.lower()) for t in to_process_texts]
            else:
                batch_results = []
                for doc in self.nlp.pipe(to_process_texts, batch_size=100, disable=["ner", "parser"]):
                    normalized = " ".join(
                        t.text for t in doc
                        if (not t.is_stop or t.text in self.medical_stopword_overrides)
                        and not t.is_punct
                    )
                    batch_results.append(normalized)

            # Update cache and populate final results
            for idx, res in zip(to_process_indices, batch_results):
                self._profile_cache[patients[idx].id] = res
                results[idx] = res

        return results

    def extract_entities(self, text: str) -> Set[str]:
        entities = set()

        for m in self.pattern.findall(text.lower()):
            entities.add(self.registry.get(m, m))

        # We keep this fast keyword-based for scale
        return entities

extractor = NLPExtractor()
