# app/services/pdf_service.py

from pypdf import PdfReader
import re
import logging

logger = logging.getLogger(__name__)

from concurrent.futures import ThreadPoolExecutor

def extract_text(path, maxpages=None):
    """Actual extraction using pypdf with parallel page processing."""
    try:
        reader = PdfReader(path)
        pages = reader.pages
        if maxpages:
            pages = pages[:maxpages]
        
        def extract_page(page_idx):
            try:
                page = reader.pages[page_idx]
                return page.extract_text() or ""
            except:
                return ""

        with ThreadPoolExecutor(max_workers=4) as executor:
            contents = list(executor.map(extract_page, range(len(pages))))
            
        return "\n".join(contents)
    except Exception as e:
        logger.error(f"pypdf extraction failed for {path}: {e}")
        return ""

class SmartSectionScanner:
    # Patterns that look like section headers (start of line or preceded by newlines)
    HEADER_PATTERNS = [
        r"(?m)^[\s\d.]*(?:Inclusion(?:\s*/\s*Exclusion)?\s*Criteria|Eligibility\s*Criteria|Subject\s*Selection|Selection\s*of\s*Subjects|Participant\s*Eligibility)",
        r"(?i)\n[\s\d.]*(?:Inclusion(?:\s*/\s*Exclusion)?\s*Criteria|Eligibility\s*Criteria|Subject\s*Selection|Selection\s*of\s*Subjects|Participant\s*Eligibility)",
    ]

    def extract(self, pdf_path: str):
        try:
            # Extract first 60 pages
            text = extract_text(pdf_path, maxpages=60)
            text_len = len(text)
            print(f"[DEBUG] PDF chars (first 60pgs): {text_len}")

            if text_len < 100:
                print(f"[WARN] Very little text extracted from {pdf_path}. Might be a scanned image.")

            # Skip common front matter more aggressively if the doc is long
            # TOCs and covers can be long. We'll search for headers after character 4000.
            start_search = min(4000, text_len // 4)
            scan_text = text[start_search:] if text_len > 10000 else text

            best_match = None
            best_start = -1

            for pattern in self.HEADER_PATTERNS:
                # Find all matches for this pattern
                matches = list(re.finditer(pattern, scan_text, re.IGNORECASE))
                for match in matches:
                    start = match.start()
                    # Grab a small snippet to verify it's not a TOC entry (dots or ellipses)
                    snippet = scan_text[start:start+120]
                    if re.search(r"\.\s*\.\s*\.", snippet) or re.search(r"_{3,}", snippet):
                        continue # Skip TOC/Boilerplate

                    # This looks like a real header. Capture a large window.
                    window = scan_text[start:start + 25000] # Use a larger window
                    if len(window) > 800:
                        best_match = window[:20000]
                        print(f"[DEBUG] SmartScanner found header: {match.group().strip()}")
                        return best_match

            # --- Fuzzy fallback (Keyword search) ---
            if not best_match:
                print("[WARN] SmartScanner fallback to keyword window")
                keyword_match = re.search(
                    r"(inclusion|exclusion|eligibility).{200,15000}",
                    scan_text,
                    re.IGNORECASE | re.S
                )
                if keyword_match:
                    idx = keyword_match.start()
                    best_match = scan_text[idx:idx + 15000]
            
            return best_match if best_match else text[:12000]
        except Exception as e:
            print(f"[ERROR] SmartScanner failed: {e}")
            return ""

class PDFExtractionService:
    def extract_raw_text(self, path: str) -> str:
        return extract_text(path)

    def clean_boilerplate(self, text: str) -> str:
        """Strips common instructional boilerplate from clinical protocol templates."""
        boilerplate_patterns = [
            r"(?i)The eligibility criteria should provide a definition of participant characteristics.*?\n",
            r"(?i)Inclusion criteria are characteristics that (?:the prospective subjects must have|define the population).*?\n",
            r"(?i)Exclusion criteria are characteristics that make an individual ineligible.*?\n",
            r"(?i)Provide a statement that (?:all )?individuals meeting any of the exclusion criteria.*?\n",
            r"(?i)List each criterion sequentially.*?\n",
            r"(?i)If specific populations are excluded.*?\n",
            r"(?i)Specific populations to be excluded.*?\n",
            r"(?i)Examples include.*?[\.\n]",
            r"(?i)Instructions for the investigator.*?\n",
            r"(?i)Enter the criteria in the following format.*?\n",
            r"(?i)Some criteria to consider for (?:inclusion|exclusion) are:.*?\n",
            r"(?i)Women and members of minority groups must be included in accordance with.*?[\.\n]",
            r"(?i)Additional criteria should be included as appropriate.*?\n",
            r"(?i)Include a statement regarding equitable selection.*?[\.\n]",
            # Aggressive Footer/Header Stripping
            r"(?im)^Protocol\s*<#>\s*.*$",
            r"(?im)^NIH-FDA\s*.*$",
            r"(?im)^DD\s*Month\s*YYYY\s*.*$",
            r"(?i)Date:\s*\d{1,2}\s*\w+\s*\d{4}.*?$",
            r"(?i)Ver\.\s*\d+\.\d+.*?$",
            r"(?i)Supersedes:.*?$",
            r"(?i)Page\s*\d+\s*of\s*\d+.*?$",
            r"(?i)Protocol\s*No\.:.*?$",
            r"(?i)Solution\s*for\s*Injection.*?$",
            r"(?i)Clinical\s*Trial\s*Protocol.*?$",
            r"(?i)Leading\s*Biopharm\s*Limited.*?$",
            r"(?im)^.*?CONFIDENTIAL\s*$",
            r"(?i)Describe (?:\w+ )+if applicable, otherwise note as not-applicable\.?\n",
            r"(?i)Provide a statement that all individuals meeting any of the exclusion criteria.*?\n",
            r"(?i)Example text provided as a guide, customize as needed.*?[\.\n]",
            r"(?i)Describe what action will be taken if prohibited medications.*?[\.\n]",
            r"(?i)Include content in this section if applicable.*?[\.\n]",
            r"(?i)Identify general strategies for participant recruitment.*?[\.\n]",
            r"(?i)Describe any restrictions during any parts of the study.*?[\.\n]",
            r"(?i)The following subsections should describe the study intervention.*?[\.\n]",
            r"(?i)No text is to be entered in this section.*?[\.\n]",
            r"(?i)pediatric populations, women or minorities\), provide a clear and compelling rationale.*?[\.\n]",
            r"(?i)Limited English proficiency cannot be an exclusion criterion.*?[\.\n]",
            r"(?i)Include content in this section if applicable, otherwise note as not-applicable.*?[\.\n]",
            r"(?i)Describe what action will be taken if prohibited medications.*?[\.\n]",
            r"(?i)Participants who are consented to participate in the clinical trial, who do not meet one or more criteria.*?[\.\n]",
            r"(?i)Indicate how screen failures will be handled in the trial.*?[\.\n]",
            r"(?i)A minimal set of screen failure information is required to ensure transparent reporting.*?[\.\n]",
            r"(?i)Identify general strategies for participant recruitment and retention.*?[\.\n]",
            r"(?i)This section may refer to a separate detailed recruitment and retention plan.*?[\.\n]",
            r"(?i)Vulnerable participants include, but are not limited to pregnant women.*?[\.\n]",
            r"(?i)Please refer to OHRP guidelines when choosing the study population.*?[\.\n]",
            r"(?i)If participants will be compensated or provided any incentives.*?[\.\n]",
            r"(?i)Describe amount, form and timing of such compensation.*?[\.\n]",
            r"(?i)The study intervention may be a drug.*?intended for administration to humans.*?[\.\n]",
            r"(?i)If multiple study interventions are to be evaluated.*?[\.\n]",
            r"(?i)Product information can usually be obtained from the:.*?[\.\n]",
            r"(?im)^<Protocol Title> Version <x\.x>.*$",
            r"(?i)Excluded from study participation.*?\.\n" # Avoid stripping actual criteria by making it specific to the template text
        ]
        
        cleaned = text
        for pattern in boilerplate_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE)
        
        # Trim leading noise (instructional sentences)
        cleaned = re.sub(r"^(?:Inclusion|Exclusion|Eligibility)\s*Criteria[:\.]?\s*(\n|and|are|should).*?[\.\n]", "", cleaned, flags=re.IGNORECASE | re.S)
        
        # Remove empty lines left by stripping
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()

    def extract_criteria(self, path: str):
        scanner = SmartSectionScanner()
        section = scanner.extract(path)

        # Splitting logic (Inclusion vs Exclusion)
        # Try multiple header patterns covering common PDF formats:
        # - Numbered sections: 4.1, 5.1, 6.1, 7.1 etc.
        # - Plain headers: "Inclusion Criteria", "Eligibility Criteria"
        # - Inline headers (colon after, or on same line as text)
        inc_pattern = r"(?im)^[\s\d.]*(?:\d+\.\d+\s+)?(?:Inclusion(?:\s*/\s*Exclusion)?|Eligibility)\s*Criteria[:\s]*$"
        exc_pattern = r"(?im)^[\s\d.]*(?:\d+\.\d+\s+)?Exclusion\s*Criteria[:\s]*$"
        
        inc_match = re.search(inc_pattern, section)
        if not inc_match:
            # Broader fallback: header anywhere on the line
            inc_match = re.search(r"(?im)^[^\n]*(?:Inclusion|Eligibility)\s*Criteria[:\s]", section)
        if not inc_match:
            # Last resort: just find the word
            inc_match = re.search(r"(?i)Inclusion\s*Criteria", section)

        inc_start = inc_match.end() if inc_match else 0
        
        exc_match = re.search(exc_pattern, section[inc_start:], re.IGNORECASE)
        if not exc_match:
            exc_match = re.search(r"(?im)^[^\n]*Exclusion\s*Criteria[:\s]", section[inc_start:])
        if not exc_match:
            exc_match = re.search(r"(?i)Exclusion\s*Criteria", section[inc_start:])
        
        if inc_match and exc_match:
            exc_start_rel = exc_match.start()
            exc_start_abs = inc_start + exc_start_rel
            inclusion = section[inc_start:exc_start_abs].strip()
            exclusion = section[exc_start_abs + (exc_match.end() - exc_match.start()):].strip()
        else:
            inclusion = section
            exclusion = ""

        # Post-process: Clean boilerplate noise
        inclusion = self.clean_boilerplate(inclusion)
        exclusion = self.clean_boilerplate(exclusion)

        print(f"[DEBUG] Final Splitting -> Inclusion: {len(inclusion)} chars, Exclusion: {len(exclusion)} chars")

        return {
            "inclusion": inclusion[:5000], 
            "exclusion": exclusion[:5000],
            "raw_text": section
        }

pdf_service = PDFExtractionService()

