import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Generator, Optional, Any
import requests
from backend.app.config import settings

logger = logging.getLogger("aegis.ingest.nvd")

class NVDIngestor:
    """
    Sovereign Live NVD API 2.0 Ingestor with 120-day window chunking from 2023-01-01 to 2026-12-31,
    pagination (resultsPerPage=2000), 6-second delay throttle, resumable checkpointing,
    and raw JSON snapshot auditing.
    """
    def __init__(self):
        self.api_url = settings.NVD_API_URL
        self.rate_limit_delay = 6.0
        self.checkpoint_file = Path(settings.CHECKPOINT_DIR) / "nvd_checkpoint.json"
        self.raw_dir = Path(settings.BASE_DIR) / "data" / "raw" / "nvd"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.start_date_base = datetime(2023, 1, 1, 0, 0, 0)
        self.end_date_max = datetime(2026, 12, 31, 23, 59, 59)

    def _load_checkpoint(self) -> dict[str, Any]:
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load NVD checkpoint: {e}")
        return {"current_window_idx": 0, "current_start_index": 0}

    def _save_checkpoint(self, window_idx: int, start_idx: int, total_available: int):
        try:
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump({
                    "current_window_idx": window_idx,
                    "current_start_index": start_idx,
                    "total_available": total_available,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save NVD checkpoint: {e}")

    def _save_raw_snapshot(self, data: dict[str, Any], start_index: int) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.raw_dir / f"nvd_raw_start_{start_index}_{timestamp}.json"
        try:
            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write raw NVD snapshot: {e}")
        return snapshot_path

    def _fetch_window_page(self, start_date_str: str, end_date_str: str, start_index: int, results_per_page: int = 2000) -> dict[str, Any]:
        params = {
            "pubStartDate": start_date_str,
            "pubEndDate": end_date_str,
            "startIndex": start_index,
            "resultsPerPage": results_per_page
        }
        headers = {
            "User-Agent": "AEGIS-Sovereign-Sentinel/0.1.0"
        }

        retries = 0
        backoff = 2.0
        while retries < settings.MAX_INGESTION_RETRIES:
            try:
                logger.info(f"[NVD] Fetching window [{start_date_str} -> {end_date_str}] startIndex={start_index}, pageSize={results_per_page} (Attempt {retries+1}/{settings.MAX_INGESTION_RETRIES})...")
                res = requests.get(self.api_url, params=params, headers=headers, timeout=45.0)
                if res.status_code == 200:
                    data = res.json()
                    self._save_raw_snapshot(data, start_index)
                    return data
                elif res.status_code in [403, 429]:
                    logger.warning(f"[NVD] Rate limit hit ({res.status_code}). Backoff sleep for {backoff * 3}s...")
                    time.sleep(backoff * 3)
                else:
                    logger.warning(f"[NVD] HTTP error {res.status_code}. Retrying in {backoff}s...")
                    time.sleep(backoff)
            except Exception as e:
                logger.warning(f"[NVD] Network error: {e}. Retrying in {backoff}s...")
                time.sleep(backoff)

            retries += 1
            backoff *= settings.RETRY_BACKOFF_FACTOR

        logger.error(f"[NVD] All {settings.MAX_INGESTION_RETRIES} retries failed for startIndex={start_index}.")
        return {}

    def ingest(self, limit: Optional[int] = None, resume: bool = True) -> Generator[dict[str, Any], None, None]:
        # Generate 115-day windows (compliant with NIST 120-day limit)
        windows = []
        cur_start = self.start_date_base
        while cur_start < self.end_date_max:
            cur_end = min(cur_start + timedelta(days=115), self.end_date_max)
            s_str = cur_start.strftime("%Y-%m-%dT%H:%M:%S.000")
            e_str = cur_end.strftime("%Y-%m-%dT%H:%M:%S.999")
            windows.append((s_str, e_str))
            cur_start = cur_end + timedelta(seconds=1)

        cp = self._load_checkpoint() if resume else {"current_window_idx": 0, "current_start_index": 0}
        window_idx = cp.get("current_window_idx", 0)
        start_index = cp.get("current_start_index", 0)
        fetched_total = 0

        while window_idx < len(windows):
            s_str, e_str = windows[window_idx]
            page_size = min(limit - fetched_total, 2000) if (limit and (limit - fetched_total) < 2000) else 2000
            
            data = self._fetch_window_page(s_str, e_str, start_index, results_per_page=page_size)
            vulns = data.get("vulnerabilities", [])
            total_results = data.get("totalResults", 0)

            if not vulns:
                window_idx += 1
                start_index = 0
                self._save_checkpoint(window_idx, start_index, total_results)
                time.sleep(self.rate_limit_delay)
                continue

            for item in vulns:
                cve = item.get("cve", {})
                cve_id = cve.get("id")
                if not cve_id:
                    continue

                # 1. Description
                descriptions = cve.get("descriptions", [])
                desc_text = next((d.get("value") for d in descriptions if d.get("lang") == "en"), "")

                # 2. CVSS v3.1 Metrics
                metrics = cve.get("metrics", {})
                cvss_data = {}
                if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
                    cvss_data = metrics["cvssMetricV31"][0].get("cvssData", {})
                elif "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
                    cvss_data = metrics["cvssMetricV30"][0].get("cvssData", {})
                elif "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
                    cvss_data = metrics["cvssMetricV2"][0].get("cvssData", {})

                base_score = cvss_data.get("baseScore", 0.0)
                base_severity = cvss_data.get("baseSeverity", "UNKNOWN")
                vector_string = cvss_data.get("vectorString", "")

                # 3. Weaknesses (CWE)
                weaknesses_list = []
                for w in cve.get("weaknesses", []):
                    for d in w.get("description", []):
                        if d.get("value") and d.get("value") != "NVD-CWE-noinfo":
                            weaknesses_list.append(d.get("value"))
                cwe_str = ", ".join(weaknesses_list) if weaknesses_list else "CWE-Unclassified"

                # 4. Canonical Reference URL
                refs = cve.get("references", [])
                ref_url = refs[0].get("url") if refs else f"https://nvd.nist.gov/vuln/detail/{cve_id}"

                # 5. Published Date
                published_date = cve.get("published", "")

                content = (
                    f"CVE Record: {cve_id}\n"
                    f"Published: {published_date}\n"
                    f"CVSS v3.1 Score: {base_score} ({base_severity})\n"
                    f"CVSS Vector: {vector_string}\n"
                    f"Weaknesses: {cwe_str}\n"
                    f"Canonical Reference: {ref_url}\n"
                    f"Description: {desc_text}"
                )

                now_iso = datetime.now(timezone.utc).isoformat()
                doc = {
                    "id": f"nvd::{cve_id}",
                    "doc_id": cve_id,
                    "source": "nvd",
                    "source_url": ref_url,
                    "fetched_at": now_iso,
                    "title": f"{cve_id} - CVSS {base_score} ({base_severity})",
                    "content": content,
                    "metadata": {
                        "doc_id": cve_id,
                        "source": "nvd",
                        "source_url": ref_url,
                        "fetched_at": now_iso,
                        "title": f"{cve_id} - CVSS {base_score} ({base_severity})",
                        "severity": str(base_severity),
                        "score": str(base_score),
                        "vector": str(vector_string),
                        "cwe": str(cwe_str),
                        "published_date": str(published_date),
                        "tags": f"nvd,cve,{cwe_str.lower()}"
                    }
                }

                yield doc
                fetched_total += 1
                if limit and fetched_total >= limit:
                    break

            start_index += len(vulns)
            if start_index >= total_results:
                window_idx += 1
                start_index = 0

            self._save_checkpoint(window_idx, start_index, total_results)

            if limit and fetched_total >= limit:
                break

            logger.info(f"[NVD] Pacing throttle: Sleeping {self.rate_limit_delay}s...")
            time.sleep(self.rate_limit_delay)

nvd_ingestor = NVDIngestor()
