import json
import time
import urllib.request

def send_chat(query: str):
    req_data = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:8000/chat",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    start = time.perf_counter()
    with urllib.request.urlopen(req) as resp:
        duration_ms = (time.perf_counter() - start) * 1000.0
        data = json.loads(resp.read().decode("utf-8"))
        return data, duration_ms

print("=== Gate 1: Query CVE-2024-21626 ===")
res1, dur1 = send_chat("Is CVE-2024-21626 critical?")
print(json.dumps(res1, indent=2))

print("\n=== Gate 2: Query Fake CVE-2099-99999 ===")
res2, dur2 = send_chat("Tell me about CVE-2099-99999")
print(json.dumps(res2, indent=2))

print("\n=== Gate 4: 5-Run Latency Benchmark ===")
latencies = []
for i in range(1, 6):
    _, d = send_chat("Is CVE-2024-21626 critical?")
    latencies.append(d)
    print(f"Run {i}: {d:.2f}ms")

avg_lat = sum(latencies) / len(latencies)
max_lat = max(latencies)
print(f"\nBenchmark Results: Avg: {avg_lat:.2f}ms ({avg_lat/1000:.2f}s), Max: {max_lat:.2f}ms ({max_lat/1000:.2f}s)")
