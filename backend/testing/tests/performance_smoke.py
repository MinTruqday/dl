import os
import statistics
import time

import httpx
import jwt


BASE_URL = os.getenv("TESTING_TEST_URL", "http://testing:8000")
HEADERS = {
    "Authorization": "Bearer "
    + jwt.encode(
        {"uid": "qa-lead-e2e", "sub": "qa-lead-e2e@test.local", "system_role": "USER"},
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )
}


def p95(values):
    return statistics.quantiles(values, n=100, method="inclusive")[94]


with httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=20) as client:
    projects = client.get("/kiem-thu/du-an")
    projects.raise_for_status()
    project_id = projects.json()["data"][0]["_id"]
    list_latencies = []
    search_latencies = []
    for _ in range(30):
        started = time.perf_counter()
        response = client.get(f"/kiem-thu/du-an/{project_id}/yeu-cau")
        response.raise_for_status()
        list_latencies.append(time.perf_counter() - started)
        started = time.perf_counter()
        response = client.post(f"/kiem-thu/du-an/{project_id}/tri-thuc/tim-kiem", json={"query": "phone validation", "artifact_types": [], "limit": 20})
        response.raise_for_status()
        search_latencies.append(time.perf_counter() - started)
    list_p95 = p95(list_latencies)
    search_p95 = p95(search_latencies)
    assert list_p95 < 0.5, f"List p95 {list_p95:.4f}s"
    assert search_p95 < 2, f"Search p95 {search_p95:.4f}s"
    print(f"performance smoke passed list_p95={list_p95:.4f}s search_p95={search_p95:.4f}s")
