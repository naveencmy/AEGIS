import logging
from typing import Generator, Optional
from backend.app.config import settings
from backend.app.ingestion.base import BaseIngestor
from backend.app.models.schemas import ThreatDocumentItem

logger = logging.getLogger("aegis.ingest.mitre")

class MitreAttackIngestor(BaseIngestor):
    source_type = "mitre"
    canonical_base_url = "https://attack.mitre.org/techniques"

    def ingest(self, limit: Optional[int] = None, resume: bool = True) -> Generator[ThreatDocumentItem, None, None]:
        logger.info("Starting live MITRE ATT&CK STIX 2.1 ingestion...")
        resp = self.fetch_with_backoff(settings.MITRE_ATTACK_URL)
        data = resp.json()
        
        objects = data.get("objects", [])
        attack_patterns = [
            obj for obj in objects 
            if obj.get("type") == "attack-pattern" 
            and not obj.get("revoked", False) 
            and not obj.get("x_mitre_deprecated", False)
        ]
        
        total_available = len(attack_patterns)
        logger.info(f"Retrieved {total_available} active ATT&CK techniques from MITRE STIX 2.1.")
        
        checkpoint = self.load_checkpoint() if resume else {"current_index": 0}
        start_idx = checkpoint.get("current_index", 0) if resume else 0
        
        count = 0
        for i, item in enumerate(attack_patterns[start_idx:], start=start_idx):
            if limit is not None and count >= limit:
                break
                
            # Extract technique ID & canonical URL
            tech_id = None
            source_url = None
            for ref in item.get("external_references", []):
                if ref.get("source_name") == "mitre-attack":
                    tech_id = ref.get("external_id")
                    source_url = ref.get("url")
                    break
            
            if not tech_id:
                continue
                
            if not source_url:
                source_url = f"{self.canonical_base_url}/{tech_id.replace('.', '/')}"
                
            name = item.get("name", "Unknown Technique")
            description = item.get("description", "")
            detection = item.get("x_mitre_detection", "")
            platforms = ", ".join(item.get("x_mitre_platforms", []))
            tactics = [phase.get("phase_name") for phase in item.get("kill_chain_phases", []) if phase.get("phase_name")]
            tactics_str = ", ".join(tactics)
            
            title = f"{tech_id}: {name}"
            
            content = (
                f"[MITRE ATT&CK ENTERPRISE TECHNIQUE]\n"
                f"Technique ID: {tech_id}\n"
                f"Technique Name: {name}\n"
                f"Tactics: {tactics_str}\n"
                f"Supported Platforms: {platforms}\n"
                f"Description:\n{description}\n"
            )
            if detection:
                content += f"\nDetection Guidance:\n{detection}\n"
            
            provenance = self.get_provenance(
                doc_id=tech_id,
                source_url=source_url,
                title=title,
                severity="TACTICAL",
                tags=f"mitre,attack,{tactics_str.replace(' ', '')}"
            )
            
            doc_metadata = provenance.model_dump()
            doc_metadata.update({
                "technique_name": name,
                "tactics": tactics_str,
                "platforms": platforms
            })
            
            yield ThreatDocumentItem(
                doc_id=tech_id,
                source=self.source_type,
                source_url=source_url,
                fetched_at=provenance.fetched_at,
                title=title,
                content=content,
                metadata=doc_metadata
            )
            
            count += 1
            if count % 50 == 0 or (start_idx + count) == total_available:
                self.save_checkpoint({
                    "current_index": start_idx + count,
                    "total_records": total_available
                })

        self.save_checkpoint({
            "current_index": min(start_idx + count, total_available),
            "total_records": total_available
        })
        logger.info(f"MITRE ATT&CK ingestion batch completed. Processed {count} techniques.")
