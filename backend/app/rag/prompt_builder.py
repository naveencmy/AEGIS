import logging
from typing import Any
from backend.app.config import settings

logger = logging.getLogger("aegis.rag.prompt")

SYSTEM_PROMPT = """You are AEGIS, an authoritative, sovereign on-premise cybersecurity intelligence co-pilot.
Your mission is to provide rigorous, accurate, and citation-grounded analysis of vulnerabilities, threat actor tactics, exploit telemetry, and detection engineering rules.

### NON-NEGOTIABLE OPERATIONAL DIRECTIVES:
1. GROUNDING & CITATION: You may ONLY synthesize answers using the verified intelligence context provided below.
2. CITATION SYNTAX: Whenever you state a technical claim, vulnerability attribute, technique, or detection pattern, immediately cite its Document ID in brackets, e.g., [CVE-2021-44228] or [T1059.001] or [Sigma: Suspicious PowerShell Execution].
3. NO SPECULATION: Do NOT hallucinate CVE identifiers, CVSS metrics, or MITRE ATT&CK techniques not present in the verified context.
4. INSUFFICIENT CONTEXT: If the provided intelligence is insufficient or ambiguous to answer the user's question with 100% factual accuracy, output EXACTLY:
"Insufficient verified intelligence in the knowledge base"
Do not apologize, explain, or attempt to guess.
5. STRUCTURED CYBER ANALYSIS: When intelligence is present, format your analysis crisply with Executive Summary, Technical Impact, Correlated Tactics & Techniques, and Mitigation / Detection Guidance."""

def build_citation_context(documents: list[dict[str, Any]]) -> str:
    """Formats retrieved threat documents into numbered context blocks."""
    if not documents:
        return "NO VERIFIED INTELLIGENCE RETRIEVED."
        
    blocks = []
    for i, doc in enumerate(documents, start=1):
        meta = doc.get("metadata", {})
        doc_id = meta.get("doc_id") or doc.get("doc_id", f"DOC-{i}")
        source = (meta.get("source") or doc.get("source", "unknown")).upper()
        title = meta.get("title") or doc.get("title", doc_id)
        source_url = meta.get("source_url") or doc.get("source_url", "")
        content = doc.get("content", "").strip()
        score = doc.get("relevance_score", doc.get("score", 0.0))
        
        block = (
            f"--- [INTELLIGENCE RECORD {i}: {doc_id}] ---\n"
            f"Entity: {title}\n"
            f"Source: {source} | Canonical URL: {source_url}\n"
            f"Relevance Confidence: {score:.3f}\n"
            f"Intelligence Payload:\n{content}\n"
        )
        blocks.append(block)
        
    return "\n".join(blocks)

def build_rag_prompt(query: str, documents: list[dict[str, Any]]) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for the sovereign LLM.
    """
    context_str = build_citation_context(documents)
    
    user_prompt = f"""VERIFIED CYBER INTELLIGENCE CONTEXT:
{context_str}

USER QUERY:
{query}

Generate an authoritative, grounded analysis answering the user query. Every factual point MUST cite its document ID e.g. [CVE-...] or [T...]."""

    return SYSTEM_PROMPT, user_prompt
