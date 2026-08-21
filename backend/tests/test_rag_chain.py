import pytest
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.app.models.schemas import ChatRequest
from backend.app.rag.chain import rag_chain

def test_rag_chain_response_contract_shape():
    req = ChatRequest(query="Analyze Apache Log4j2 CVE-2021-44228 vulnerability and CISA KEV exploitation.")
    res = rag_chain.run(req)
    
    assert hasattr(res, "answer")
    assert hasattr(res, "cve_ids")
    assert hasattr(res, "cvss")
    assert hasattr(res, "mitre_techniques")
    assert hasattr(res, "cisa_kev")
    assert hasattr(res, "citations")
    assert hasattr(res, "guard")
    assert hasattr(res, "latency_ms")
    assert hasattr(res, "insufficient_evidence")
    
    assert res.insufficient_evidence == False
    assert len(res.citations) > 0
    assert "CVE-2021-44228" in res.cve_ids

def test_rag_chain_silence_invariant():
    req = ChatRequest(query="Explain the zero-day exploit mechanism for the quantum protocol vulnerability in CVE-2099-99999.")
    res = rag_chain.run(req)
    
    assert res.insufficient_evidence == True
    assert res.answer == "Insufficient verified intelligence in the knowledge base"
    assert len(res.cve_ids) == 0
    assert len(res.citations) == 0
