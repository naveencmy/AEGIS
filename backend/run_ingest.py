import argparse
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.ingestion.pipeline import pipeline_manager
from backend.app.rag.vector_store import vector_store

def main():
    parser = argparse.ArgumentParser(
        description="AEGIS Threat Intelligence Live Ingestion Tool (Sovereign / Real Data)"
    )
    parser.add_argument(
        "--source",
        choices=["all", "cisa_kev", "mitre", "nvd", "sigma"],
        default="all",
        help="Threat intelligence source to ingest (default: all)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum records to fetch per source (useful for fast verification or rate limits)"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Do not resume from disk checkpoint; restart from beginning"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="ChromaDB batch upsert chunk size (default: 50)"
    )

    args = parser.parse_args()
    resume = not args.no_resume

    print("================================================================")
    print("  AEGIS Cyber Sentinel — Live Threat Intel Ingestion Engine")
    print("================================================================")
    print(f"Target Source: {args.source}")
    print(f"Record Limit:  {args.limit or 'Full dataset'}")
    print(f"Resume State:  {resume}")
    print(f"Batch Size:    {args.batch_size}")
    print("================================================================")

    sources = ["cisa_kev", "mitre", "sigma", "nvd"] if args.source == "all" else [args.source]

    for s in sources:
        print(f"\n[+] Starting live ingestion for source: '{s.upper()}'...")
        try:
            count = pipeline_manager.run_source_sync(
                source=s,
                limit=args.limit,
                resume=resume,
                batch_size=args.batch_size
            )
            print(f"[OK] Ingestion for '{s.upper()}' succeeded. Indexed {count} records into ChromaDB.")
        except Exception as e:
            print(f"[FAIL] Ingestion failed for '{s.upper()}': {e}", file=sys.stderr)
            if args.source != "all":
                sys.exit(1)

    print("\n================================================================")
    print("  Current Knowledge Base Summary")
    print("================================================================")
    stats = vector_store.get_stats()
    print(f"Total Verified Documents in ChromaDB: {stats['total']}")
    for k, v in stats['breakdown'].items():
        print(f"  - {k.upper():<10}: {v} records")
    print("================================================================\n")

if __name__ == "__main__":
    main()
