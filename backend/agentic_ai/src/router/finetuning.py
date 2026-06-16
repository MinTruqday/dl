import asyncio
from datetime import datetime, timezone
from core.config import settings
from core.database import db_client
from core.repositories.base import RepositoryFactory
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from huggingface_hub import HfApi
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.training.engine import run_finetune_job
from uuid6 import uuid7

router = APIRouter(prefix="/huan-luyen")

def get_db():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    return client.get_default_database()

async def report_progress(job_id: str, data: dict):
    update_fields = {}
    for key in ["progress", "current_epoch", "current_loss", "status", "adapter_path", "merged_model_name", "error_message", "best_loss"]:
        if key in data:
            update_fields[key] = data[key]
    if data.get("status") == "completed":
        update_fields["completed_at"] = datetime.now(timezone.utc)
        update_fields["progress"] = 100.0
    if "loss" in data:
        log_entry = {"epoch": data.get("current_epoch", 0), "loss": data["loss"], "timestamp": datetime.now(timezone.utc).isoformat()}
        await RepositoryFactory.get("finetune_jobs").update_one({"_id": job_id}, {"$push": {"training_log": log_entry}})
        job = await RepositoryFactory.get("finetune_jobs").find_one({"_id": job_id})
        if job:
            best = job.get("best_loss")
            if best is None or data["loss"] < best:
                update_fields["best_loss"] = data["loss"]
    if update_fields:
        await RepositoryFactory.get("finetune_jobs").update_one({"_id": job_id}, {"$set": update_fields})

def _run_training_sync(job_id: str, config: dict, loop):
    async def _update(data):
        await report_progress(job_id, data)

    def sync_update(data):
        asyncio.run_coroutine_threadsafe(_update(data), loop)

    try:
        sync_update({"status": "running", "progress": 5})
        sync_update({"progress": 10, "status": "running"})
        result = run_finetune_job(job_id, config, sync_update)
        adapter_path = result.get("adapter_path", "")
        final_loss = result.get("final_loss", 0)
        merged_path = result.get("merged_path", "")
        sync_update({"progress": 98, "current_loss": round(final_loss, 6)})
        model_name = f"model-ft-{job_id[:8]}"
        gguf_path = result.get("gguf_path", "")
        sync_update({"status": "completed", "progress": 100, "current_loss": round(final_loss, 6), "best_loss": round(final_loss, 6), "merged_model_name": model_name, "adapter_path": adapter_path, "merged_path": merged_path, "gguf_path": gguf_path})
    except Exception:
        logger.error("Lỗi xử lý model AI")
        sync_update({"status": "failed", "error_message": "The system encountered an unexpected error and requires you to try again later"})
    finally:
        if db_client.redis:
            asyncio.run_coroutine_threadsafe(db_client.redis.delete(f"finetune_lock:{job_id}"), loop)

@router.post("/du-lieu")
async def create_dataset(req: dict):
    doc = {"_id": str(uuid7()), "user_id": req.get("user_id"), "name": req.get("name"), "description": req.get("description", ""), "source": req.get("source", "manual"), "sample_count": 0, "status": "draft", "created_at": datetime.now(timezone.utc)}
    await RepositoryFactory.get("finetune_datasets").insert_one(doc)
    return doc

@router.get("/du-lieu")
async def list_datasets(user_id: str):
    return await get_db()["finetune_datasets"].find({"user_id": user_id}).sort("created_at", -1).to_list(length=100)

@router.get("/du-lieu/{dataset_id}")
async def get_dataset(dataset_id: str, user_id: str):
    doc = await get_db()["finetune_datasets"].find_one({"_id": dataset_id, "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
    return doc

@router.delete("/du-lieu/{dataset_id}")
async def delete_dataset(dataset_id: str, user_id: str):
    result = await RepositoryFactory.get("finetune_datasets").delete_one({"_id": dataset_id, "user_id": user_id})
    if result.deleted_count > 0:
        await RepositoryFactory.get("finetune_samples").delete_many({"dataset_id": dataset_id})
        return {"success": True}
    raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.post("/du-lieu/{dataset_id}/mau-thu")
async def add_samples(dataset_id: str, req: dict):
    dataset = await RepositoryFactory.get("finetune_datasets").find_one({"_id": dataset_id, "user_id": req.get("user_id")})
    if not dataset:
        raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
    documents = [{"_id": str(uuid7()), "dataset_id": dataset_id, "instruction": s.get("instruction", ""), "input": s.get("input", ""), "output": s.get("output", ""), "created_at": datetime.now(timezone.utc)} for s in req.get("samples", [])]
    if documents:
        await RepositoryFactory.get("finetune_samples").insert_many(documents)
    total = await RepositoryFactory.get("finetune_samples").count_documents({"dataset_id": dataset_id})
    await RepositoryFactory.get("finetune_datasets").update_one({"_id": dataset_id}, {"$set": {"sample_count": total, "updated_at": datetime.now(timezone.utc)}})
    return {"added": len(documents), "total": total}

@router.get("/du-lieu/{dataset_id}/mau-thu")
async def get_samples(dataset_id: str, user_id: str, skip: int = 0, limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT)):
    if not await RepositoryFactory.get("finetune_datasets").find_one({"_id": dataset_id, "user_id": user_id}):
        raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
    return await RepositoryFactory.get("finetune_samples").find({"dataset_id": dataset_id}).sort("created_at", 1).skip(int(skip)).limit(int(limit)).to_list(length=int(limit))

@router.delete("/du-lieu/{dataset_id}/mau-thu/{sample_id}")
async def delete_sample(dataset_id: str, sample_id: str, user_id: str):
    if not await RepositoryFactory.get("finetune_datasets").find_one({"_id": dataset_id, "user_id": user_id}):
        raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
    if (await RepositoryFactory.get("finetune_samples").delete_one({"_id": sample_id, "dataset_id": dataset_id})).deleted_count > 0:
        total = await RepositoryFactory.get("finetune_samples").count_documents({"dataset_id": dataset_id})
        await RepositoryFactory.get("finetune_datasets").update_one({"_id": dataset_id}, {"$set": {"sample_count": total, "updated_at": datetime.now(timezone.utc)}})
        return {"success": True}
    raise HTTPException(status_code=404, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")

@router.post("/cong-viec")
async def create_job(req: dict):
    ds_id, user_id = req.get("dataset_id"), req.get("user_id")
    dataset = await RepositoryFactory.get("finetune_datasets").find_one({"_id": ds_id, "user_id": user_id})
    if not dataset:
        raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
    if dataset.get("sample_count", 0) < 10:
        return {"error": "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"}
    job_id = str(uuid7())
    job = {"_id": job_id, "user_id": user_id, "dataset_id": ds_id, "job_name": req.get("job_name") or f"Model-Training-Task-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}", "base_model": req.get("base_model"), "method": req.get("method", "lora"), "epochs": req.get("epochs", 3), "learning_rate": req.get("learning_rate", 2e-4), "batch_size": req.get("batch_size", 4), "lora_rank": req.get("lora_rank", 16), "lora_alpha": req.get("lora_alpha", 32), "status": "pending", "progress": 0.0, "current_epoch": 0, "training_log": [], "created_at": datetime.now(timezone.utc)}
    await RepositoryFactory.get("finetune_jobs").insert_one(job)
    await RepositoryFactory.get("finetune_datasets").update_one({"_id": ds_id}, {"$set": {"status": "training"}})
    return job

@router.post("/cong-viec/{job_id}/bat-dau")
async def start_job(job_id: str, req: dict, background_tasks: BackgroundTasks):
    job = await RepositoryFactory.get("finetune_jobs").find_one({"_id": job_id, "user_id": req.get("user_id")})
    if not job:
        raise HTTPException(status_code=404, detail="Khởi tạo AI thành công")
    
    if db_client.redis:
        lock_acquired = await db_client.redis.set(f"finetune_lock:{job_id}", "locked", nx=True, ex=86400)
        if not lock_acquired:
            return {"error": "Mất kết nối mạng tạm thời"}
            
    samples = await RepositoryFactory.get("finetune_samples").find({"dataset_id": job["dataset_id"]}).to_list(length=10000)
    config = {"base_model": job.get("base_model"), "epochs": job.get("epochs", 3), "batch_size": job.get("batch_size", 4), "learning_rate": job.get("learning_rate", 2e-4), "lora_rank": job.get("lora_rank", 16), "lora_alpha": job.get("lora_alpha", 32), "training_data": [{"instruction": s.get("instruction", ""), "input": s.get("input", ""), "output": s.get("output", "")} for s in samples]}
    loop = asyncio.get_running_loop()
    background_tasks.add_task(asyncio.to_thread, _run_training_sync, job_id, config, loop)
    await RepositoryFactory.get("finetune_jobs").update_one({"_id": job_id}, {"$set": {"status": "running", "started_at": datetime.now(timezone.utc)}})
    return {"status": "started", "job_id": job_id}

@router.get("/cong-viec")
async def list_jobs(user_id: str):
    return await get_db()["finetune_jobs"].find({"user_id": user_id}).sort("created_at", -1).to_list(length=100)

@router.get("/cong-viec/{job_id}")
async def get_job(job_id: str, user_id: str):
    job = await get_db()["finetune_jobs"].find_one({"_id": job_id, "user_id": user_id})
    if not job:
        raise HTTPException(status_code=404, detail="Khởi tạo AI thành công")
    return job

@router.post("/cong-viec/{job_id}/huy-bo")
async def cancel_job(job_id: str, req: dict):
    result = await RepositoryFactory.get("finetune_jobs").update_one({"_id": job_id, "user_id": req.get("user_id"), "status": {"$in": ["pending", "running"]}}, {"$set": {"status": "cancelled"}})
    if result.modified_count > 0:
        if db_client.redis:
            await db_client.redis.delete(f"finetune_lock:{job_id}")
        return {"status": "cancelled"}
    raise HTTPException(status_code=400, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")

@router.post("/cong-viec/{job_id}/trien-khai")
async def deploy_model(job_id: str, req: dict):
    import os
    job = await RepositoryFactory.get("finetune_jobs").find_one({"_id": job_id, "user_id": req.get("user_id"), "status": "completed"})
    if not job:
        raise HTTPException(status_code=404, detail="Khởi tạo AI thành công")
    model_name = job.get("merged_model_name", job["job_name"])
    merged_path = job.get("merged_path")
    if not settings.HF_TOKEN:
        raise HTTPException(status_code=500, detail="Mất kết nối mạng tạm thời")
    try:
        api = HfApi(token=settings.HF_TOKEN)
        repo_id = f"{api.whoami().get('name')}/{model_name}"
        logger.info("Khởi tạo AI thành công")
        api.create_repo(repo_id=repo_id, exist_ok=True)
        if merged_path and os.path.exists(merged_path):
            logger.info("Mất kết nối mạng tạm thời")
            await asyncio.get_event_loop().run_in_executor(None, lambda: api.upload_folder(folder_path=merged_path, repo_id=repo_id, commit_message="Lỗi xử lý model AI"))
        else:
            logger.warning("Khởi tạo AI thành công")
            raise Exception("The directory containing the merged model could not be located on the system")
        await RepositoryFactory.get("finetune_jobs").update_one({"_id": job_id}, {"$set": {"merged_model_name": repo_id}})
    except Exception:
        logger.error("Khởi tạo AI thành công")
        raise HTTPException(status_code=500, detail="Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
    await RepositoryFactory.get("finetune_jobs").update_one({"_id": job_id}, {"$set": {"status": "deployed"}})
    return {"status": "deployed", "model_name": repo_id}