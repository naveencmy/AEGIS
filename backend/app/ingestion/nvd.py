import logging
import time
from typing import Generator, Optional
from backend.app.config import settings
from backend.app.ingestion.base import BaseIngestor
from backend.app.models.schemas import ThreatDocumentItem

logger = logging.getLogger("aegis.ingest.nvd")

class NvdIngestor(BaseIngestor):
    source_type = "nvd"
    canonical_base_url = "https://nvd.nist.gov/vuln/detail"

    def ingest(self, limit: Optional[int] = None, resume: bool = True, batch_size: int = 50) -> Generator[ThreatDocumentItem, None, None]:
        logger.info("Starting live NVD API 2.0 ingestion (Rate limit compliant: 5 req/30s)...")
        
        checkpoint = self.load_checkpoint() if resume else {"current_index": 0}
        start_index = checkpoint.get("current_index", 0) if resume else 0
        total_fetched = 0
        
        while True:
            if limit is not None and total_fetched >= limit:
                logger.info(f"Reached requested limit of {limit} NVD records.")
                break
                
            current_batch = min(batch_size, limit - total_fetched) if limit is not None else batch_size
            params = {
                "startIndex": start_index,
                "resultsPerPage": current_batch
            }
            
            logger.info(f"Requesting NVD API: startIndex={start_index}, resultsPerPage={current_batch}...")
            resp = self.fetch_with_backoff(settings.NVD_API_URL, params=params)
            data = resp.json()
            
            total_results = data.get("totalResults", 0)
            vulnerabilities = data.get("vulnerabilities", [])
            
            if not vulnerabilities:
                logger.info("No more vulnerabilities returned by NVD API.")
                break
                
            for item in vulnerabilities:
                cve_obj = item.get("cve", {})
                cve_id = cve_obj.get("id", "").strip()
                if not cve_id:
                    continue
                    
                # English description
                descriptions = cve_obj.get("descriptions", [])
                desc_text = ""
                for d in descriptions:
                    if d.get("lang") == "en":
                        desc_text = d.get("value", "")
                        break
                if not desc_text and descriptions:
                    desc_text = descriptions[0].get("value", "")
                    
                # CVSS metrics
                metrics = cve_obj.get("metrics", {})
                cvss_data = None
                severity = "UNKNOWN"
                score = None
                vector = ""
                
                # Check CVSS v3.1 -> v3.0 -> v2.0
                if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
                    m = metrics["cvssMetricV31"][0].get("cvssData", {})
                    score = m.get("baseScore")
                    severity = m.get("baseSeverity", "UNKNOWN")
                    vector = m.get("vectorString", "")
                elif "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
                    m = metrics["cvssMetricV30"][0].get("cvssData", {})
                    score = m.get("baseScore")
                    severity = m.get("baseSeverity", "UNKNOWN")
                    vector = m.get("vectorString", "")
                elif "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
                    m = metrics["cvssMetricV2"][0].get("cvssData", {})
                    score = m.get("baseScore")
                    severity = metrics["cvssMetricV2"][0].get("baseSeverity", "UNKNOWN")
                    vector = m.get("vectorString", "")
                    
                # Weaknesses (CWE)
                weaknesses = []
                for w in cve_obj.get("weaknesses", []):
                    for desc in w.get("description", []):
                        val = desc.get("value", "")
                        if val and val != "NVD-CWE-noinfo" and val != "NVD-CWE-Other":
                            weaknesses.append(val)
                cwe_str = ", ".join(weaknesses) if weaknesses else "Not Specified"
                
                source_url = f"{self.canonical_base_url}/{cve_id}"
                title = f"{cve_id} (Severity: {severity} - Score: {score or 'N/A'})"
                
                content = (
                    f"[NVD CVE RECORD]\n"
                    f"CVE ID: {cve_id}\n"
                    f"Severity: {severity}\n"
                    f"CVSS Base Score: {score or 'N/A'}\n"
                    f"CVSS Vector: {vector or 'N/A'}\n"
                    f"Associated Weaknesses (CWE): {cwe_str}\n"
                    f"Description:\n{desc_text}\n"
                )
                
                provenance = self.get_provenance(
                    doc_id=cve_id,
                    source_url=source_url,
                    title=title,
                    severity=severity,
                    tags=f"nvd,cve,{severity.lower()},{cwe_str.replace(' ', '')}"
                )
                
                doc_metadata = provenance.model_dump()
                doc_metadata.update({
                    "cvss_score": float(score) if score is not None else 0.0,
                    "cvss_severity": severity,
                    "cvss_vector": vector,
                    "cwe": cwe_str
                })
                
                yield ThreatDocumentItem(
                    doc_id=cve_id,
                    source=self.source_type,
                    source_url=source_url,
                    fetched_at=provenance.fetched_at,
                    title=title,
                    content=content,
                    metadata=doc_metadata
                )
                
                total_fetched += 1
                if limit is not None and total_fetched >= limit:
                    break

            start_index += len(vulnerabilities)
            self.save_checkpoint({
                "current_index": start_index,
                "total_records": total_results
            })
            
            if start_index >= total_results:
                logger.info(f"Completed all {total_results} NVD records.")
                break
                
            # Rate limit adherence: without API key, max 5 req / 30s -> sleep >= 6.1s
            logger.info(f"NVD Rate Limit Throttle: Sleeping {settings.NVD_RATE_LIMIT_DELAY}s before next page...")
            time.sleep(settings.NVD_RATE_LIMIT_DELAY)
            
        logger.info(f"NVD ingestion batch complete. Total records yielded: {total_fetched}.")
