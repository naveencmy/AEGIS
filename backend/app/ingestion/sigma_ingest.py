import json
import logging
import os
import subprocess
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Generator, Optional, Any
import yaml
from backend.app.config import settings

logger = logging.getLogger("aegis.ingest.sigma")

def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)

class SigmaRuleIngestor:
    """
    Sovereign Sigma Rules Ingestor.
    Clones/downloads SigmaHQ rules repo (depth 1), parses YAML detection rules,
    extracts title, id, logsource, detection logic, and saves raw audit snapshot.
    """
    def __init__(self):
        self.repo_url = settings.SIGMA_REPO_URL
        self.sigma_dir = Path(settings.BASE_DIR) / "data" / "sigma_repo"
        self.raw_dir = Path(settings.BASE_DIR) / "data" / "raw" / "sigma"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_sigma_repo(self):
        if not self.sigma_dir.exists() or not (self.sigma_dir / "rules").exists():
            logger.info(f"[SIGMA] Shallow-cloning Sigma repository into {self.sigma_dir}...")
            self.sigma_dir.parent.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", self.repo_url, str(self.sigma_dir)],
                    check=True,
                    capture_output=True,
                    timeout=120
                )
                logger.info("[SIGMA] Repository shallow clone successful.")
            except Exception as e:
                logger.warning(f"[SIGMA] Git clone failed ({e}). Attempting archive download...")
                import requests, zipfile, io
                zip_url = "https://github.com/SigmaHQ/sigma/archive/refs/heads/master.zip"
                res = requests.get(zip_url, timeout=60)
                if res.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                        z.extractall(self.sigma_dir.parent)
                    extracted = self.sigma_dir.parent / "sigma-master"
                    if extracted.exists():
                        if self.sigma_dir.exists():
                            import shutil; shutil.rmtree(self.sigma_dir, ignore_errors=True)
                        extracted.rename(self.sigma_dir)

    def _save_raw_snapshot(self, rules_data: list[dict[str, Any]]) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.raw_dir / f"sigma_raw_snapshot_{timestamp}.json"
        try:
            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump(rules_data, f, default=json_serial, indent=2)
            logger.info(f"[SIGMA] Saved raw snapshot to {snapshot_path}")
        except Exception as e:
            logger.warning(f"Failed to write raw Sigma snapshot: {e}")
        return snapshot_path

    def ingest(self, limit: Optional[int] = 200, resume: bool = True) -> Generator[dict[str, Any], None, None]:
        self._ensure_sigma_repo()
        rules_dir = self.sigma_dir / "rules"
        if not rules_dir.exists():
            logger.error(f"[SIGMA] Rules directory not found at {rules_dir}")
            return

        valid_rules = 0
        raw_snapshots_buffer = []
        yaml_files = list(rules_dir.rglob("*.yml")) + list(rules_dir.rglob("*.yaml"))
        logger.info(f"[SIGMA] Found {len(yaml_files)} YAML candidate files.")

        for yf in yaml_files:
            try:
                with open(yf, "r", encoding="utf-8", errors="ignore") as f:
                    docs = yaml.safe_load_all(f)
                    for doc_data in docs:
                        if not isinstance(doc_data, dict):
                            continue
                        
                        rule_id = doc_data.get("id")
                        title = doc_data.get("title")
                        logsource = doc_data.get("logsource", {})
                        detection = doc_data.get("detection", {})

                        if not rule_id or not title or not detection:
                            continue

                        raw_snapshots_buffer.append(doc_data)

                        level = doc_data.get("level", "medium").upper()
                        description = doc_data.get("description", "Sigma detection rule")
                        status = doc_data.get("status", "experimental")
                        tags = doc_data.get("tags", [])

                        logsource_str = ", ".join(f"{k}={v}" for k, v in logsource.items()) if isinstance(logsource, dict) else str(logsource)
                        detection_str = yaml.dump(detection, default_flow_style=False)

                        content = (
                            f"[SIGMA DETECTION RULE] Rule ID: {rule_id}\n"
                            f"Title: {title}\n"
                            f"Severity Level: {level} (Status: {status})\n"
                            f"Log Source: {logsource_str}\n"
                            f"Description: {description}\n"
                            f"Detection Logic:\n{detection_str}"
                        )

                        now_iso = datetime.now(timezone.utc).isoformat()
                        canonical_url = f"https://github.com/SigmaHQ/sigma/blob/master/{yf.relative_to(self.sigma_dir).as_posix()}"

                        doc = {
                            "id": f"sigma::{rule_id}",
                            "doc_id": str(rule_id),
                            "source": "sigma",
                            "source_url": canonical_url,
                            "fetched_at": now_iso,
                            "title": f"Sigma: {title} ({level})",
                            "content": content,
                            "metadata": {
                                "doc_id": str(rule_id),
                                "source": "sigma",
                                "source_url": canonical_url,
                                "fetched_at": now_iso,
                                "title": f"Sigma: {title}",
                                "level": level,
                                "status": status,
                                "logsource": logsource_str[:250],
                                "severity": level,
                                "tags": f"sigma,rule,{','.join(tags) if isinstance(tags, list) else ''}"
                            }
                        }

                        yield doc
                        valid_rules += 1
                        if limit and valid_rules >= limit:
                            break

                if limit and valid_rules >= limit:
                    break
            except Exception as e:
                logger.debug(f"[SIGMA] Skipping {yf.name}: {e}")

        if raw_snapshots_buffer:
            self._save_raw_snapshot(raw_snapshots_buffer)

        logger.info(f"[SIGMA] Ingested {valid_rules} valid detection rules.")

sigma_ingestor = SigmaRuleIngestor()
