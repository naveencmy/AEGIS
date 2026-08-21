# Contributing to AEGIS

Thank you for your interest in contributing to **AEGIS** (Autonomous Enterprise Guard for Intelligence & Sovereignty).

AEGIS is built to enterprise engineering standards. We welcome contributions from security engineers, data scientists, and developers worldwide to improve air-gapped threat intelligence, detection rule parsing, and sovereign AI reasoning.

---

## 🧭 Core Architectural Invariants

Every contribution **must** respect the 4 sovereign invariants of AEGIS:

1. **Zero Hardcoded Data**: All intelligence must be dynamically ingested from authoritative security feeds (NIST NVD, CISA KEV, MITRE ATT&CK, SigmaHQ) or queried from the vector store. No synthetic or hardcoded CVE data.
2. **Citation or Silence Contract**: The system must never guess. If intelligence is absent, it must output explicit insufficient evidence status.
3. **Sovereign Hallucination Guard**: All extracted entity IDs must be validated against verified local vector records before presentation.
4. **Air-Gapped Local Inference**: Core reasoning and embeddings must run on-premise without requiring outbound cloud API calls.

---

## 🛠️ Development Environment Setup

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm 9+**
- **Git**
- **Ollama** with `mistral:7b-instruct-q4_K_M` model:
  ```bash
  ollama pull mistral:7b-instruct-q4_K_M
  ```

### 2. Fork and Clone
```bash
git clone https://github.com/<your-username>/AEGIS_V0.1.git
cd AEGIS_V0.1
```

### 3. Backend Setup
```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

pip install --upgrade pip
pip install -r backend/requirements.txt
pip install pytest pytest-asyncio flake8 httpx
```

### 4. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### 5. Running the Local Stack
```bash
# Terminal 1: Backend
$env:PYTHONPATH = "$PWD;$PWD/backend"
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

## 🌿 Branching & Git Commit Conventions

We enforce the **[Conventional Commits](https://www.conventionalcommits.org/)** standard for clean changelogs:

| Prefix | Description | Example |
|---|---|---|
| `feat:` | A new feature or capability | `feat(ingest): add STIX 2.1 ICS attack pattern parser` |
| `fix:` | A bug fix | `fix(guard): prevent regex false positives on hyphenated IDs` |
| `docs:` | Documentation changes only | `docs(readme): add Kubernetes Helm deployment guide` |
| `test:` | Adding or updating unit/integration tests | `test(eval): add 5 new KEV exploit evaluation queries` |
| `perf:` | Code change that improves performance | `perf(embeddings): optimize ONNX runtime batch size` |
| `refactor:` | Code change that neither fixes a bug nor adds a feature | `refactor(chain): streamline RAG context serialization` |

### Branch Naming
- Features: `feat/<short-description>` (e.g. `feat/cisa-kev-enrichment`)
- Fixes: `fix/<short-description>` (e.g. `fix/cors-headers-proxy`)

---

## 🧪 Testing & Validation Requirements

All pull requests must pass the automated verification suite before review:

### 1. Run Unit & Integration Tests
```bash
pytest backend/tests/ -v
```

### 2. Run the Sovereign Hallucination Guard Tests
```bash
pytest backend/tests/test_guard.py -v
```

### 3. Run the 20-Query Sovereign Evaluation Benchmark
```bash
python backend/tests/run_eval_suite.py
```
*Target Thresholds:*
- **Retrieval Accuracy**: $\ge 80\%$
- **Citation Presence**: $100\%$
- **Hallucinated Entity IDs**: $0$
- **Average Query Latency**: $< 15\text{s}$

### 4. Frontend Build Check
```bash
cd frontend
npm run build
cd ..
```

---

## 📐 Code Style & Best Practices

### Python (Backend)
- Follow **PEP 8** guidelines.
- Use explicit type annotations on all function signatures (`pydantic` models for schemas).
- Write Google-style docstrings for public classes, methods, and ingestion pipelines.
- Ensure all exceptions are properly caught and logged with structured loggers (`logger = logging.getLogger("aegis.module")`).

### JavaScript / React (Frontend)
- Use functional React components with hooks.
- Keep the dark theme locked (`#0A0E17` background, `#6366F1` indigo, `#06B6D4` cyan accents).
- Ensure all citation cards have working links, timestamps, and accessible labels.

---

## 📋 Pull Request (PR) Checklist

Before opening a PR, ensure that:
- [ ] Your code complies with the 4 Sovereign Invariants.
- [ ] All unit and integration tests pass cleanly (`pytest backend/tests/`).
- [ ] No hardcoded tokens, API keys, private IPs, or credentials are committed.
- [ ] `.gitignore` rules are respected (no cache, `.venv`, or temporary test dumps committed).
- [ ] You have added tests for any new features or bug fixes.
- [ ] Documentation and docstrings have been updated accordingly.

---

## 🔒 Security Vulnerability Disclosure

Security is fundamental to AEGIS. If you discover a vulnerability or security issue within AEGIS itself, please **do not** open a public GitHub issue.

Please report security issues privately to:
📧 `security@aegis-sentinel.internal` (or reach out via GitHub Security Advisories).

We will acknowledge reports within 24 hours and coordinate a fix and release.

---

## 📄 License

By contributing to AEGIS, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
