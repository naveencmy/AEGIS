import sys
import os
import time
import re

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.config import settings
from backend.app.models.schemas import QueryRequest
from backend.app.ingestion.pipeline import pipeline_manager
from backend.app.rag.vector_store import vector_store
from backend.app.rag.engine import rag_engine
from backend.app.rag.hallucination_guard import hallucination_guard

def log_test(title: str):
    print(f"\n=================================================================")
    print(f"  TEST: {title}")
    print(f"=================================================================")

def assert_true(cond: bool, msg: str):
    if cond:
        print(f"  [PASS] {msg}")
    else:
        print(f"  [FAIL] {msg}")
        raise AssertionError(msg)

def run_all_verifications():
    print("\n" + "#"*65)
    print("  AEGIS MVP v0.1 — End-to-End Automated Verification Suite")
    print("#"*65)
    
    # -------------------------------------------------------------
    # 1. Ingestion & Real Data Test
    # -------------------------------------------------------------
    log_test("1. Live Threat Intelligence Ingestion (Real Data)")
    print("Ingesting initial live records from CISA KEV, MITRE ATT&CK, Sigma, and NVD...")
    
    cisa_count = pipeline_manager.run_source_sync(source="cisa_kev", limit=25, resume=False)
    assert_true(cisa_count > 0, f"CISA KEV ingested {cisa_count} live records")

    mitre_count = pipeline_manager.run_source_sync(source="mitre", limit=25, resume=False)
    assert_true(mitre_count > 0, f"MITRE ATT&CK ingested {mitre_count} live techniques")

    sigma_count = pipeline_manager.run_source_sync(source="sigma", limit=25, resume=False)
    assert_true(sigma_count > 0, f"SigmaHQ ingested {sigma_count} live detection rules")

    nvd_count = pipeline_manager.run_source_sync(source="nvd", limit=5, resume=False)
    assert_true(nvd_count > 0, f"NVD API 2.0 ingested {nvd_count} live CVE records (rate-limited)")

    # -------------------------------------------------------------
    # 2. Provenance Metadata Compliance Test
    # -------------------------------------------------------------
    log_test("2. Provenance Metadata Verification")
    stats = vector_store.get_stats()
    assert_true(stats["total"] >= (cisa_count + mitre_count + sigma_count + nvd_count), f"Total ChromaDB records >= {stats['total']}")
    
    sample_docs = vector_store.list_threat_intel(limit=10)
    for doc in sample_docs:
        meta = doc.get("metadata", {})
        doc_id = meta.get("doc_id")
        source = meta.get("source")
        source_url = meta.get("source_url")
        fetched_at = meta.get("fetched_at")
        
        assert_true(bool(doc_id), f"Record has doc_id: {doc_id}")
        assert_true(source in ["cisa_kev", "mitre", "sigma", "nvd"], f"Record source '{source}' is valid")
        assert_true(bool(source_url) and source_url.startswith("http"), f"Record source_url is valid canonical URL: {source_url}")
        assert_true(bool(fetched_at) and "T" in fetched_at, f"Record fetched_at is ISO-8601 timestamp: {fetched_at}")
    
    # -------------------------------------------------------------
    # 3. Citation or Silence Invariant Test
    # -------------------------------------------------------------
    log_test("3. Invariant 4: Citation or Silence Gating")
    # Query a totally fictitious concept that does not exist in any threat database
    bogus_query = "What is the zero-day exploit mechanism for the Klingon subspace protocol in CVE-2099-88888?"
    print(f"Querying out-of-distribution fictitious topic: '{bogus_query}'")
    silence_res = rag_engine.query(QueryRequest(query=bogus_query))
    
    print(f"Response: '{silence_res.answer}'")
    print(f"Silence triggered: {silence_res.silence_triggered}")
    assert_true(silence_res.silence_triggered == True, "Silence was triggered for unindexed fictitious query")
    assert_true(settings.SILENCE_RESPONSE in silence_res.answer, f"Answer strictly equals '{settings.SILENCE_RESPONSE}'")
    assert_true(len(silence_res.citations) == 0, "No false citations returned")

    # -------------------------------------------------------------
    # 4. Hallucination Guard Test
    # -------------------------------------------------------------
    log_test("4. Invariant 5: Post-Generation Hallucination Guard")
    # Fabricate a response string that mentions both a valid ID (from CISA KEV or MITRE) and an unindexed fake ID
    sample_valid_cve = sample_docs[0].get("doc_id")
    fake_cve = "CVE-2099-77777"
    fake_mitre = "T9999.999"
    
    test_llm_output = (
        f"Based on intelligence, {sample_valid_cve} is active in campaigns. "
        f"Additionally, attackers leverage {fake_cve} alongside technique {fake_mitre} for execution."
    )
    
    print(f"Input text to Hallucination Guard:\n{test_llm_output}")
    guard_res = hallucination_guard.validate_and_sanitize(test_llm_output, cited_doc_ids={sample_valid_cve})
    
    print(f"Sanitized output:\n{guard_res.sanitized_text}")
    print(f"Verified IDs: {guard_res.verified_ids}")
    print(f"Hallucinations Detected: {guard_res.hallucinations_detected}")
    print(f"Unverified claims removed flag: {guard_res.unverified_claims_removed}")
    
    assert_true(fake_cve in guard_res.hallucinations_detected, f"Detected fake CVE {fake_cve}")
    assert_true(fake_mitre in guard_res.hallucinations_detected, f"Detected fake MITRE ID {fake_mitre}")
    assert_true(guard_res.unverified_claims_removed == True, "unverified_claims_removed flag is True")
    assert_true(fake_cve not in guard_res.sanitized_text or "UNVERIFIED" in guard_res.sanitized_text, "Fake CVE was sanitized/stripped")

    # -------------------------------------------------------------
    # 5. Determinism Test
    # -------------------------------------------------------------
    log_test("5. Invariant 7: Determinism with Fixed Seed (Temp=0.1, Seed=42)")
    # Query a known indexed topic
    test_query = f"Provide threat intelligence details and mitigation for {sample_valid_cve}."
    print(f"Running deterministic query 1: '{test_query}'")
    run1 = rag_engine.query(QueryRequest(query=test_query))
    
    print(f"Running deterministic query 2: '{test_query}'")
    run2 = rag_engine.query(QueryRequest(query=test_query))
    
    assert_true(run1.answer == run2.answer, "Both identical queries produced 100% deterministic identical answers")
    assert_true(len(run1.citations) == len(run2.citations), "Citations count matches across runs")
    print(f"  Deterministic answer sample:\n  {run1.answer[:200]}...")

    # -------------------------------------------------------------
    # 6. Summary Report
    # -------------------------------------------------------------
    print("\n" + "="*65)
    print("  ALL 5 CORE VERIFICATION SUITES PASSED (100% COMPLIANCE)")
    print("  - Real Data Ingestion: PASSED")
    print("  - Provenance Metadata: PASSED")
    print("  - Citation or Silence Gating: PASSED")
    print("  - Hallucination Guard Extraction & Stripping: PASSED")
    print("  - Determinism (Seed 42 / Temp 0.1): PASSED")
    print("="*65 + "\n")

if __name__ == "__main__":
    run_all_verifications()
