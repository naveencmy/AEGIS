import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from backend.app.models.schemas import IngestRequest, IngestStatusResponse, SourceType
from backend.app.ingestion.pipeline import pipeline_manager

logger = logging.getLogger("aegis.api.ingest")
router = APIRouter(prefix="/api/v1/ingest", tags=["Ingestion & Pipeline"])

@router.get("/status", response_model=IngestStatusResponse, summary="Get Ingestion Pipeline Status")
async def get_ingest_status():
    """Returns live status of all 4 threat intelligence ingestors and database counts."""
    return pipeline_manager.get_status()

@router.post("/run", summary="Trigger Background Threat Intel Ingestion")
async def trigger_ingestion(req: IngestRequest):
    """
    Triggers asynchronous live ingestion from NVD API 2.0, MITRE ATT&CK STIX 2.1,
    CISA KEV, and SigmaHQ detection rules.
    """
    started = pipeline_manager.trigger_async_pipeline(req)
    if not started:
        raise HTTPException(status_code=409, detail="An ingestion pipeline task is already actively running.")
    return {"message": "Ingestion pipeline launched successfully in background.", "status": "running"}

@router.post("/sync/{source}", summary="Synchronously Sync Single Source")
async def sync_single_source(
    source: SourceType,
    limit: Optional[int] = Query(None, description="Max records to pull"),
    resume: bool = Query(True, description="Resume from disk checkpoint"),
    batch_size: int = Query(50, description="ChromaDB upsert batch size")
):
    """
    Synchronously runs live ingestion for a specific intelligence source with progress reporting.
    """
    try:
        count = pipeline_manager.run_source_sync(source=source, limit=limit, resume=resume, batch_size=batch_size)
        return {
            "source": source,
            "status": "completed",
            "records_upserted": count,
            "message": f"Successfully ingested and indexed {count} records from {source}."
        }
    except Exception as e:
        logger.exception(f"Sync failed for {source}: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed for {source}: {str(e)}")
