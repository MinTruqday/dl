from fastapi import APIRouter, HTTPException
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings
from datetime import datetime, timezone
from uuid6 import uuid7
from datasets import Dataset
import httpx
import json
import asyncio
import threading

router = APIRouter(prefix="/finetune")
active_jobs = {}

def get_db():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    return client.get_default_database()

async def report_progress(job_id: str, data: dict):
    db = get_db()
    update_fields = {}
    for key in ["progress", "current_epoch", "current_loss", "status", "adapter_path", "merged_model_name", "error_message", "best_loss"]:
        if key in data:
            update_fields[key] = data[key]
    if data.get("status") == "completed":
        update_fields["completed_at"] = datetime.now(timezone.utc)
        update_fields["progress"] = 100.0
    if "loss" in data:
        log_entry = {"epoch": data.get("current_epoch", 0), "loss": data["loss"], "timestamp": datetime.now(timezone.utc).isoformat()}
        await db["finetune_jobs"].update_one({"_id": job_id}, {"$push": {"training_log": log_entry}})
        job = await db["finetune_jobs"].find_one({"_id": job_id})
        if job:
            best = job.get("best_loss")
            if best is None or data["loss"] < best:
                update_fields["best_loss"] = data["loss"]
    if update_fields:
        await db["finetune_jobs"].update_one({"_id": job_id}, {"$set": update_fields})

def _run_training_sync(job_id: str, config: dict, loop):
    from src.training.engine import run_finetune_job

    async def _update(data):
        await report_progress(job_id, data)

    def sync_update(data):
        asyncio.run_coroutine_threadsafe(_update(data), loop)

    try:
        sync_update({"status": "running", "progress": 5})

        base_model_name = config.get("base_model", settings.LLAMA_MODEL)
        hf_token = getattr(settings, "HF_TOKEN", None)
        epochs = config.get("epochs", 3)
        batch_size = config.get("batch_size", 4)
        learning_rate = config.get("learning_rate", 2e-4)
        lora_rank = config.get("lora_rank", 16)
        lora_alpha = config.get("lora_alpha", 32)
        training_data = config.get("training_data", [])

        sync_update({"progress": 10, "status": "running"})
        result = run_finetune_job(job_id, config, sync_update)

        adapter_path = result.get("adapter_path", "")
        final_loss = result.get("final_loss", 0)
        merged_path = result.get("merged_path", "")
        
        sync_update({"progress": 98, "current_loss": round(final_loss, 6)})

        model_name = f"doclib-ft-{job_id[:8]}"

        merged_path = result.get("merged_path", "")
        gguf_path = result.get("gguf_path", "")

        sync_update({
            "status": "completed", "progress": 100,
            "current_loss": round(final_loss, 6),
            "best_loss": round(final_loss, 6),
            "merged_model_name": model_name,
            "adapter_path": adapter_path,
            "merged_path": merged_path,
            "gguf_path": gguf_path
        })

    except Exception as e:
        logger.error(f"Finetune training failed for job {job_id}: {e}")
        sync_update({"status": "failed", "error_message": str(e)})
    finally:
        active_jobs.pop(job_id, None)

@router.post("/dataset")
async def create_dataset(req: dict):
    db = get_db()
    doc = {
        "_id": str(uuid7()), "user_id": req.get("user_id"),
        "name": req.get("name"), "description": req.get("description", ""),
        "source": req.get("source", "manual"), "sample_count": 0,
        "status": "draft", "created_at": datetime.now(timezone.utc)
    }
    await db["finetune_datasets"].insert_one(doc)
    return doc

@router.get("/dataset")
async def list_datasets(user_id: str):
    return await get_db()["finetune_datasets"].find({"user_id": user_id}).sort("created_at", -1).to_list(length=100)

@router.get("/dataset/{dataset_id}")
async def get_dataset(dataset_id: str, user_id: str):
    doc = await get_db()["finetune_datasets"].find_one({"_id": dataset_id, "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tập dữ liệu.")
    return doc

@router.delete("/dataset/{dataset_id}")
async def delete_dataset(dataset_id: str, user_id: str):
    db = get_db()
    result = await db["finetune_datasets"].delete_one({"_id": dataset_id, "user_id": user_id})
    if result.deleted_count > 0:
        await db["finetune_samples"].delete_many({"dataset_id": dataset_id})
        return {"success": True}
    raise HTTPException(status_code=404, detail="Không tìm thấy tập dữ liệu.")

@router.post("/dataset/{dataset_id}/samples")
async def add_samples(dataset_id: str, req: dict):
    db = get_db()
    user_id = req.get("user_id")
    dataset = await db["finetune_datasets"].find_one({"_id": dataset_id, "user_id": user_id})
    if not dataset:
        raise HTTPException(status_code=404, detail="Không tìm thấy tập dữ liệu.")
    docs = [{"_id": str(uuid7()), "dataset_id": dataset_id, "instruction": s.get("instruction", ""), "input": s.get("input", ""), "output": s.get("output", ""), "created_at": datetime.now(timezone.utc)} for s in req.get("samples", [])]
    if docs:
        await db["finetune_samples"].insert_many(docs)
    total = await db["finetune_samples"].count_documents({"dataset_id": dataset_id})
    await db["finetune_datasets"].update_one({"_id": dataset_id}, {"$set": {"sample_count": total, "updated_at": datetime.now(timezone.utc)}})
    return {"added": len(docs), "total": total}

@router.get("/dataset/{dataset_id}/samples")
async def get_samples(dataset_id: str, user_id: str, skip: int = 0, limit: int = 50):
    db = get_db()
    if not await db["finetune_datasets"].find_one({"_id": dataset_id, "user_id": user_id}):
        raise HTTPException(status_code=404, detail="Không tìm thấy tập dữ liệu.")
    return await db["finetune_samples"].find({"dataset_id": dataset_id}).sort("created_at", 1).skip(int(skip)).limit(int(limit)).to_list(length=int(limit))

@router.delete("/dataset/{dataset_id}/samples/{sample_id}")
async def delete_sample(dataset_id: str, sample_id: str, user_id: str):
    db = get_db()
    if not await db["finetune_datasets"].find_one({"_id": dataset_id, "user_id": user_id}):
        raise HTTPException(status_code=404, detail="Không tìm thấy tập dữ liệu.")
    if (await db["finetune_samples"].delete_one({"_id": sample_id, "dataset_id": dataset_id})).deleted_count > 0:
        total = await db["finetune_samples"].count_documents({"dataset_id": dataset_id})
        await db["finetune_datasets"].update_one({"_id": dataset_id}, {"$set": {"sample_count": total, "updated_at": datetime.now(timezone.utc)}})
        return {"success": True}
    raise HTTPException(status_code=404, detail="Không tìm thấy mẫu.")

@router.post("/import/feedback")
async def import_feedback(req: dict):
    db = get_db()
    user_id = req.get("user_id")
    feedbacks = await db["rag_feedback"].find({"user_id": user_id, "vote_type": "up"}).to_list(length=500)
    if not feedbacks:
        return {"imported": 0}
    ds_id = str(uuid7())
    await db["finetune_datasets"].insert_one({
        "_id": ds_id, "user_id": user_id,
        "name": f"Feedback Import {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        "description": "Nhập từ phản hồi tích cực", "source": "feedback",
        "sample_count": 0, "status": "draft", "created_at": datetime.now(timezone.utc)
    })
    samples = []
    for fb in feedbacks:
        msg = await db["ai_messages"].find_one({"_id": fb.get("message_id")})
        if not msg:
            continue
        prev = await db["ai_messages"].find_one({"session_id": msg.get("session_id"), "role": "user", "created_at": {"$lt": msg["created_at"]}}, sort=[("created_at", -1)])
        if prev:
            samples.append({"_id": str(uuid7()), "dataset_id": ds_id, "instruction": prev.get("content", ""), "input": "", "output": msg.get("content", ""), "created_at": datetime.now(timezone.utc)})
    if samples:
        await db["finetune_samples"].insert_many(samples)
        await db["finetune_datasets"].update_one({"_id": ds_id}, {"$set": {"sample_count": len(samples), "status": "ready"}})
    return {"dataset_id": ds_id, "imported": len(samples)}

@router.post("/import/documents")
async def import_docs(req: dict):
    db = get_db()
    user_id, doc_ids = req.get("user_id"), req.get("document_ids", [])
    ds_id = str(uuid7())
    await db["finetune_datasets"].insert_one({
        "_id": ds_id, "user_id": user_id,
        "name": f"Document Import {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        "description": f"Trích xuất từ {len(doc_ids)} tài liệu", "source": "documents",
        "sample_count": 0, "status": "draft", "created_at": datetime.now(timezone.utc)
    })
    ollama_url = settings.OLLAMA_BASE_URL
    samples = []
    for did in doc_ids:
        doc = await db["documents"].find_one({"_id": did})
        if not doc:
            continue
        content = ""
        if isinstance(doc.get("content"), list):
            content = "\n".join([b.get("data", {}).get("text", "") for b in doc["content"] if isinstance(b, dict)])
        elif isinstance(doc.get("content"), str):
            content = doc["content"]
        words = content.split()
        chunks = [" ".join(words[i:i + 500]) for i in range(0, len(words), 500) if len(words[i:i + 500]) > 50][:10]
        hf_token = getattr(settings, "HF_TOKEN", None)
        from huggingface_hub import AsyncInferenceClient
        for chunk in chunks:
            try:
                client = AsyncInferenceClient(model=settings.LLAMA_MODEL, token=hf_token)
                prompt = f"Tạo 3 cặp câu hỏi - câu trả lời từ văn bản sau. Trả về mảng JSON với khóa 'instruction', 'input' (rỗng), 'output'.\n\nVăn bản:\n{chunk}\n\nJSON:"
                messages = [{"role": "user", "content": prompt}]
                resp = await client.chat_completion(messages=messages, max_tokens=1024, temperature=0.3)
                raw = resp.choices[0].message.content.strip()
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0]
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0]
                for p in json.loads(raw):
                    if p.get("instruction") and p.get("output"):
                        samples.append({"_id": str(uuid7()), "dataset_id": ds_id, "instruction": p["instruction"], "input": p.get("input", ""), "output": p["output"], "created_at": datetime.now(timezone.utc)})
            except Exception as e:
                logger.warning(f"Finetune extract failed: {e}")
    if samples:
        await db["finetune_samples"].insert_many(samples)
        await db["finetune_datasets"].update_one({"_id": ds_id}, {"$set": {"sample_count": len(samples), "status": "ready"}})
    return {"dataset_id": ds_id, "imported": len(samples)}

@router.post("/job")
async def create_job(req: dict):
    db = get_db()
    ds_id, user_id = req.get("dataset_id"), req.get("user_id")
    dataset = await db["finetune_datasets"].find_one({"_id": ds_id, "user_id": user_id})
    if not dataset:
        raise HTTPException(status_code=404, detail="Không tìm thấy tập dữ liệu.")
    if dataset.get("sample_count", 0) < 10:
        return {"error": "insufficient_samples"}
    job_id = str(uuid7())
    job = {
        "_id": job_id, "user_id": user_id, "dataset_id": ds_id,
        "job_name": req.get("job_name") or f"FT-{req.get('base_model')}-{datetime.now(timezone.utc).strftime('%m%d%H%M')}",
        "base_model": req.get("base_model"), "method": req.get("method", "lora"),
        "epochs": req.get("epochs", 3), "learning_rate": req.get("learning_rate", 2e-4),
        "batch_size": req.get("batch_size", 4), "lora_rank": req.get("lora_rank", 16),
        "lora_alpha": req.get("lora_alpha", 32),
        "status": "pending", "progress": 0.0, "current_epoch": 0, "training_log": [],
        "created_at": datetime.now(timezone.utc)
    }
    await db["finetune_jobs"].insert_one(job)
    await db["finetune_datasets"].update_one({"_id": ds_id}, {"$set": {"status": "training"}})
    return job

@router.post("/job/{job_id}/start")
async def start_job(job_id: str, req: dict):
    db = get_db()
    job = await db["finetune_jobs"].find_one({"_id": job_id, "user_id": req.get("user_id")})
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")
    if job_id in active_jobs:
        return {"error": "Công việc đang chạy."}
    samples = await db["finetune_samples"].find({"dataset_id": job["dataset_id"]}).to_list(length=10000)
    config = {
        "base_model": job.get("base_model"),
        "epochs": job.get("epochs", 3),
        "batch_size": job.get("batch_size", 4),
        "learning_rate": job.get("learning_rate", 2e-4),
        "lora_rank": job.get("lora_rank", 16),
        "lora_alpha": job.get("lora_alpha", 32),
        "training_data": [{"instruction": s.get("instruction", ""), "input": s.get("input", ""), "output": s.get("output", "")} for s in samples]
    }
    loop = asyncio.get_event_loop()
    thread = threading.Thread(target=_run_training_sync, args=(job_id, config, loop), daemon=True)
    active_jobs[job_id] = thread
    thread.start()
    await db["finetune_jobs"].update_one({"_id": job_id}, {"$set": {"status": "running", "started_at": datetime.now(timezone.utc)}})
    return {"status": "started", "job_id": job_id}

@router.get("/job")
async def list_jobs(user_id: str):
    return await get_db()["finetune_jobs"].find({"user_id": user_id}).sort("created_at", -1).to_list(length=100)

@router.get("/job/{job_id}")
async def get_job(job_id: str, user_id: str):
    job = await get_db()["finetune_jobs"].find_one({"_id": job_id, "user_id": user_id})
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")
    return job

@router.post("/job/{job_id}/cancel")
async def cancel_job(job_id: str, req: dict):
    db = get_db()
    result = await db["finetune_jobs"].update_one(
        {"_id": job_id, "user_id": req.get("user_id"), "status": {"$in": ["pending", "running"]}},
        {"$set": {"status": "cancelled"}}
    )
    if result.modified_count > 0:
        active_jobs.pop(job_id, None)
        return {"status": "cancelled"}
    raise HTTPException(status_code=400, detail="Không thể hủy công việc này.")

@router.post("/job/{job_id}/deploy")
async def deploy_model(job_id: str, req: dict):
    db = get_db()
    job = await db["finetune_jobs"].find_one({"_id": job_id, "user_id": req.get("user_id"), "status": "completed"})
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc hoàn thành.")
    model_name = job.get("merged_model_name", job["job_name"])
    gguf_path = job.get("gguf_path")
    merged_path = job.get("merged_path")
    
    hf_token = getattr(settings, "HF_TOKEN", None)
    if not hf_token:
        raise HTTPException(status_code=500, detail="Thiếu HF_TOKEN để tải mô hình lên HuggingFace Hub.")

    try:
        from huggingface_hub import HfApi
        api = HfApi(token=hf_token)
        user_info = api.whoami()
        hf_username = user_info.get("name")
        
        repo_id = f"{hf_username}/{model_name}"
        
        logger.info(f"Creating repository on HuggingFace Hub: {repo_id}")
        api.create_repo(repo_id=repo_id, exist_ok=True)
        
        if merged_path:
            import os
            if os.path.exists(merged_path):
                logger.info(f"Uploading folder {merged_path} to {repo_id}")
                import asyncio
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: api.upload_folder(
                    folder_path=merged_path,
                    repo_id=repo_id,
                    commit_message="Deploy fine-tuned model via DocLib"
                ))
            else:
                logger.warning(f"Could not find merged path directory: {merged_path}")
                raise Exception("Không tìm thấy thư mục mô hình đã gộp.")
                
        model_name = repo_id
        await db["finetune_jobs"].update_one({"_id": job_id}, {"$set": {"merged_model_name": repo_id}})
        
    except Exception as e:
        logger.error(f"HuggingFace Hub deploy failed: {e}")
        raise HTTPException(status_code=500, detail=f"Triển khai lên HuggingFace thất bại: {e}")

    await db["finetune_jobs"].update_one({"_id": job_id}, {"$set": {"status": "deployed"}})
    return {"status": "deployed", "model_name": model_name}

@router.post("/job/{job_id}/evaluate")
async def evaluate_model(job_id: str, req: dict):
    from src.harness.evaluation_harness import evaluation_harness
    db = get_db()
    job = await db["finetune_jobs"].find_one({"_id": job_id, "user_id": req.get("user_id")})
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")
    model_name = job.get("merged_model_name") or job.get("base_model")
    use_judge = req.get("use_judge", True)
    evaluation_harness._dataset = req.get("test_samples", [])
    result = await evaluation_harness.run_benchmark(model_name=model_name, use_judge=use_judge)
    return result

