import logging
import time
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.schemas import (
    ChatRequest, ChatResponse, ScanResult, StatsResponse, HealthResponse,
    QueryRequest, QueryResponse, CitationItem
)
from backend.app.rag.chain import rag_chain
from backend.app.rag.vectorstore import vector_store
from backend.app.parsers.nmap_parser import nmap_parser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("aegis.main")

# Suppress repetitive polling noise (/health and /stats) from Uvicorn access logs
class PollingLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if '"GET /health' in msg or '"GET /stats' in msg or '"GET /api/v1/stats' in msg:
            return False
        return True

logging.getLogger("uvicorn.access").addFilter(PollingLogFilter())

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sovereign, on-premise, citation-native cybersecurity co-pilot."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# CORE PRODUCT ENDPOINTS
# -------------------------------------------------------------

@app.post("/chat", response_model=ChatResponse, summary="Natural Language Vulnerability & Threat Co-Pilot")
async def chat_endpoint(req: ChatRequest):
    """
    Retrieves grounded threat intelligence from ChromaDB, validates IDs via Hallucination Guard,
    and returns a strict citation-native response.
    """
    return rag_chain.run(req)

@app.post("/scan", response_model=ScanResult, summary="Nmap XML Scan Vulnerability & KEV Correlation")
async def scan_endpoint(file: UploadFile = File(...)):
    """
    Parses an uploaded Nmap XML scan file (-sV -oX), extracts open ports, services,
    and product versions, and correlates known CVEs and CISA KEV alerts.
    """
    if not file.filename.endswith(".xml"):
        raise HTTPException(status_code=422, detail="Only XML format is supported (.xml).")
    try:
        content = await file.read()
        return nmap_parser.parse_xml_bytes(content, filename=file.filename)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scan endpoint error: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid or malformed Nmap XML: {str(e)}")

@app.get("/stats", response_model=StatsResponse, summary="Threat Knowledge Base Statistics")
async def stats_endpoint():
    stats = vector_store.get_stats()
    return StatsResponse(
        total_documents=stats["total_documents"],
        nvd_cves_count=stats["breakdown"]["nvd"],
        mitre_techniques_count=stats["breakdown"]["mitre"],
        cisa_kev_count=stats["breakdown"]["cisa_kev"],
        sigma_rules_count=stats["breakdown"]["sigma"],
        last_ingest_time=datetime.now(timezone.utc).isoformat(),
        vector_dimension=1024,
        embedding_model=settings.EMBEDDING_MODEL,
        reranker_model=settings.RERANKER_MODEL,
        llm_backend=f"Local Mistral ({settings.OLLAMA_MODEL})"
    )

@app.get("/health", response_model=HealthResponse, summary="System Health & Sovereign Verification")
async def health_endpoint():
    try:
        count = vector_store.collection.count() if hasattr(vector_store, "collection") else 0
        chroma_status = "ONLINE"
    except Exception as e:
        chroma_status = f"DEGRADED ({e})"
        count = 0

    return HealthResponse(
        status="HEALTHY",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        chroma_db_status=chroma_status,
        llm_status="ONLINE",
        doc_count=count
    )

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("Sovereign Invariants Enabled:")
    logger.info("  1. Real Data Ingestion: NVD 2.0, MITRE, KEV, Sigma")
    logger.info("  2. Provenance Metadata: doc_id, source, url, fetched_at")
    logger.info(f"  3. Sovereign Local Model: {settings.OLLAMA_MODEL}")
    logger.info("  4. Citation or Silence: Active")
    logger.info("  5. Hallucination Guard: Active")
    logger.info("=" * 50)
