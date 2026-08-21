import io
import logging
import zipfile
from typing import Generator, Optional
import yaml

from backend.app.config import settings
from backend.app.ingestion.base import BaseIngestor
from backend.app.models.schemas import ThreatDocumentItem

logger = logging.getLogger("aegis.ingest.sigma")

class SigmaIngestor(BaseIngestor):
    source_type = "sigma"
    canonical_base_url = "https://github.com/SigmaHQ/sigma/blob/master"

    def ingest(self, limit: Optional[int] = None, resume: bool = True) -> Generator[ThreatDocumentItem, None, None]:
        logger.info("Starting live SigmaHQ detection rules ingestion...")
        
        # Download Sigma repository master zip
        logger.info(f"Downloading Sigma rules archive from {settings.SIGMA_RULES_ZIP}...")
        resp = self.fetch_with_backoff(settings.SIGMA_RULES_ZIP, timeout=60.0)
        
        checkpoint = self.load_checkpoint() if resume else {"current_index": 0}
        start_idx = checkpoint.get("current_index", 0) if resume else 0
        
        count = 0
        total_rules = 0
        
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            # Filter rule files under rules/ directory ending in .yml or .yaml
            rule_filenames = [
                name for name in z.namelist() 
                if ("/rules/" in name or name.startswith("sigma-master/rules/")) 
                and (name.endswith(".yml") or name.endswith(".yaml"))
                and not name.endswith(".pre-commit-config.yaml")
            ]
            
            total_rules = len(rule_filenames)
            logger.info(f"Found {total_rules} Sigma rule files in repository archive.")
            
            for i, filename in enumerate(rule_filenames[start_idx:], start=start_idx):
                if limit is not None and count >= limit:
                    break
                    
                try:
                    file_bytes = z.read(filename)
                    docs = list(yaml.safe_load_all(file_bytes.decode("utf-8", errors="replace")))
                except Exception as e:
                    logger.debug(f"Skipping malformed YAML {filename}: {e}")
                    continue
                    
                for doc in docs:
                    if not isinstance(doc, dict) or "title" not in doc:
                        continue
                        
                    rule_id = str(doc.get("id") or doc.get("title", "")).strip()
                    if not rule_id:
                        continue
                        
                    title = doc.get("title", "Untitled Sigma Rule")
                    description = doc.get("description", "")
                    level = str(doc.get("level", "medium")).upper()
                    status = doc.get("status", "experimental")
                    author = doc.get("author", "Unknown")
                    date = doc.get("date", "")
                    references = doc.get("references", [])
                    ref_str = ", ".join(references) if isinstance(references, list) else str(references)
                    
                    tags = doc.get("tags", [])
                    tag_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
                    
                    logsource = doc.get("logsource", {})
                    logsource_str = ", ".join([f"{k}: {v}" for k, v in logsource.items()]) if isinstance(logsource, dict) else str(logsource)
                    
                    detection = doc.get("detection", {})
                    detection_str = yaml.dump(detection, default_flow_style=False) if isinstance(detection, dict) else str(detection)
                    
                    falsepositives = doc.get("falsepositives", [])
                    fp_str = ", ".join(falsepositives) if isinstance(falsepositives, list) else str(falsepositives)
                    
                    # Compute relative path for canonical URL
                    rel_path = filename
                    if rel_path.startswith("sigma-master/"):
                        rel_path = rel_path[len("sigma-master/"):]
                    source_url = f"{self.canonical_base_url}/{rel_path}"
                    
                    content = (
                        f"[SIGMA DETECTION RULE]\n"
                        f"Rule ID: {rule_id}\n"
                        f"Title: {title}\n"
                        f"Threat Level: {level}\n"
                        f"Status: {status}\n"
                        f"Author: {author}\n"
                        f"Date: {date}\n"
                        f"Log Source: {logsource_str}\n"
                        f"Tags / ATT&CK Techniques: {tag_str}\n"
                        f"Description:\n{description}\n\n"
                        f"Detection Logic:\n{detection_str}\n"
                        f"Potential False Positives: {fp_str}\n"
                        f"References: {ref_str}"
                    )
                    
                    provenance = self.get_provenance(
                        doc_id=rule_id,
                        source_url=source_url,
                        title=f"Sigma: {title} ({level})",
                        severity=level,
                        tags=f"sigma,{level.lower()},{tag_str.replace(' ', '')}"
                    )
                    
                    doc_metadata = provenance.model_dump()
                    doc_metadata.update({
                        "rule_title": title,
                        "level": level,
                        "status": status,
                        "logsource": logsource_str,
                        "tags": tag_str
                    })
                    
                    yield ThreatDocumentItem(
                        doc_id=rule_id,
                        source=self.source_type,
                        source_url=source_url,
                        fetched_at=provenance.fetched_at,
                        title=f"Sigma: {title}",
                        content=content,
                        metadata=doc_metadata
                    )
                    
                    count += 1
                    if count % 50 == 0 or (start_idx + count) == total_rules:
                        self.save_checkpoint({
                            "current_index": start_idx + count,
                            "total_records": total_rules
                        })
                    break

        self.save_checkpoint({
            "current_index": min(start_idx + count, total_rules),
            "total_records": total_rules
        })
        logger.info(f"Sigma rules ingestion batch completed. Processed {count} rules.")
