import os
import time

import httpx


BASE_URL = os.getenv("QA_TEST_URL", "http://qa:8000")
HEADERS = {"x-test-user-id": "qa-lead-e2e", "x-test-user-role": "author"}


with httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=20) as client:
    projects = client.get("/api/qa/projects")
    projects.raise_for_status()
    project_id = projects.json()["data"][0]["_id"]
    marker = str(time.time_ns())
    payload = {"event": "duplicate.scan.requested", "artifact_version_id": f"ART-{marker}", "model_version": "duplicate-v1", "payload": {}}
    queued = client.post(f"/api/qa/projects/{project_id}/jobs", json=payload)
    assert queued.status_code == 202, queued.text
    first = queued.json()["data"]
    duplicate = client.post(f"/api/qa/projects/{project_id}/jobs", json=payload)
    assert duplicate.status_code == 202, duplicate.text
    assert duplicate.json()["data"]["job_id"] == first["job_id"]
    completed = None
    for _ in range(40):
        response = client.get(f"/api/qa/jobs/{first['job_id']}")
        response.raise_for_status()
        completed = response.json()["data"]
        if completed["status"] in {"completed", "failed"}:
            break
        time.sleep(0.25)
    assert completed["status"] == "completed", completed
    assert completed["project_id"] == project_id
    print(f"qa worker integration passed {first['job_id']}")
