import logging
import re
from typing import Set, Tuple, Optional
from pydantic import BaseModel

logger = logging.getLogger("aegis.rag.guard")

class GuardResult(BaseModel):
    sanitized_text: str
    ids_checked: int
    ids_verified: int
    unverified_claims_removed: bool
    verified_ids: list[str]
    unverified_ids: list[str]

class HallucinationGuard:
    """
    Sovereign Hallucination Guard.
    Extracts all CVE IDs (CVE-YYYY-NNNNN) and MITRE Technique IDs (T#### or T####.###)
    from generated text, validates them against known verified knowledge base document IDs,
    and strips/replaces any unverified hallucinated entities.
    """
    CVE_PATTERN = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
    MITRE_PATTERN = re.compile(r"\bT\d{4}(?:\.\d{3})?\b", re.IGNORECASE)

    def validate_and_sanitize(self, text: str, context_ids: Set[str], vector_store_lookup = None) -> GuardResult:
        if not text:
            return GuardResult(
                sanitized_text="",
                ids_checked=0,
                ids_verified=0,
                unverified_claims_removed=False,
                verified_ids=[],
                unverified_ids=[]
            )

        # Normalize context IDs to uppercase
        valid_ids = {str(cid).upper() for cid in context_ids if cid}
        
        # Also strip prefixes like 'nvd::' or 'cisa_kev::' or 'mitre::'
        stripped_valid = set()
        for vid in valid_ids:
            stripped_valid.add(vid)
            if "::" in vid:
                stripped_valid.add(vid.split("::")[-1])

        # Extract all entity references from text
        found_cves = self.CVE_PATTERN.findall(text)
        found_mitre = self.MITRE_PATTERN.findall(text)
        all_found = list(dict.fromkeys(found_cves + found_mitre)) # preserve order, unique

        ids_checked = len(all_found)
        verified_ids = []
        unverified_ids = []
        sanitized_text = text
        unverified_removed = False

        for entity_id in all_found:
            clean_id = entity_id.upper()
            is_valid = clean_id in stripped_valid

            # If not in local context, check ChromaDB if vector_store_lookup provided
            if not is_valid and vector_store_lookup:
                try:
                    # Check collections for clean_id
                    for ck in ["cves", "mitre_techniques", "kev", "sigma_rules", "unified"]:
                        col = vector_store_lookup.collections.get(ck)
                        if col:
                            res = col.get(ids=[f"nvd::{clean_id}", f"cisa_kev::{clean_id}", f"mitre::{clean_id}", clean_id])
                            if res and res.get("ids"):
                                is_valid = True
                                stripped_valid.add(clean_id)
                                break
                except Exception:
                    pass

            if is_valid:
                verified_ids.append(clean_id)
            else:
                unverified_ids.append(clean_id)
                unverified_removed = True
                logger.warning(f"[GUARD TRIGGERED] Unverified hallucinated entity detected: {entity_id}")
                
                # Replace unverified claim in text
                replacement = f"[UNVERIFIED CLAIM REMOVED: {clean_id}]"
                pattern = re.compile(re.escape(entity_id), re.IGNORECASE)
                sanitized_text = pattern.sub(replacement, sanitized_text)

        return GuardResult(
            sanitized_text=sanitized_text,
            ids_checked=ids_checked,
            ids_verified=len(verified_ids),
            unverified_claims_removed=unverified_removed,
            verified_ids=verified_ids,
            unverified_ids=unverified_ids
        )

hallucination_guard = HallucinationGuard()
