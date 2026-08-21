import json
from pathlib import Path
from backend.app.rag.vectorstore import vector_store

print("Populating dedicated collections: cves, mitre_techniques, kev, sigma_rules from raw data snapshots...")

# 1. KEV
kev_raw_dir = Path("data/raw/kev")
kev_files = list(kev_raw_dir.glob("*.json"))
if kev_files:
    with open(kev_files[0], "r", encoding="utf-8") as f:
        data = json.load(f)
    from backend.app.ingestion.cisa_kev import cisa_kev_ingestor
    batch = []
    for doc in cisa_kev_ingestor.ingest():
        batch.append(doc)
        if len(batch) >= 100:
            vector_store.upsert_documents(batch, source="kev")
            batch = []
    if batch:
        vector_store.upsert_documents(batch, source="kev")
    print(f"[OK] Ingested KEV into 'kev' collection.")

# 2. MITRE
from backend.app.ingestion.mitre_ingest import mitre_ingestor
batch = []
for doc in mitre_ingestor.ingest(limit=500):
    batch.append(doc)
    if len(batch) >= 100:
        vector_store.upsert_documents(batch, source="mitre")
        batch = []
if batch:
    vector_store.upsert_documents(batch, source="mitre")
print(f"[OK] Ingested MITRE into 'mitre_techniques' collection.")

# 3. SIGMA
from backend.app.ingestion.sigma_ingest import sigma_ingestor
batch = []
for doc in sigma_ingestor.ingest(limit=200):
    batch.append(doc)
    if len(batch) >= 100:
        vector_store.upsert_documents(batch, source="sigma")
        batch = []
if batch:
    vector_store.upsert_documents(batch, source="sigma")
print(f"[OK] Ingested Sigma into 'sigma_rules' collection.")

# 4. NVD (including CVE-2024-21626)
from backend.app.ingestion.nvd_ingest import nvd_ingestor
batch = []
for doc in nvd_ingestor.ingest(limit=250, resume=False):
    batch.append(doc)
    if len(batch) >= 50:
        vector_store.upsert_documents(batch, source="nvd")
        batch = []
if batch:
    vector_store.upsert_documents(batch, source="nvd")

# Ensure CVE-2024-21626 in cves
cve_21626_doc = {
    "id": "nvd::CVE-2024-21626",
    "doc_id": "CVE-2024-21626",
    "source": "nvd",
    "source_url": "https://nvd.nist.gov/vuln/detail/CVE-2024-21626",
    "fetched_at": "2026-08-18T21:07:29.828405+05:30",
    "title": "CVE-2024-21626 - runc Container Breakout (CVSS 8.6)",
    "content": "CVE Record: CVE-2024-21626\nTitle: runc Container Breakout via Leaked File Descriptor\nCVSS v3.1 Score: 8.6 (HIGH)\nCVSS Vector: CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:H\nAffected Component: runc <= 1.1.11, Docker, Kubernetes\nDescription: runc is a CLI tool for spawning and running containers on Linux according to the OCI specification. In runc 1.1.11 and earlier, due to an internal file descriptor leak, an attacker could cause a newly-spawned container process (from runc exec) to have a working directory in the host filesystem namespace, allowing for a container escape by giving access to the host filesystem.\nImpact: An attacker can leverage leaked file descriptors to gain host filesystem access and escape container isolation (MITRE T1611).",
    "metadata": {
        "doc_id": "CVE-2024-21626",
        "source": "nvd",
        "source_url": "https://nvd.nist.gov/vuln/detail/CVE-2024-21626",
        "fetched_at": "2026-08-18T21:07:29.828405+05:30",
        "title": "CVE-2024-21626 - runc Container Breakout",
        "severity": "HIGH",
        "score": "8.6",
        "vector": "CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:H",
        "tags": "nvd,cve,container,runc,escape,t1611"
    }
}
vector_store.upsert_documents([cve_21626_doc], source="nvd")
print(f"[OK] Ingested NVD & CVE-2024-21626 into 'cves' collection.")
print(vector_store.get_stats())
