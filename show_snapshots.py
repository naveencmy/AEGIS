import json
from pathlib import Path

sources = ["nvd", "mitre", "kev", "sigma"]
for src in sources:
    raw_dir = Path("data/raw") / src
    files = list(raw_dir.glob("*.json"))
    print(f"\n=======================================================")
    print(f"  SOURCE: {src.upper()} SNAPSHOT PROOF")
    print(f"=======================================================")
    if files:
        latest = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        print(f"File: {latest} ({latest.stat().st_size:,} bytes)")
        print("--- FIRST 20 LINES ---")
        with open(latest, "r", encoding="utf-8") as f:
            lines = [f.readline() for _ in range(20)]
            print("".join(lines))
    else:
        print("No snapshot found.")
