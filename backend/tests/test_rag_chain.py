import unittest
from backend.app.models.schemas import ChatRequest
from backend.app.rag.chain import rag_chain


class TestRagChain(unittest.TestCase):
    def test_rag_chain_response_contract_shape(self):
        req = ChatRequest(query="Analyze Apache Log4j2 CVE-2021-44228 vulnerability and CISA KEV exploitation.")
        res = rag_chain.run(req)
        
        self.assertTrue(hasattr(res, "answer"))
        self.assertTrue(hasattr(res, "cve_ids"))
        self.assertTrue(hasattr(res, "cvss"))
        self.assertTrue(hasattr(res, "mitre_techniques"))
        self.assertTrue(hasattr(res, "cisa_kev"))
        self.assertTrue(hasattr(res, "citations"))
        self.assertTrue(hasattr(res, "guard"))
        self.assertTrue(hasattr(res, "latency_ms"))
        self.assertTrue(hasattr(res, "insufficient_evidence"))
        
        self.assertFalse(res.insufficient_evidence)
        self.assertGreater(len(res.citations), 0)
        self.assertIn("CVE-2021-44228", res.cve_ids)

    def test_rag_chain_silence_invariant(self):
        req = ChatRequest(query="Explain the zero-day exploit mechanism for the quantum protocol vulnerability in CVE-2099-99999.")
        res = rag_chain.run(req)
        
        self.assertTrue(res.insufficient_evidence)
        self.assertEqual(res.answer, "Insufficient verified intelligence in the knowledge base")
        self.assertEqual(len(res.cve_ids), 0)
        self.assertEqual(len(res.citations), 0)


if __name__ == "__main__":
    unittest.main()
