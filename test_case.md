# AEGIS MVP v0.1 — End-User Scenarios, Test Cases & Evaluation Benchmark Suite

This document defines the comprehensive test suite and **real-world end-user workflow examples** for evaluating **AEGIS MVP v0.1**: a sovereign, on-premise, citation-native RAG cybersecurity co-pilot.

---

## 👥 Section 1: End-User Personas & Real-World Usage Examples

### Scenario A: SOC Analyst (Vulnerability Triage & CISA KEV Exploitation Check)
> **Goal**: A Tier-2 SOC Analyst needs to quickly verify if an observed CVE is actively exploited in the wild, check its CVSS severity, and determine mandatory remediation deadlines.

#### Step-by-Step End-User Workflow:
1. Open the AEGIS Web UI (`http://localhost:5173`).
2. In the **Co-Pilot Reasoning** view, type:
   > *"Analyze Apache Log4j2 CVE-2021-44228: CVSS metrics, CISA KEV ransomware exploitation, and remediation actions."*
3. Press **[Query]** (or click the **Log4Shell** preset card).
4. **What the End User Sees**:
   - **Executive Assessment**: Grounded breakdown of CVE-2021-44228.
   - **Verified Entity Badges**: `[CVE-2021-44228]` with confidence score (e.g., `94%`).
   - **Provenance Citation Chips**: Clickable pills `[CVE-2021-44228]` and `[CISA KEV]`.
5. **Interactive Action**:
   - The analyst clicks the `[CVE-2021-44228]` citation chip.
   - A slide-out **Provenance Drawer** opens, showing the canonical link to `https://nvd.nist.gov/vuln/detail/CVE-2021-44228`, the exact ISO-8601 UTC timestamp of ingestion, and the raw ingested payload.
   - The analyst clicks **[Copy Payload]** to paste the evidence directly into their SIEM/ticketing system.

---

### Scenario B: Threat Hunter (Adversary TTP & MITRE ATT&CK Mapping)
> **Goal**: A Threat Hunter is investigating suspicious PowerShell process trees and needs detection guidance and technique IDs.

#### Step-by-Step End-User Workflow:
1. In the **Co-Pilot Reasoning** tab, type:
   > *"What are the tactics, platforms, and detection strategies for MITRE ATT&CK technique T1059.001 (Command and Scripting Interpreter: PowerShell)?"*
2. **What the End User Sees**:
   - **Tactics**: `Execution`
   - **Platforms**: `Windows, Linux, macOS`
   - **Detection Guidance**: Grounded guidance citing `[T1059.001]`.
   - **Hallucination Guard Badge**: Displays `✓ T1059.001 (Verified in Local ChromaDB Store)`.

---

### Scenario C: Detection Engineer (Sigma Rule Extraction & Threat Matrix)
> **Goal**: A Detection Engineer wants to browse indexed Sigma rules and create SIEM alerting rules for script execution.

#### Step-by-Step End-User Workflow:
1. Click the **Threat Explorer** tab in the top navigation bar.
2. In the search bar, type `PowerShell` and click the **[SigmaHQ Rules]** filter pill.
3. The UI displays matching Sigma detection cards showing rule IDs, threat level (e.g., `HIGH`, `CRITICAL`), and canonical GitHub repository links.
4. Click **[View Provenance]** on any rule to view the raw YAML detection logic and condition statements.

---

### Scenario D: Security Auditor / CISO (Zero-Hallucination & Air-Gap Audit)
> **Goal**: A Security Auditor wants to test if the AI will hallucinate fake CVEs or make up security advice when given a fake topic.

#### Step-by-Step End-User Workflow:
1. In the Co-Pilot view, enter a fictitious query:
   > *"Explain the zero-day exploit mechanism for the Klingon subspace protocol in CVE-2099-88888."*
2. **What the End User Sees**:
   - **Silence Alert Banner (Invariant 4)**:
     > ⚠️ **INVARIANT 4 ENFORCED (CITATION OR SILENCE)**:
     > *"Insufficient verified intelligence in the knowledge base"*
   - **Hallucination Guard Audit**:
     - Fictitious CVE `CVE-2099-88888` is recognized as unverified and blocked from generation.
     - Zero fake citations are returned.

---

## 📋 Section 2: Evaluation Summary Matrix

| Test Case ID | Target Persona | Test Category | Target Invariant / Feature | Expected Outcome | Status |
|---|---|---|---|---|---|
| **TC-INV-01** | Data Engineer | Invariant 1 | Real Data Ingestion (Zero Synthetic Data) | Pulls live records from NIST NVD, MITRE ATT&CK STIX 2.1, CISA KEV, and SigmaHQ | ✅ PASS |
| **TC-INV-02** | Security Auditor | Invariant 2 | Provenance Metadata Compliance | 100% of ChromaDB documents contain `{source, source_url, fetched_at, doc_id}` | ✅ PASS |
| **TC-INV-03** | CISO | Invariant 3 | Zero Cloud Dependencies / Air-Gap | Operates locally with Mistral-7B Q4, local ONNX/Torch vectors, zero cloud LLM keys | ✅ PASS |
| **TC-INV-04** | Security Auditor | Invariant 4 | Citation or Silence Gating | Out-of-distribution/fake CVE queries return strict silence string rather than guessing | ✅ PASS |
| **TC-INV-05** | Security Auditor | Invariant 5 | Post-Generation Hallucination Guard | Extracts CVE & MITRE IDs, queries DB, strips fake IDs, sets `unverified_claims_removed: true` | ✅ PASS |
| **TC-INV-06** | System Admin | Invariant 6 | NVD API Rate Limit & Checkpoint | Enforces 5 req/30s throttling (6.2s delay), saves checkpoint to disk | ✅ PASS |
| **TC-INV-07** | Judge / Evaluator | Invariant 7 | Deterministic Demo (Seed 42 / Temp 0.1) | Identical queries generate 100% bit-exact responses across runs | ✅ PASS |
| **TC-API-01** | Developer | Backend API | `/health` & `/api/v1/system` | Returns sovereign health status and telemetry | ✅ PASS |
| **TC-API-02** | SOC Analyst | Backend API | `/api/v1/query` & Grounding | Returns grounded answer with structured citation items and score meters | ✅ PASS |
| **TC-UI-01** | SOC Analyst | Frontend UI | Obsidian Cyber Interface & Badges | Displays `#0A0E17` obsidian theme, live vector counts, and sovereign air-gap badges | ✅ PASS |
| **TC-UI-02** | SOC Analyst | Frontend UI | Interactive Provenance Drawers | Clicking `[CVE-...]` or `[T...]` opens drawer with canonical source URLs and payload | ✅ PASS |

---

## 🧪 Section 3: Core Invariant Test Cases

### TC-INV-01: Live Threat Intelligence Ingestion (Zero Fallbacks)
- **Objective**: Ensure all threat intelligence comes from live upstream APIs and repositories. No synthetic or hardcoded fallback data.
- **Preconditions**: Internet connectivity to NIST NVD, MITRE GitHub repo, CISA feed, and SigmaHQ repo.
- **Test Steps**:
  1. Execute CLI ingestion tool with record limit:
     ```powershell
     python backend/run_ingest.py --source all --limit 20
     ```
  2. Inspect output logs to verify live HTTP requests and payload parsing.
- **Expected Result**:
  - CISA KEV pulls live JSON from `cisa.gov` (1,600+ records available).
  - MITRE ATT&CK parses live STIX 2.1 JSON from `github.com/mitre/cti` (690+ techniques available).
  - SigmaHQ parses live YAML rule archive from `github.com/SigmaHQ/sigma` (3,300+ rules available).
  - NVD API 2.0 requests paginated CVE records from `services.nvd.nist.gov`.
  - ChromaDB upserts records with positive confirmation.

---

### TC-INV-02: Provenance Metadata Verification
- **Objective**: Validate that every document stored in ChromaDB contains complete, non-null provenance metadata.
- **Preconditions**: Ingestion completed.
- **Test Steps**:
  1. Query database records via API or Python script:
     ```python
     from backend.app.rag.vector_store import vector_store
     docs = vector_store.list_threat_intel(limit=50)
     for d in docs:
         meta = d["metadata"]
         assert meta["source"] in ["nvd", "mitre", "cisa_kev", "sigma"]
         assert meta["source_url"].startswith("http")
         assert "T" in meta["fetched_at"]
         assert len(meta["doc_id"]) > 0
     ```
- **Expected Result**:
  - 100% of inspected documents contain `source`, `source_url`, `fetched_at` (ISO-8601 UTC timestamp), and canonical `doc_id`.

---

### TC-INV-03: Zero Cloud Dependencies & Air-Gap Compliance
- **Objective**: Prove the system operates locally without cloud LLM/embedding API keys (e.g., OpenAI, Anthropic, Google Vertex).
- **Preconditions**: Local backend running.
- **Test Steps**:
  1. Check source code and environment variables for external cloud keys:
     ```powershell
     Select-String -Path "backend\**\*.py" -Pattern "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "api.openai.com"
     ```
  2. Query `GET http://localhost:8000/api/v1/system`.
- **Expected Result**:
  - 0 external cloud API keys found in codebase.
  - Telemetry confirms `sovereign_mode: AIR-GAPPED / ON-PREMISE` and `cloud_dependencies: NONE`.

---

### TC-INV-04: Invariant 4 — "Citation or Silence" Gating
- **Objective**: Verify that AEGIS refuses to speculate or guess when asked about unindexed, ambiguous, or fictitious vulnerabilities.
- **Preconditions**: ChromaDB initialized.
- **Test Steps**:
  1. Send a fictitious query via API or Chat UI:
     ```json
     POST /api/v1/query
     {
       "query": "What is the zero-day exploit mechanism for the Klingon subspace protocol in CVE-2099-88888?"
     }
     ```
- **Expected Result**:
  - `silence_triggered`: `true`
  - `answer`: `"Insufficient verified intelligence in the knowledge base"`
  - `citations`: `[]` (Empty list — zero hallucinated references).

---

### TC-INV-05: Invariant 5 — Post-Generation Hallucination Guard
- **Objective**: Verify that the Hallucination Guard extracts all CVE-IDs (`CVE-\d{4}-\d{4,7}`) and MITRE IDs (`T\d{4}(\.\d{3})?`) from LLM output, verifies them against ChromaDB, and sanitizes unknown claims.
- **Preconditions**: Vector store populated with valid records.
- **Test Steps**:
  1. Pass text containing both a real indexed CVE (e.g., `CVE-2021-44228`) and a fictitious CVE (`CVE-2099-77777`) and fake MITRE ID (`T9999.999`) to `hallucination_guard.validate_and_sanitize()`.
- **Expected Result**:
  - Real CVE is verified: `verified_ids: ["CVE-2021-44228"]`.
  - Fake IDs are detected: `hallucinations_detected: ["CVE-2099-77777", "T9999.999"]`.
  - `unverified_claims_removed`: `true`.
  - Output text replaces fake IDs with `[UNVERIFIED CLAIM REMOVED: ...]`.

---

### TC-INV-06: Invariant 6 — NVD API Rate Limit Throttle & Checkpoint Resumption
- **Objective**: Verify NVD 2.0 API rate limiting (max 5 requests per 30s) and disk checkpointing.
- **Preconditions**: Network connection to NIST.
- **Test Steps**:
  1. Run NVD ingestion with limit:
     ```powershell
     python backend/run_ingest.py --source nvd --limit 10
     ```
  2. Inspect time between HTTP requests in log output.
  3. Verify `backend/checkpoints/nvd_checkpoint.json` exists on disk.
- **Expected Result**:
  - Throttled pause of `>= 6.2s` between unauthenticated pagination requests.
  - Checkpoint file records `current_index` and `total_records`.
  - Re-running with `--resume` resumes from `current_index` without duplicate fetching.

---

### TC-INV-07: Invariant 7 — Determinism with Fixed Seed
- **Objective**: Verify reproducible, deterministic inference (`temperature=0.1`, `top_p=0.9`, `seed=42`).
- **Test Steps**:
  1. Execute identical query twice against `/api/v1/query`:
     ```powershell
     $body = '{"query":"Provide threat intelligence details and mitigation for CVE-2021-44228."}'
     $res1 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/query" -Method Post -Body $body -ContentType "application/json"
     $res2 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/query" -Method Post -Body $body -ContentType "application/json"
     $res1.answer -eq $res2.answer
     ```
- **Expected Result**:
  - `$res1.answer` and `$res2.answer` are 100% bit-exact identical.

---

## 🚀 One-Step Automated Verification Command

To run the entire test suite and produce an automated audit report:

```powershell
python verify_aegis.py
```
