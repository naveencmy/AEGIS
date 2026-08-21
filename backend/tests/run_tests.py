import unittest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.ingestion.kev_ingest import kev_ingestor
from backend.app.ingestion.mitre_ingest import mitre_ingestor
from backend.app.ingestion.sigma_ingest import sigma_ingestor
from backend.app.rag.guard import hallucination_guard
from backend.app.rag.chain import rag_chain
from backend.app.models.schemas import ChatRequest

class AegisIngestionTests(unittest.TestCase):
    def test_cisa_kev_live_ingestion(self):
        docs = list(kev_ingestor.ingest(limit=5, resume=False))
        self.assertEqual(len(docs), 5)
        for doc in docs:
            self.assertEqual(doc["source"], "cisa_kev")
            self.assertTrue(doc["doc_id"].startswith("CVE-"))
            self.assertTrue(doc["source_url"].startswith("http"))
            self.assertIn("T", doc["fetched_at"])

    def test_mitre_attack_live_ingestion(self):
        docs = list(mitre_ingestor.ingest(limit=5, resume=False))
        self.assertEqual(len(docs), 5)
        for doc in docs:
            self.assertEqual(doc["source"], "mitre")
            self.assertTrue(doc["doc_id"].startswith("T"))
            self.assertIn("tactics", doc["metadata"])

    def test_sigma_rules_live_ingestion(self):
        docs = list(sigma_ingestor.ingest(limit=5, resume=False))
        self.assertEqual(len(docs), 5)
        for doc in docs:
            self.assertEqual(doc["source"], "sigma")
            self.assertIn(doc["metadata"]["level"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

class AegisGuardTests(unittest.TestCase):
    def test_hallucination_guard_strips_fake_cve(self):
        input_text = "Based on analysis, CVE-2021-44228 is critical. Also, attackers use fictitious CVE-2099-77777 and technique T9999.999."
        res = hallucination_guard.validate_and_sanitize(input_text, context_doc_ids={"CVE-2021-44228"})
        self.assertTrue(res.unverified_claims_removed)
        self.assertIn("CVE-2021-44228", res.verified_ids)
        self.assertIn("CVE-2099-77777", res.hallucinations_detected)
        self.assertIn("T9999.999", res.hallucinations_detected)
        self.assertIn("[UNVERIFIED CLAIM REMOVED: CVE-2099-77777]", res.sanitized_text)

    def test_hallucination_guard_clean_text(self):
        clean_text = "Analysis for CVE-2021-44228 under technique T1059."
        res = hallucination_guard.validate_and_sanitize(clean_text, context_doc_ids={"CVE-2021-44228", "T1059"})
        self.assertFalse(res.unverified_claims_removed)
        self.assertEqual(len(res.hallucinations_detected), 0)
        self.assertEqual(len(res.verified_ids), 2)

class AegisRAGChainTests(unittest.TestCase):
    def test_rag_chain_response_contract_shape(self):
        req = ChatRequest(query="Analyze Apache Log4j2 CVE-2021-44228 vulnerability and CISA KEV exploitation.")
        res = rag_chain.run(req)
        self.assertFalse(res.insufficient_evidence)
        self.assertGreater(len(res.citations), 0)
        self.assertIn("CVE-2021-44228", res.cve_ids)
        self.assertGreater(res.latency_ms, 0)

    def test_rag_chain_silence_invariant(self):
        req = ChatRequest(query="Explain the zero-day exploit mechanism for the quantum protocol vulnerability in CVE-2099-99999.")
        res = rag_chain.run(req)
        self.assertTrue(res.insufficient_evidence)
        self.assertEqual(res.answer, "Insufficient verified intelligence in the knowledge base")
        self.assertEqual(len(res.cve_ids), 0)
        self.assertEqual(len(res.citations), 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
