import asyncio
import logging
import threading
from typing import Optional, Callable
from datetime import datetime, timezone

from backend.app.ingestion.base import IngestionError
from backend.app.ingestion.cisa_kev import CisaKevIngestor
from backend.app.ingestion.mitre_attack import MitreAttackIngestor
from backend.app.ingestion.nvd import NvdIngestor
from backend.app.ingestion.sigma import SigmaIngestor
from backend.app.models.schemas import IngestRequest, IngestStatusResponse, IngestTaskStatus, SourceType
from backend.app.rag.vector_store import vector_store

logger = logging.getLogger("aegis.ingest.pipeline")

class IngestionPipelineManager:
    """
    Coordinates and monitors live threat intelligence ingestion into AEGIS sovereign vector store.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.is_running = False
        self.tasks: dict[str, IngestTaskStatus] = {
            "cisa_kev": IngestTaskStatus(source="cisa_kev", status="idle"),
            "mitre": IngestTaskStatus(source="mitre", status="idle"),
            "nvd": IngestTaskStatus(source="nvd", status="idle"),
            "sigma": IngestTaskStatus(source="sigma", status="idle"),
        }
        self.last_sync_timestamp: Optional[str] = None
        self.ingestors = {
            "cisa_kev": CisaKevIngestor(),
            "mitre": MitreAttackIngestor(),
            "nvd": NvdIngestor(),
            "sigma": SigmaIngestor(),
        }

    def get_status(self) -> IngestStatusResponse:
        """Returns current ingestion tasks status and database stats."""
        stats = vector_store.get_stats()
        return IngestStatusResponse(
            is_running=self.is_running,
            tasks=self.tasks,
            total_docs_in_db=stats["total"],
            db_breakdown=stats["breakdown"],
            last_sync_timestamp=self.last_sync_timestamp
        )

    def run_source_sync(self, source: SourceType, limit: Optional[int] = None, resume: bool = True, batch_size: int = 50) -> int:
        """
        Synchronously runs ingestion for a single source.
        Upserts batches directly into ChromaDB.
        """
        ingestor = self.ingestors.get(source)
        if not ingestor:
            raise ValueError(f"Unknown source: {source}")

        self.tasks[source].status = "running"
        self.tasks[source].last_error = None
        self.tasks[source].records_fetched = 0
        self.tasks[source].records_upserted = 0
        self.tasks[source].last_updated = datetime.now(timezone.utc).isoformat()

        batch = []
        total_upserted = 0
        
        try:
            for doc in ingestor.ingest(limit=limit, resume=resume):
                batch.append(doc)
                self.tasks[source].records_fetched += 1
                
                if len(batch) >= batch_size:
                    upserted = vector_store.upsert_documents(batch)
                    total_upserted += upserted
                    self.tasks[source].records_upserted = total_upserted
                    self.tasks[source].last_updated = datetime.now(timezone.utc).isoformat()
                    batch = []

            # Upsert remainder
            if batch:
                upserted = vector_store.upsert_documents(batch)
                total_upserted += upserted
                self.tasks[source].records_upserted = total_upserted

            self.tasks[source].status = "completed"
            self.tasks[source].last_updated = datetime.now(timezone.utc).isoformat()
            logger.info(f"[{source.upper()}] Ingestion finished successfully. {total_upserted} documents indexed.")
            return total_upserted

        except IngestionError as e:
            self.tasks[source].status = "failed"
            self.tasks[source].last_error = str(e)
            self.tasks[source].last_updated = datetime.now(timezone.utc).isoformat()
            logger.error(f"[{source.upper()}] Ingestion halted due to fatal failure: {e}")
            raise
        except Exception as e:
            self.tasks[source].status = "failed"
            self.tasks[source].last_error = f"Unexpected error: {e}"
            self.tasks[source].last_updated = datetime.now(timezone.utc).isoformat()
            logger.exception(f"[{source.upper()}] Unexpected error during ingestion: {e}")
            raise

    def run_full_pipeline_thread(self, request: IngestRequest):
        """Worker thread function executing sequential ingestion."""
        with self.lock:
            self.is_running = True
        
        try:
            sources_to_run = request.sources or ["cisa_kev", "mitre", "sigma", "nvd"]
            for s in sources_to_run:
                try:
                    logger.info(f"Starting pipeline step: {s}...")
                    self.run_source_sync(
                        source=s,
                        limit=request.limit,
                        resume=request.resume_checkpoint
                    )
                except Exception as e:
                    logger.error(f"Step {s} failed: {e}. Moving to next configured source.")
            
            self.last_sync_timestamp = datetime.now(timezone.utc).isoformat()
        finally:
            with self.lock:
                self.is_running = False
            logger.info("Ingestion pipeline run finished.")

    def trigger_async_pipeline(self, request: IngestRequest) -> bool:
        """Triggers pipeline run in a background thread."""
        with self.lock:
            if self.is_running:
                return False
            self.is_running = True

        thread = threading.Thread(target=self.run_full_pipeline_thread, args=(request,), daemon=True)
        thread.start()
        return True

# Singleton pipeline manager
pipeline_manager = IngestionPipelineManager()
