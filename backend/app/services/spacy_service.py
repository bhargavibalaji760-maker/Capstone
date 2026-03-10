import re
from app.services.nlp_extractor import extractor

class SpacyService:
    @property
    def nlp(self):
        return extractor.nlp

    def extract_bullet_terms(self, text: str) -> list:
        """
        Breaks down a paragraph of criteria into individual clinical terms/bullets.
        """
        if not text:
            return []
            
        # 1. Clean and split by common delimiters
        segments = re.split(r'\n|;|(?<=[.!?])\s+', text)
        
        extracted_terms = []
        # Common non-clinical words to filter out from noun chunks
        filter_words = {"patients", "subjects", "study", "trial", "trials", "participation", 
                        "placebo", "who", "they", "them", "those", "imp", "controlled", 
                        "randomized", "criteria", "inclusion", "exclusion"}
        
        nlp = self.nlp
        for seg in segments:
            clean_seg = seg.strip().strip("•-*")
            if len(clean_seg) < 3:
                continue
                
            if nlp:
                doc = nlp(clean_seg)
                
                # If the segment is a short phrase, keep it
                if len(doc) <= 5:
                    extracted_terms.append(clean_seg.lower())
                
                # Extract noun phrases which usually contain the condition/drug
                for chunk in doc.noun_chunks:
                    words = [t.text.lower() for t in chunk if t.text.lower() not in filter_words and not t.is_stop and not t.is_punct]
                    if words:
                        phrase = " ".join(words)
                        if len(phrase) > 2:
                            extracted_terms.append(phrase)
            else:
                extracted_terms.append(clean_seg.lower())

        return list(set(extracted_terms))

    def fast_extract(self, text: str):
        nlp = self.nlp
        if not nlp:
            return {
                "min_age": None,
                "max_age": None,
                "gender": "All",
                "keywords": []
            }

        doc = nlp(text)

        age_min = None
        age_max = None

        # Age detection: range like 18-65 years
        age_match = re.findall(r'(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\s*years', text.lower())
        if age_match:
            age_min = int(age_match[0][0])
            age_max = int(age_match[0][1])
        else:
            # Single age like >= 18 years
            min_match = re.findall(r'>=\s*(\d{1,2})\s*years', text.lower())
            if min_match:
                age_min = int(min_match[0])

        gender = "All"
        if "male" in text.lower() and "female" not in text.lower():
            gender = "Male"
        elif "female" in text.lower() and "male" not in text.lower():
            gender = "Female"

        # Smarter keyword extraction using entities and bullet parsing
        keywords = self.extract_bullet_terms(text)

        return {
            "min_age": age_min,
            "max_age": age_max,
            "gender": gender,
            "keywords": keywords
        }


spacy_service = SpacyService()
