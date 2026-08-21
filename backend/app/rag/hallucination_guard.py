import re
import logging
from typing import NamedTuple
from backend.app.rag.vector_store import vector_store

logger = logging.getLogger("aegis.rag.guard")

CVE_REGEX = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
MITRE_REGEX = re.compile(r"\bT\d{4}(?:\.\d{3})?\b", re.IGNORECASE)

class GuardVerificationResult(NamedTuple):
    sanitized_text: str
    verified_ids: list[str]
    hallucinations_detected: list[str]
    unverified_claims_removed: bool

class HallucinationGuard:
    """
    AEGIS Post-Generation Hallucination Validator.
    
    Enforces Invariant 5:
    Extracts every CVE-ID (CVE-\\d{4}-\\d{4,7}) and MITRE technique ID (T\\d{4}(\\.\\d{3})?)
    from the LLM output and verifies each exists in ChromaDB.
    Unknown IDs are stripped and the response is flagged with unverified_claims_removed: true.
    """
    def __init__(self, db=None):
        self.db = db or vector_store

    def validate_and_sanitize(self, response_text: str, cited_doc_ids: set[str]) -> GuardVerificationResult:
        if not response_text:
            return GuardVerificationResult(
                sanitized_text="",
                verified_ids=[],
                hallucinations_detected=[],
                unverified_claims_removed=False
            )

        # 1. Extract all candidate CVEs and MITRE technique IDs
        cves_found = CVE_REGEX.findall(response_text)
        mitre_found = MITRE_REGEX.findall(response_text)
        
        all_candidates = list(dict.fromkeys([c.upper() for c in cves_found] + [m.upper() for m in mitre_found]))
        
        verified_ids = []
        hallucinations_detected = []

        # 2. Check existence in ChromaDB or retrieved context
        for candidate_id in all_candidates:
            # Fast check: was it in the retrieved context?
            is_valid = (candidate_id in cited_doc_ids) or (candidate_id.upper() in cited_doc_ids)
            
            # If not in cited docs, verify against ChromaDB
            if not is_valid:
                is_valid = self.db.doc_exists(candidate_id)
                
            if is_valid:
                verified_ids.append(candidate_id)
            else:
                hallucinations_detected.append(candidate_id)
                logger.warning(f"[HALLUCINATION GUARD] Intercepted unverified entity claim: '{candidate_id}' (not indexed in ChromaDB)")

        # 3. If unverified IDs detected, sanitize response text
        sanitized_text = response_text
        unverified_claims_removed = len(hallucinations_detected) > 0

        for fake_id in hallucinations_detected:
            # Replace occurrences with sanitized warning or remove
            # Pattern matching word boundary for this specific fake ID (case-insensitive)
            pattern = re.compile(re.escape(fake_id), re.IGNORECASE)
            sanitized_text = pattern.sub(f"[UNVERIFIED CLAIM REMOVED: {fake_id}]", sanitized_text)

        if unverified_claims_removed:
            logger.info(f"[HALLUCINATION GUARD] Stripped {len(hallucinations_detected)} hallucinated identifiers from output.")

        return GuardVerificationResult(
            sanitized_text=sanitized_text,
            verified_ids=verified_ids,
            hallucinations_detected=hallucinations_detected,
            unverified_claims_removed=unverified_claims_removed
        )

hallucination_guard = HallucinationGuard()
