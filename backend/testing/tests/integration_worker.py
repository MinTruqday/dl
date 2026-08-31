import os
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


with httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=20) as client:
    assert "/kiem-thu/noi-bo/tac-vu/{event}" in client.get("/openapi.json").json()["paths"]
    projects = client.get("/kiem-thu/du-an")
    projects.raise_for_status()
    project_id = projects.json()["data"][0]["_id"]
    marker = str(time.time_ns())
    internal = client.post(
        "/kiem-thu/noi-bo/tac-vu/document.parse.requested",
        headers={
            "X-Internal-Token": os.environ["SECRET_KEY"],
            "X-Requester-Id": "qa-lead-e2e",
            "X-Requester-Email": "qa-lead-e2e@test.local",
        },
        json={
            "job_id": f"DIRECT-{marker}",
            "project_id": project_id,
            "artifact_version_id": f"DOC-{marker}",
            "model_version": "document-parser-v1",
            "payload": {"document_id": f"DOC-{marker}"},
        },
    )
    assert internal.status_code == 200, internal.text
    assert internal.json()["data"]["status"] == "COMPLETED"
    payload = {"event": "duplicate.scan.requested", "artifact_version_id": f"ART-{marker}", "model_version": "duplicate-v1", "payload": {}}
    queued = client.post(f"/kiem-thu/du-an/{project_id}/tac-vu", json=payload)
    assert queued.status_code == 202, queued.text
    first = queued.json()["data"]
    duplicate = client.post(f"/kiem-thu/du-an/{project_id}/tac-vu", json=payload)
    assert duplicate.status_code == 202, duplicate.text
    assert duplicate.json()["data"]["job_id"] == first["job_id"]
    completed = None
    for _ in range(40):
        response = client.get(f"/kiem-thu/tac-vu/{first['job_id']}")
        response.raise_for_status()
        completed = response.json()["data"]
        if completed["status"] in {"completed", "failed"}:
            break
        time.sleep(0.25)
    assert completed["status"] == "completed", completed
    assert completed["project_id"] == project_id
    print(f"qa worker integration passed {first['job_id']}")
