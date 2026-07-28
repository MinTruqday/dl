import asyncio
import json
import os
import shutil
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = "http://127.0.0.1:8000"
SECRET_KEY = os.environ["SECRET_KEY"]
ADMIN_ID = f"tiny-finetune-admin-{uuid.uuid4()}"
SESSION_ID = str(uuid.uuid4())

def call(method, path, token, body=None):
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())

async def main():
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    cache = redis.from_url(os.environ["REDIS_URI"], decode_responses=True)
    agentic = mongo[os.getenv("AGENTIC_AI_DB_NAME", "doclib_agentic_ai")]
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": f"{ADMIN_ID}@doclib.local",
            "uid": ADMIN_ID,
            "sid": SESSION_ID,
            "role": "admin",
            "ai_tier": "PREMIUM",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    dataset_id = None
    job_id = None
    artifact_paths = []
    try:
        await cache.sadd(f"user_sessions:{ADMIN_ID}", SESSION_ID)
        status, dataset = call(
            "POST",
            "/tinh-chinh/tap-du-lieu",
            token,
            {"name": "Tiny model integration", "source": "manual"},
        )
        assert status == 200, dataset
        dataset_id = dataset["_id"]
        samples = [
            {
                "instruction": f"Return token {index}",
                "input": "",
                "output": f"token {index}",
            }
            for index in range(10)
        ]
        status, added = call(
            "POST",
            f"/tinh-chinh/tap-du-lieu/{dataset_id}/mau-thu",
            token,
            {"samples": samples},
        )
        assert status == 200 and added["total"] == 10, added
        status, job = call(
            "POST",
            "/tinh-chinh/tien-trinh",
            token,
            {
                "dataset_id": dataset_id,
                "job_name": "Tiny model integration",
                "base_model": "hf-internal-testing/tiny-random-LlamaForCausalLM",
                "epochs": 1,
                "batch_size": 2,
                "lora_rank": 4,
                "lora_alpha": 8,
            },
        )
        assert status == 200 and job.get("_id"), job
        job_id = job["_id"]
        status, started = call(
            "POST",
            f"/tinh-chinh/tien-trinh/{job_id}/bat-dau",
            token,
        )
        assert status == 200 and started["status"] == "started", started
        deadline = time.monotonic() + 240
        while time.monotonic() < deadline:
            status, current = call(
                "GET",
                f"/tinh-chinh/tien-trinh/{job_id}",
                token,
            )
            assert status == 200, current
            if current["status"] in {"completed", "failed", "cancelled"}:
                break
            await asyncio.sleep(1)
        assert current["status"] == "completed", current
        for key in ["adapter_path", "merged_path"]:
            path = current.get(key)
            assert path and path.startswith("/var/lib/doclib/finetune/"), current
            assert os.path.exists(path), path
            artifact_paths.append(path)
        if current.get("gguf_path"):
            assert os.path.isfile(current["gguf_path"])
            artifact_paths.append(current["gguf_path"])
        print("tiny finetuning integration passed")
    finally:
        if job_id:
            await agentic.finetune_jobs.delete_one({"_id": job_id})
        if dataset_id:
            await agentic.finetune_samples.delete_many({"dataset_id": dataset_id})
            await agentic.finetune_datasets.delete_one({"_id": dataset_id})
        for path in artifact_paths:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.unlink(path)
        await cache.delete(f"user_sessions:{ADMIN_ID}")
        await cache.aclose()
        mongo.close()

asyncio.run(main())
