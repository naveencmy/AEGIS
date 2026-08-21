import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional, Any
import requests
from backend.app.config import settings

logger = logging.getLogger("aegis.ingest.mitre")

class MitreAttackIngestor:
    """
    Sovereign MITRE ATT&CK STIX 2.1 Ingestor.
    Parses enterprise-attack.json for attack-pattern objects with valid ATT&CK IDs,
    extracts technique ID, name, description (first 1500 chars), tactics, and saves raw snapshot.
    """
    def __init__(self):
        self.url = settings.MITRE_ATTACK_URL
        self.raw_dir = Path(settings.BASE_DIR) / "data" / "raw" / "mitre"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def _save_raw_snapshot(self, bundle: dict[str, Any]) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.raw_dir / f"mitre_raw_snapshot_{timestamp}.json"
        try:
            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump(bundle, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write raw MITRE snapshot: {e}")
        return snapshot_path

    def ingest(self, limit: Optional[int] = 500, resume: bool = True) -> Generator[dict[str, Any], None, None]:
        logger.info(f"[MITRE] Fetching STIX 2.1 bundle from {self.url}...")
        
        retries = 0
        backoff = 2.0
        bundle = None
        while retries < settings.MAX_INGESTION_RETRIES:
            try:
                res = requests.get(self.url, timeout=50.0)
                if res.status_code == 200:
                    bundle = res.json()
                    self._save_raw_snapshot(bundle)
                    break
            except Exception as e:
                logger.warning(f"[MITRE] Fetch attempt {retries+1} failed: {e}. Retrying in {backoff}s...")
                import time; time.sleep(backoff)
            retries += 1
            backoff *= 2.0

        if not bundle:
            logger.error("[MITRE] Failed to download MITRE STIX bundle after retries.")
            return

        objects = bundle.get("objects", [])
        techniques_yielded = 0

        for obj in objects:
            if obj.get("type") != "attack-pattern":
                continue
            if obj.get("revoked", False) or obj.get("x_mitre_deprecated", False):
                continue

            ext_refs = obj.get("external_references", [])
            mitre_ref = next((r for r in ext_refs if r.get("source_name") == "mitre-attack"), None)
            if not mitre_ref or not mitre_ref.get("external_id"):
                continue

            tech_id = mitre_ref.get("external_id")
            source_url = mitre_ref.get("url", f"https://attack.mitre.org/techniques/{tech_id}")
            name = obj.get("name", "Unknown Technique")
            
            # First 1500 chars of description
            raw_desc = obj.get("description", "")
            description = raw_desc[:1500] if len(raw_desc) > 1500 else raw_desc

            # Tactics (kill chain phases)
            phases = obj.get("kill_chain_phases", [])
            tactics = [p.get("phase_name") for p in phases if p.get("kill_chain_name") == "mitre-attack"]
            tactics_str = ", ".join(tactics) if tactics else "Enterprise"

            # Platforms
            platforms = obj.get("x_mitre_platforms", [])
            platforms_str = ", ".join(platforms) if platforms else "Cross-Platform"

            detection = obj.get("x_mitre_detection", "Analyze process monitoring, command-line arguments, and authentication telemetry.")

            content = (
                f"MITRE ATT&CK Technique: {tech_id} - {name}\n"
                f"Tactics: {tactics_str}\n"
                f"Platforms: {platforms_str}\n"
                f"Description: {description}\n"
                f"Detection Guidance: {detection}"
            )

            now_iso = datetime.now(timezone.utc).isoformat()
            doc = {
                "id": f"mitre::{tech_id}",
                "doc_id": tech_id,
                "source": "mitre",
                "source_url": source_url,
                "fetched_at": now_iso,
                "title": f"{tech_id}: {name}",
                "content": content,
                "metadata": {
                    "doc_id": tech_id,
                    "source": "mitre",
                    "source_url": source_url,
                    "fetched_at": now_iso,
                    "title": f"{tech_id}: {name}",
                    "technique_name": name,
                    "tactics": tactics_str,
                    "platforms": platforms_str,
                    "severity": "TACTICAL",
                    "tags": f"mitre,attack,{','.join(tactics)}"
                }
            }

            yield doc
            techniques_yielded += 1
            if limit and techniques_yielded >= limit:
                break

        logger.info(f"[MITRE] Ingested {techniques_yielded} active ATT&CK techniques.")

mitre_ingestor = MitreAttackIngestor()
