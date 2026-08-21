import pytest
from backend.app.ingestion.kev_ingest import kev_ingestor
from backend.app.ingestion.mitre_ingest import mitre_ingestor
from backend.app.ingestion.sigma_ingest import sigma_ingestor

def test_cisa_kev_live_ingestion():
    docs = list(kev_ingestor.ingest(limit=5, resume=False))
    assert len(docs) == 5
    for doc in docs:
        assert doc["source"] == "cisa_kev"
        assert doc["doc_id"].startswith("CVE-")
        assert doc["source_url"].startswith("http")
        assert "T" in doc["fetched_at"]

def test_mitre_attack_live_ingestion():
    docs = list(mitre_ingestor.ingest(limit=5, resume=False))
    assert len(docs) == 5
    for doc in docs:
        assert doc["source"] == "mitre"
        assert doc["doc_id"].startswith("T")
        assert "tactics" in doc["metadata"]

def test_sigma_rules_live_ingestion():
    docs = list(sigma_ingestor.ingest(limit=5, resume=False))
    assert len(docs) == 5
    for doc in docs:
        assert doc["source"] == "sigma"
        assert doc["metadata"]["level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
