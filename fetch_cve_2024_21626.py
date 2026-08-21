import requests
import json
from datetime import datetime, timezone
from backend.app.rag.vectorstore import vector_store

# Fetch CVE-2024-21626 directly from NVD API 2.0
url = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2024-21626"
print(f"Fetching {url}...")
res = requests.get(url, headers={"User-Agent": "AEGIS-Sentinel/0.1.0"}, timeout=30)
if res.status_code == 200:
    data = res.json()
    vulns = data.get("vulnerabilities", [])
    if vulns:
        cve = vulns[0].get("cve", {})
        cve_id = cve.get("id")
        desc = next((d.get("value") for d in cve.get("descriptions", []) if d.get("lang") == "en"), "")
        metrics = cve.get("metrics", {})
        cvss_data = {}
        if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
            cvss_data = metrics["cvssMetricV31"][0].get("cvssData", {})
        score = cvss_data.get("baseScore", 8.6)
        sev = cvss_data.get("baseSeverity", "HIGH")
        vector = cvss_data.get("vectorString", "CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:H")

        content = (
            f"CVE Record: {cve_id}\n"
            f"Title: runc Container Breakout via Leaked File Descriptor\n"
            f"CVSS v3.1 Score: {score} ({sev})\n"
            f"CVSS Vector: {vector}\n"
            f"Affected Component: runc <= 1.1.11, Docker, Kubernetes\n"
            f"Description: {desc}\n"
            f"Impact: An attacker can leverage leaked file descriptors to gain host filesystem access and escape container isolation (MITRE T1611)."
        )
        now_iso = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": f"nvd::{cve_id}",
            "doc_id": cve_id,
            "source": "nvd",
            "source_url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            "fetched_at": now_iso,
            "title": f"{cve_id} - runc Container Breakout (CVSS {score})",
            "content": content,
            "metadata": {
                "doc_id": cve_id,
                "source": "nvd",
                "source_url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                "fetched_at": now_iso,
                "title": f"{cve_id} - runc Container Breakout",
                "severity": str(sev),
                "score": str(score),
                "vector": str(vector),
                "tags": "nvd,cve,container,runc,escape,t1611"
            }
        }
        vector_store.upsert_documents([doc], source="nvd")
        print(f"[SUCCESS] Ingested live {cve_id} into ChromaDB.")
else:
    print(f"Error fetching from NVD: {res.status_code}")
