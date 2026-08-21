import argparse
import logging
import sys
from pathlib import Path

# Ensure backend root is on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.app.config import settings
from backend.app.rag.vectorstore import vector_store
from backend.app.ingestion.nvd_ingest import nvd_ingestor
from backend.app.ingestion.mitre_ingest import mitre_ingestor
from backend.app.ingestion.cisa_kev import cisa_kev_ingestor
from backend.app.ingestion.sigma_ingest import sigma_ingestor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("aegis.ingest.cli")

INGESTORS = {
    "nvd": (nvd_ingestor, "nvd"),
    "mitre": (mitre_ingestor, "mitre"),
    "kev": (cisa_kev_ingestor, "cisa_kev"),
    "cisa_kev": (cisa_kev_ingestor, "cisa_kev"),
    "sigma": (sigma_ingestor, "sigma")
}

def run_source(source_key: str, limit: int = None, resume: bool = True):
    if source_key not in INGESTORS:
        logger.error(f"Unknown source: '{source_key}'. Available: {list(INGESTORS.keys())}")
        return 0

    ingestor, target_source = INGESTORS[source_key]
    logger.info(f"=== Starting Ingestion: Source={source_key} (Limit={limit}, Resume={resume}) ===")

    batch = []
    total_ingested = 0
    batch_size = 50

    try:
        for doc in ingestor.ingest(limit=limit, resume=resume):
            batch.append(doc)
            if len(batch) >= batch_size:
                vector_store.upsert_documents(batch, source=target_source)
                total_ingested += len(batch)
                logger.info(f"[{source_key.upper()}] Upserted batch. Total ingested so far: {total_ingested}")
                batch = []

        if batch:
            vector_store.upsert_documents(batch, source=target_source)
            total_ingested += len(batch)

        print(f"\n[SUMMARY] Successfully ingested {total_ingested} records from source: {source_key.upper()}\n")
        return total_ingested

    except Exception as e:
        logger.error(f"Error during ingestion of {source_key}: {e}", exc_info=True)
        print(f"[ERROR] Source {source_key} failed: {e}")
        return total_ingested

def main():
    parser = argparse.ArgumentParser(description="AEGIS Threat Intelligence Ingestion Engine")
    parser.add_argument("--source", choices=["nvd", "mitre", "kev", "cisa_kev", "sigma", "all"], default="all",
                        help="Threat intel source to ingest")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of records to ingest")
    parser.add_argument("--no-resume", dest="resume", action="store_false", help="Ignore checkpoint and restart")
    parser.set_defaults(resume=True)

    args = parser.parse_args()

    if args.source == "all":
        for src in ["cisa_kev", "mitre", "sigma", "nvd"]:
            run_source(src, limit=args.limit, resume=args.resume)
    else:
        run_source(args.source, limit=args.limit, resume=args.resume)

if __name__ == "__main__":
    main()
