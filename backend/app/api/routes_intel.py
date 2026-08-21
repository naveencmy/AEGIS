import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.config import settings
from backend.app.models.schemas import KnowledgeBaseStats, ThreatDocumentItem, SourceType
from backend.app.rag.vector_store import vector_store
from backend.app.ingestion.pipeline import pipeline_manager

logger = logging.getLogger("aegis.api.intel")
router = APIRouter(prefix="/api/v1", tags=["Intelligence & Knowledge Base"])

@router.get("/stats", response_model=KnowledgeBaseStats, summary="Knowledge Base Statistics")
async def get_stats():
    """Returns total documents indexed, breakdown by threat intelligence source, and model parameters."""
    counts = vector_store.get_stats()
    breakdown = counts.get("breakdown", {})
    return KnowledgeBaseStats(
        total_documents=counts.get("total", 0),
        nvd_cves_count=breakdown.get("nvd", 0),
        mitre_techniques_count=breakdown.get("mitre", 0),
        cisa_kev_count=breakdown.get("cisa_kev", 0),
        sigma_rules_count=breakdown.get("sigma", 0),
        last_ingestion_time=pipeline_manager.last_sync_timestamp,
        vector_dimension=1024,
        embedding_model=settings.EMBEDDING_MODEL_NAME,
        reranker_model=settings.RERANKER_MODEL_NAME,
        llm_backend=f"Mistral 7B Q4 via {settings.OLLAMA_MODEL}"
    )

@router.get("/intel/search", summary="Search and Browse Threat Documents")
async def search_intel(
    query: Optional[str] = Query(None, description="Search query or keyword"),
    source: Optional[SourceType] = Query(None, description="Filter by source"),
    limit: int = Query(50, le=200, description="Max documents to return")
):
    """Searches indexed threat intelligence documents for Threat Explorer UI."""
    return vector_store.list_threat_intel(query_str=query, source=source, limit=limit)

@router.get("/intel/cve/{cve_id}", summary="Lookup CVE Record")
async def get_cve_details(cve_id: str):
    """Retrieves full provenance and payload for a specific CVE."""
    doc = vector_store.get_document(cve_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"CVE record '{cve_id}' not found in ChromaDB.")
    return doc

@router.get("/intel/mitre/{tech_id}", summary="Lookup MITRE Technique")
async def get_mitre_details(tech_id: str):
    """Retrieves full provenance and payload for a specific MITRE ATT&CK technique."""
    doc = vector_store.get_document(tech_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"MITRE ATT&CK technique '{tech_id}' not found in ChromaDB.")
    return doc
