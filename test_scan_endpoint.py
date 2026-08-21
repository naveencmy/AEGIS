import json
import httpx

with open("backend/tests/data/scan.xml", "rb") as f:
    files = {"file": ("scan.xml", f, "application/xml")}
    with httpx.Client(timeout=30.0) as client:
        resp = client.post("http://localhost:8000/scan", files=files)
        print(f"Status Code: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2))
