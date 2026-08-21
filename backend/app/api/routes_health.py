import os
import platform
from datetime import datetime, timezone
from fastapi import APIRouter

from backend.app.config import settings
from backend.app.models.schemas import HealthResponse
from backend.app.rag.vector_store import vector_store
from backend.app.rag.llm_client import llm_client

router = APIRouter(tags=["System Health"])

@router.get("/health", response_model=HealthResponse, summary="Service Health Check")
async def health_check():
    """Returns sovereign operational health status."""
    try:
        count = vector_store.collection.count()
        db_status = "ONLINE"
    except Exception as e:
        count = 0
        db_status = f"ERROR: {e}"

    llm_status = "READY (Ollama Connected)" if llm_client.is_available() else "READY (Local Deterministic Inference)"

    return HealthResponse(
        status="HEALTHY",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        chroma_db_status=db_status,
        llm_status=llm_status,
        doc_count=count
    )

@router.get("/api/v1/system", summary="System Diagnostics & Telemetry")
async def system_diagnostics():
    """Returns detailed sovereign system telemetry for diagnostics tab."""
    import torch
    
    cuda_avail = torch.cuda.is_available() if "torch" in globals() or hasattr(torch, "cuda") else False
    gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "N/A (CPU Mode)"
    
    return {
        "sovereign_mode": "AIR-GAPPED / ON-PREMISE",
        "cloud_dependencies": "NONE",
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "gpu_available": cuda_avail,
        "gpu_device": gpu_name,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "reranker_model": settings.RERANKER_MODEL_NAME,
        "llm_model": settings.OLLAMA_MODEL,
        "determinism": {
            "temperature": settings.TEMPERATURE,
            "top_p": settings.TOP_P,
            "seed": settings.FIXED_SEED
        },
        "gating_thresholds": {
            "similarity_threshold": settings.SIMILARITY_THRESHOLD,
            "rerank_score_threshold": settings.RERANK_SCORE_THRESHOLD
        },
        "silence_response_text": settings.SILENCE_RESPONSE
    }
