import json
from typing import Any
from backend.app.config import settings

SYSTEM_PROMPT = """You are AEGIS, a sovereign, citation-native cybersecurity co-pilot.
Your mission is to provide accurate, grounded threat intelligence strictly based on the verified intelligence context provided.

MANDATORY CITATION & FORMATTING CONTRACT:
1. Answer ONLY using the CONTEXT blocks provided below. Each context block is labeled [SOURCE: <source> | ID: <doc_id> | URL: <source_url>].
2. Every factual claim or metric must cite its source ID in brackets (e.g. `[CVE-2024-21626]` or `[T1611]`).
3. Output STRICT JSON conforming to the following schema without markdown formatting or code fences:
{
  "answer": "Grounded intelligence summary citing [DOC_ID]...",
  "cve_ids": ["CVE-YYYY-NNNN"],
  "cvss": {
    "score": 8.6,
    "severity": "HIGH",
    "vector": "CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:H"
  },
  "mitre_techniques": [
    {"id": "T1611", "name": "Escape to Host"}
  ],
  "cisa_kev": {
    "listed": true,
    "date_added": "2024-01-31",
    "due_date": "2024-02-21"
  },
  "insufficient_evidence": false
}
4. If the provided context does not contain enough verified information to answer the query, you MUST output:
{"insufficient_evidence": true, "answer": "Insufficient verified intelligence in the knowledge base", "cve_ids": [], "cvss": {}, "mitre_techniques": [], "cisa_kev": {"listed": false}}
5. NEVER invent or hallucinate CVE IDs, CVSS scores, technique IDs, dates, or URLs.
"""

def build_context_block(documents: list[dict[str, Any]]) -> str:
    blocks = []
    for idx, doc in enumerate(documents, 1):
        meta = doc.get("metadata", {})
        doc_id = meta.get("doc_id") or doc.get("id", f"DOC-{idx}")
        source = meta.get("source") or doc.get("source", "intel")
        url = meta.get("source_url") or doc.get("source_url", "https://nvd.nist.gov")
        content = doc.get("content", "").strip()

        block = f"[SOURCE: {source.upper()} | ID: {doc_id} | URL: {url}]\n{content}\n"
        blocks.append(block)

    return "\n---\n".join(blocks)

def build_prompt(query: str, documents: list[dict[str, Any]]) -> tuple[str, str]:
    context_text = build_context_block(documents)
    user_prompt = f"VERIFIED INTELLIGENCE CONTEXT:\n{context_text}\n\nANALYST QUERY:\n{query}\n\nJSON RESPONSE:"
    return SYSTEM_PROMPT, user_prompt
