from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
import asyncio
import threading
from datetime import datetime, timezone

from fastapi import HTTPException, Query
from loguru import logger

from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.repositories.finetuning import FinetuneRepository
from src.repositories.chat import ChatRepository

active_jobs = {}

class TrainingCancelled(Exception):
    pass

from src.schemas.finetuning import FinetuneJobUpdate

@log_logic_execution
async def report_progress(job_id: str, data: dict):
    update_fields = FinetuneJobUpdate(**data).model_dump(exclude_none=True)
    if data.get("status") == "completed":
        update_fields["completed_at"] = datetime.now(timezone.utc)
        update_fields["progress"] = 100.0
    if "loss" in data:
        log_entry = {
            "epoch": data.get("current_epoch", 0),
            "loss": data["loss"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await FinetuneRepository.update_job(
            {"_id": job_id}, {"$push": {"training_log": log_entry}}
        )
        job = await FinetuneRepository.find_job({"_id": job_id})
        if job:
            best = job.get("best_loss")
            if best is None or data["loss"] < best:
                update_fields["best_loss"] = data["loss"]
    if update_fields:
        await FinetuneRepository.update_job(
            {"_id": job_id}, {"$set": update_fields}
        )
    status_value = data.get("status")
    if status_value in {"completed", "failed", "cancelled"}:
        job = await FinetuneRepository.find_job({"_id": job_id})
        if job:
            dataset_status = "trained" if status_value == "completed" else "ready"
            await FinetuneRepository.update_dataset(
                {"_id": job["dataset_id"]},
                {"$set": {"status": dataset_status}},
            )

def _run_training_sync(job_id: str, config: dict, loop, cancel_event):
    from src.training.finetuning import run_finetune_job

    @log_logic_execution
    async def _update(data):
        await report_progress(job_id, data)

    def sync_update(data):
        if cancel_event.is_set():
            raise TrainingCancelled
        future = asyncio.run_coroutine_threadsafe(_update(data), loop)
        future.result(timeout=30)

    try:
        sync_update({"status": "running", "progress": 5})

        sync_update({"progress": 10, "status": "running"})
        result = run_finetune_job(job_id, config, sync_update)

        adapter_path = result.get("adapter_path", "")
        final_loss = result.get("final_loss", 0)
        merged_path = result.get("merged_path", "")

        sync_update({"progress": 98, "current_loss": round(final_loss, 6)})

        model_name = "DocLib Metis"

        merged_path = result.get("merged_path", "")
        gguf_path = result.get("gguf_path", "")

        sync_update(
            {
                "status": "completed",
                "progress": 100,
                "current_epoch": config.get("epochs", 3),
                "current_loss": round(final_loss, 6),
                "best_loss": round(final_loss, 6),
                "merged_model_name": model_name,
                "adapter_path": adapter_path,
                "merged_path": merged_path,
                "gguf_path": gguf_path,
            }
        )

    except TrainingCancelled:
        future = asyncio.run_coroutine_threadsafe(
            _update({"status": "cancelled"}),
            loop,
        )
        future.result(timeout=30)
    except Exception:
        logger.exception("Model fine-tuning process error")
        sync_update({"status": "failed", "error_code": "model_finetuning_failed"})
    finally:
        active_jobs.pop(job_id, None)

@log_logic_execution
async def create_dataset(req: dict):
    logger.info(f"Started fine-tuning dataset creation for user_id={req.get('user_id')}")
    doc = {
        "_id": str(uuid7()),
        "user_id": req.get("user_id"),
        "name": req.get("name"),
        "description": req.get("description", ""),
        "source": req.get("source", "manual"),
        "sample_count": 0,
        "status": "draft",
        "created_at": datetime.now(timezone.utc),
    }
    await FinetuneRepository.insert_dataset(doc)
    return doc

@log_logic_execution
async def list_datasets(user_id: str):
    cursor = mongo.find("finetune_datasets", {"user_id": user_id}).sort("created_at", -1)
    return await cursor.to_list(length=None)

@log_logic_execution
async def get_dataset(dataset_id: str, user_id: str):
    doc = await mongo.find_one("finetune_datasets", 
        {"_id": dataset_id, "user_id": user_id}
    )
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "finetuning_dataset_not_found"})
    return doc

@log_logic_execution
async def delete_dataset(dataset_id: str, user_id: str):
    
    result = await FinetuneRepository.delete_dataset(
        {"_id": dataset_id, "user_id": user_id}
    )
    if result.deleted_count > 0:
        await FinetuneRepository.delete_samples(
            {"dataset_id": dataset_id}
        )
        return {"success": True}
    raise HTTPException(status_code=404, detail={"code": "finetuning_dataset_not_found"})

@log_logic_execution
async def add_samples(dataset_id: str, req: dict):
    
    user_id = req.get("user_id")
    dataset = await FinetuneRepository.find_dataset(
        {"_id": dataset_id, "user_id": user_id}
    )
    if not dataset:
        raise HTTPException(status_code=404, detail={"code": "finetuning_dataset_not_found"})
    documents = [
        {
            "_id": str(uuid7()),
            "dataset_id": dataset_id,
            "instruction": s.get("instruction", ""),
            "input": s.get("input", ""),
            "output": s.get("output", ""),
            "created_at": datetime.now(timezone.utc),
        }
        for s in req.get("samples", [])
    ]
    if documents:
        await FinetuneRepository.insert_samples(documents)
    total = await FinetuneRepository.count_samples(
        {"dataset_id": dataset_id}
    )
    await FinetuneRepository.update_dataset(
        {"_id": dataset_id},
        {"$set": {"sample_count": total, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"added": len(documents), "total": total}

@log_logic_execution
async def get_samples(
    dataset_id: str,
    user_id: str,
    skip: int = 0,
    limit: int = Query(default=20, le=100),
):
    
    if not await FinetuneRepository.find_dataset(
        {"_id": dataset_id, "user_id": user_id}
    ):
        raise HTTPException(status_code=404, detail={"code": "finetuning_dataset_not_found"})
    cursor = mongo.find("finetune_samples", {"dataset_id": dataset_id}).sort("created_at", 1).skip(int(skip)).limit(int(limit))
    return await cursor.to_list(length=None)

@log_logic_execution
async def delete_sample(dataset_id: str, sample_id: str, user_id: str):
    
    if not await FinetuneRepository.find_dataset(
        {"_id": dataset_id, "user_id": user_id}
    ):
        raise HTTPException(status_code=404, detail={"code": "finetuning_dataset_not_found"})
    if (
        await FinetuneRepository.delete_sample(
            {"_id": sample_id, "dataset_id": dataset_id}
        )
    ).deleted_count > 0:
        total = await FinetuneRepository.count_samples(
            {"dataset_id": dataset_id}
        )
        await FinetuneRepository.update_dataset(
            {"_id": dataset_id},
            {"$set": {"sample_count": total, "updated_at": datetime.now(timezone.utc)}},
        )
        return {"success": True}
    raise HTTPException(status_code=404, detail={"code": "finetuning_sample_not_found"})

@log_logic_execution
async def import_feedback(req: dict):
    
    user_id = req.get("user_id")
    feedbacks = await mongo.find("rag_feedback", {"user_id": user_id, "vote_type": "up"}).to_list(length=None)
    if not feedbacks:
        return {"imported": 0}
    ds_id = str(uuid7())
    await FinetuneRepository.insert_dataset(
        {
            "_id": ds_id,
            "user_id": user_id,
            "name": f"Data Import {datetime.now(timezone.utc).strftime('%Y-%m-%d %H%M')}",
            "description": "",
            "source": "feedback",
            "sample_count": 0,
            "status": "draft",
            "created_at": datetime.now(timezone.utc),
        }
    )
    samples = []
    for fb in feedbacks:
        msg = await ChatRepository.find_ai_message(
            {"_id": fb.get("message_id")}
        )
        if not msg:
            continue
        prev = await ChatRepository.find_ai_message(
            {
                "session_id": msg.get("session_id"),
                "role": "user",
                "created_at": {"$lt": msg["created_at"]},
            },
            sort=[("created_at", -1)],
        )
        if prev:
            samples.append(
                {
                    "_id": str(uuid7()),
                    "dataset_id": ds_id,
                    "instruction": prev.get("content", ""),
                    "input": "",
                    "output": msg.get("content", ""),
                    "created_at": datetime.now(timezone.utc),
                }
            )
    if samples:
        await FinetuneRepository.insert_samples(samples)
        await FinetuneRepository.update_dataset(
            {"_id": ds_id}, {"$set": {"sample_count": len(samples), "status": "ready"}}
        )
    return {"dataset_id": ds_id, "imported": len(samples)}

@log_logic_execution
async def import_documents(req: dict):
    user_id, doc_ids = req.get("user_id"), req.get("document_ids", [])
    from huggingface_hub import AsyncInferenceClient
    from langchain_core.messages import HumanMessage
    from src.schemas.finetuning import GeneratedSamples
    from src.utils.huggingface import HFInferenceChat

    client = AsyncInferenceClient(
        model=settings.LLM_MODEL,
        token=settings.HF_TOKEN,
    )
    structured_model = HFInferenceChat(
        client=client,
        model=settings.LLM_MODEL,
    ).with_structured_output(GeneratedSamples)
    generated_samples = []
    for document_id in doc_ids:
        document = await FinetuneRepository.find_document_context(
            {"_id": document_id}
        )
        if not document:
            continue
        content = ""
        if isinstance(document.get("content"), list):
            content = "\n".join(
                str(block.get("data", {}).get("text", ""))
                for block in document["content"]
                if isinstance(block, dict)
            )
        elif isinstance(document.get("content"), str):
            content = document["content"]
        words = content.split()
        chunks = [
            " ".join(words[index : index + 500])
            for index in range(0, len(words), 500)
            if len(words[index : index + 500]) > 50
        ][:10]
        for chunk in chunks:
            try:
                from src.core.registry import PromptType, registry

                prompt = registry.get(PromptType.FINETUNE_QA_GENERATION).format(
                    chunk=chunk
                )
                generated = await structured_model.ainvoke(
                    [HumanMessage(content=prompt)],
                    max_tokens=1024,
                    temperature=0.3,
                )
                generated_samples.extend(
                    sample.model_dump() for sample in generated.samples
                )
            except Exception:
                logger.exception("Training data extraction error")
    if not generated_samples:
        raise HTTPException(
            status_code=503,
            detail={"code": "finetuning_sample_generation_failed"},
        )
    dataset_id = str(uuid7())
    await FinetuneRepository.insert_dataset(
        {
            "_id": dataset_id,
            "user_id": user_id,
            "name": f"Data Import {datetime.now(timezone.utc).strftime('%Y-%m-%d %H%M')}",
            "description": "",
            "source": "documents",
            "sample_count": len(generated_samples),
            "status": "ready",
            "created_at": datetime.now(timezone.utc),
        }
    )
    sample_documents = [
        {
            "_id": str(uuid7()),
            "dataset_id": dataset_id,
            **sample,
            "created_at": datetime.now(timezone.utc),
        }
        for sample in generated_samples
    ]
    await FinetuneRepository.insert_samples(sample_documents)
    return {"dataset_id": dataset_id, "imported": len(sample_documents)}

@log_logic_execution
async def create_job(req: dict):
    
    ds_id, user_id = req.get("dataset_id"), req.get("user_id")
    dataset = await FinetuneRepository.find_dataset(
        {"_id": ds_id, "user_id": user_id}
    )
    if not dataset:
        raise HTTPException(status_code=404, detail={"code": "finetuning_dataset_not_found"})
    if dataset.get("sample_count", 0) < 10:
        return {"error_code": "finetuning_dataset_too_small", "minimum_samples": 10}
    job_id = str(uuid7())
    job = {
        "_id": job_id,
        "user_id": user_id,
        "dataset_id": ds_id,
        "job_name": req.get("job_name")
        or f"Model-Training-Task-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
        "base_model": req.get("base_model") or settings.LLM_MODEL,
        "method": req.get("method", "lora"),
        "epochs": req.get("epochs", 3),
        "learning_rate": req.get("learning_rate", 2e-4),
        "batch_size": req.get("batch_size", 4),
        "lora_rank": req.get("lora_rank", 16),
        "lora_alpha": req.get("lora_alpha", 32),
        "status": "pending",
        "progress": 0.0,
        "current_epoch": 0,
        "training_log": [],
        "created_at": datetime.now(timezone.utc),
    }
    await FinetuneRepository.insert_job(job)
    return job

@log_logic_execution
async def start_job(job_id: str, req: dict):
    
    job = await FinetuneRepository.find_job(
        {"_id": job_id, "user_id": req.get("user_id"), "status": "pending"}
    )
    if not job:
        raise HTTPException(status_code=404, detail={"code": "finetuning_job_not_found"})
    if job_id in active_jobs:
        return {"error_code": "finetuning_job_already_running"}
    samples = await mongo.find("finetune_samples", {"dataset_id": job["dataset_id"]}).to_list(length=None)
    config = {
        "base_model": job.get("base_model") or settings.LLM_MODEL,
        "hf_token": settings.HF_TOKEN,
        "epochs": job.get("epochs", 3),
        "batch_size": job.get("batch_size", 4),
        "learning_rate": job.get("learning_rate", 2e-4),
        "lora_rank": job.get("lora_rank", 16),
        "lora_alpha": job.get("lora_alpha", 32),
        "training_data": [
            {
                "instruction": s.get("instruction", ""),
                "input": s.get("input", ""),
                "output": s.get("output", ""),
            }
            for s in samples
        ],
    }
    loop = asyncio.get_event_loop()
    cancel_event = threading.Event()
    thread = threading.Thread(
        target=_run_training_sync,
        args=(job_id, config, loop, cancel_event),
        daemon=True,
    )
    await FinetuneRepository.update_job(
        {"_id": job_id},
        {"$set": {"status": "running", "started_at": datetime.now(timezone.utc)}},
    )
    await FinetuneRepository.update_dataset(
        {"_id": job["dataset_id"]}, {"$set": {"status": "training"}}
    )
    active_jobs[job_id] = {"thread": thread, "cancel_event": cancel_event}
    thread.start()
    return {"status": "started", "job_id": job_id}

@log_logic_execution
async def list_jobs(user_id: str):
    cursor = mongo.find("finetune_jobs", {"user_id": user_id}).sort("created_at", -1)
    return await cursor.to_list(length=None)

@log_logic_execution
async def get_job(job_id: str, user_id: str):
    job = await mongo.find_one("finetune_jobs", {"_id": job_id, "user_id": user_id})
    if not job:
        raise HTTPException(status_code=404, detail={"code": "finetuning_job_not_found"})
    return job

@log_logic_execution
async def cancel_job(job_id: str, req: dict):
    job = await FinetuneRepository.find_job(
        {"_id": job_id, "user_id": req.get("user_id")}
    )
    if not job:
        raise HTTPException(status_code=404, detail={"code": "finetuning_job_not_found"})
    result = await FinetuneRepository.update_job(
        {
            "_id": job_id,
            "user_id": req.get("user_id"),
            "status": {"$in": ["pending", "running"]},
        },
        {"$set": {"status": "cancelled"}},
    )
    if result.modified_count > 0:
        active_job = active_jobs.get(job_id)
        if active_job:
            active_job["cancel_event"].set()
        await FinetuneRepository.update_dataset(
            {"_id": job["dataset_id"]}, {"$set": {"status": "ready"}}
        )
        return {"status": "cancelled"}
    raise HTTPException(
        status_code=400, detail={"code": "finetuning_job_not_cancellable"}
    )

@log_logic_execution
async def deploy_model(job_id: str, req: dict):
    
    job = await FinetuneRepository.find_job(
        {"_id": job_id, "user_id": req.get("user_id"), "status": "completed"}
    )
    if not job:
        raise HTTPException(
            status_code=404, detail={"code": "deployable_finetuning_job_not_found"}
        )
    model_name = job.get("merged_model_name", job["job_name"])
    gguf_path = job.get("gguf_path")
    merged_path = job.get("merged_path")

    hf_token = settings.HF_TOKEN
    if not hf_token:
        raise HTTPException(
            status_code=500, detail={"code": "model_registry_credentials_missing"}
        )

    try:
        from huggingface_hub import HfApi

        api = HfApi(token=hf_token)
        user_info = api.whoami()
        hf_username = user_info.get("name")

        repo_id = f"{hf_username}/{model_name}"

        logger.info("Remote model repository created")
        api.create_repo(repo_id=repo_id, exist_ok=True)

        import os
        artifact_uploaded = False
        if merged_path:
            if await asyncio.to_thread(os.path.exists, merged_path):
                logger.info("Uploading model to remote repository")

                await asyncio.to_thread(
                    api.upload_folder,
                    folder_path=merged_path,
                    repo_id=repo_id,
                    commit_message="Deploy fine tuned model via automated system",
                )
                artifact_uploaded = True
            else:
                logger.warning("Model output directory not found")
        if gguf_path:
            if await asyncio.to_thread(os.path.isfile, gguf_path):
                logger.info("Uploading GGUF model to remote repository")
                await asyncio.to_thread(
                    api.upload_file,
                    path_or_fileobj=gguf_path,
                    path_in_repo=os.path.basename(gguf_path),
                    repo_id=repo_id,
                    commit_message="Deploy GGUF model via automated system",
                )
                artifact_uploaded = True
            else:
                logger.warning("GGUF model artifact not found")
        if not artifact_uploaded:
            raise FileNotFoundError("model_artifact_not_found")

        model_name = repo_id
        await FinetuneRepository.update_job(
            {"_id": job_id}, {"$set": {"merged_model_name": repo_id}}
        )

    except Exception:
        logger.exception("Model deployment to remote repository error")
        raise HTTPException(
            status_code=500, detail={"code": "model_deployment_failed"}
        )

    await FinetuneRepository.update_job(
        {"_id": job_id}, {"$set": {"status": "deployed"}}
    )
    return {"status": "deployed", "model_name": model_name}

@log_logic_execution
async def evaluate_model(job_id: str, req: dict):
    from src.loop.evaluation import evaluation

    job = await FinetuneRepository.find_job(
        {"_id": job_id, "user_id": req.get("user_id")}
    )
    if not job:
        raise HTTPException(status_code=404, detail={"code": "finetuning_job_not_found"})
    model_name = job.get("merged_model_name") or job.get("base_model")
    use_judge = req.get("use_judge", True)
    evaluation._dataset = req.get("test_samples", [])
    result = await evaluation.run_benchmark(model_name=model_name, use_judge=use_judge)
    return result
