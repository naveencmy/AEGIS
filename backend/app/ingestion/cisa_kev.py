import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional, Any
import requests
from backend.app.config import settings

logger = logging.getLogger("aegis.ingest.cisa_kev")

class CisaKevIngestor:
    """
    Sovereign CISA Known Exploited Vulnerabilities (KEV) Catalog Ingestor.
    Fetches official JSON feed, extracts cveID, vulnerabilityName, shortDescription,
    dateAdded, dueDate, knownRansomwareCampaignUse, and saves raw audit snapshot.
    """
    def __init__(self):
        self.url = settings.CISA_KEV_URL
        self.raw_dir = Path(settings.BASE_DIR) / "data" / "raw" / "kev"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def _save_raw_snapshot(self, feed_data: dict[str, Any]) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.raw_dir / f"cisa_kev_raw_snapshot_{timestamp}.json"
        try:
            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump(feed_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write raw CISA KEV snapshot: {e}")
        return snapshot_path

    def ingest(self, limit: Optional[int] = None, resume: bool = True) -> Generator[dict[str, Any], None, None]:
        logger.info(f"[CISA KEV] Fetching live feed from {self.url}...")
        
        retries = 0
        backoff = 2.0
        data = None
        while retries < settings.MAX_INGESTION_RETRIES:
            try:
                res = requests.get(self.url, timeout=40.0)
                if res.status_code == 200:
                    data = res.json()
                    self._save_raw_snapshot(data)
                    break
            except Exception as e:
                logger.warning(f"[CISA KEV] Fetch attempt {retries+1} failed: {e}. Retrying in {backoff}s...")
                import time; time.sleep(backoff)
            retries += 1
            backoff *= 2.0

        if not data:
            logger.error("[CISA KEV] Failed to download CISA KEV catalog after retries.")
            return

        vulns = data.get("vulnerabilities", [])
        logger.info(f"[CISA KEV] Loaded {len(vulns)} catalog records from live feed.")

        count = 0
        for item in vulns:
            cve_id = item.get("cveID")
            if not cve_id:
                continue

            vendor_project = item.get("vendorProject", "Unknown")
            product = item.get("product", "Unknown")
            vuln_name = item.get("vulnerabilityName", "")
            date_added = item.get("dateAdded", "")
            short_desc = item.get("shortDescription", "")
            due_date = item.get("dueDate", "")
            action = item.get("requiredAction", "Apply mitigations per vendor instructions.")
            ransomware = item.get("knownRansomwareCampaignUse", "Unknown")
            notes = item.get("notes", "")

            content = (
                f"CISA Known Exploited Vulnerability: {cve_id}\n"
                f"Vendor/Product: {vendor_project} - {product}\n"
                f"Vulnerability: {vuln_name}\n"
                f"Date Added to KEV: {date_added} | Remediation Due Date: {due_date}\n"
                f"Known Ransomware Campaign Association: {ransomware}\n"
                f"Mandatory Action: {action}\n"
                f"Description: {short_desc}\n"
                f"Notes: {notes}"
            )

            now_iso = datetime.now(timezone.utc).isoformat()
            doc = {
                "id": f"cisa_kev::{cve_id}",
                "doc_id": cve_id,
                "source": "cisa_kev",
                "source_url": f"https://www.cisa.gov/known-exploited-vulnerabilities-catalog?search_api_fulltext={cve_id}",
                "fetched_at": now_iso,
                "title": f"CISA KEV: {cve_id} - {vendor_project} {product} ({vuln_name})",
                "content": content,
                "metadata": {
                    "doc_id": cve_id,
                    "source": "cisa_kev",
                    "source_url": f"https://www.cisa.gov/known-exploited-vulnerabilities-catalog?search_api_fulltext={cve_id}",
                    "fetched_at": now_iso,
                    "title": f"CISA KEV: {cve_id} - {vendor_project} {product}",
                    "vendor": vendor_project,
                    "product": product,
                    "date_added": date_added,
                    "due_date": due_date,
                    "ransomware": ransomware,
                    "severity": "CRITICAL_EXPLOITED",
                    "tags": f"cisa_kev,exploited,ransomware_{ransomware.lower()}"
                }
            }

            yield doc
            count += 1
            if limit and count >= limit:
                break

        logger.info(f"[CISA KEV] Ingested {count} records into pipeline.")

cisa_kev_ingestor = CisaKevIngestor()
