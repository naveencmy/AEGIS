import abc
import json
import logging
import os
import time
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional
import httpx

from backend.app.config import settings
from backend.app.models.schemas import ProvenanceMetadata, SourceType, ThreatDocumentItem

logger = logging.getLogger("aegis.ingest")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class IngestionError(Exception):
    """Raised when an ingestion source fails after maximum retries."""
    pass

class BaseIngestor(abc.ABC):
    """
    Abstract base class for all AEGIS live threat intelligence ingestors.
    
    Enforces:
    1. Real data ingestion with exponential backoff (3 retries).
    2. Strict provenance metadata.
    3. Resumable checkpointing to disk.
    4. Prohibition of synthetic/sample fallback data.
    """
    source_type: SourceType
    canonical_base_url: str

    def __init__(self, checkpoint_dir: Optional[str] = None):
        self.checkpoint_dir = Path(checkpoint_dir or settings.CHECKPOINT_DIR)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / f"{self.source_type}_checkpoint.json"

    def get_provenance(self, doc_id: str, source_url: str, title: Optional[str] = None, severity: Optional[str] = None, tags: Optional[str] = None) -> ProvenanceMetadata:
        """Constructs standardized provenance metadata."""
        now_utc = datetime.now(timezone.utc).isoformat()
        return ProvenanceMetadata(
            source=self.source_type,
            source_url=source_url,
            fetched_at=now_utc,
            doc_id=doc_id,
            title=title,
            severity=severity,
            tags=tags
        )

    def fetch_with_backoff(self, url: str, params: Optional[dict[str, Any]] = None, headers: Optional[dict[str, str]] = None, timeout: float = 30.0) -> httpx.Response:
        """
        Executes HTTP GET with 3 retries and exponential backoff.
        NEVER returns fake/fallback data. If all retries fail, raises IngestionError to stop the pipeline.
        """
        default_headers = {
            "User-Agent": "AEGIS-Threat-Sentinel/0.1 (Sovereign Security Co-Pilot; On-Premise RAG)",
            "Accept": "application/json"
        }
        if headers:
            default_headers.update(headers)

        last_exception = None
        for attempt in range(1, settings.MAX_INGESTION_RETRIES + 1):
            try:
                logger.info(f"[{self.source_type.upper()}] Fetching {url} (Attempt {attempt}/{settings.MAX_INGESTION_RETRIES})...")
                with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                    resp = client.get(url, params=params, headers=default_headers)
                    resp.raise_for_status()
                    return resp
            except Exception as e:
                last_exception = e
                logger.warning(f"[{self.source_type.upper()}] Attempt {attempt} failed for {url}: {e}")
                if attempt < settings.MAX_INGESTION_RETRIES:
                    backoff = (settings.RETRY_BACKOFF_FACTOR ** attempt) + (random.uniform(0.1, 0.5))
                    logger.info(f"[{self.source_type.upper()}] Sleeping {backoff:.2f}s before retry...")
                    time.sleep(backoff)
        
        error_msg = f"FATAL: Failed to ingest from {url} after {settings.MAX_INGESTION_RETRIES} attempts. Cause: {last_exception}. Halting pipeline."
        logger.error(error_msg)
        raise IngestionError(error_msg)

    def load_checkpoint(self) -> dict[str, Any]:
        """Loads state checkpoint from disk."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not read checkpoint file {self.checkpoint_file}: {e}")
        return {"current_index": 0, "total_records": 0, "last_updated": None}

    def save_checkpoint(self, data: dict[str, Any]):
        """Persists state checkpoint to disk."""
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        try:
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write checkpoint to {self.checkpoint_file}: {e}")

    @abc.abstractmethod
    def ingest(self, limit: Optional[int] = None, resume: bool = True) -> Generator[ThreatDocumentItem, None, None]:
        """Generator yielding ingested ThreatDocumentItems with provenance."""
        pass
