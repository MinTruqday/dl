import asyncio
from fastapi import APIRouter, Query, HTTPException
from src.services import finetune as finetune_service

router = APIRouter(prefix="/tinh-chinh")

@router.post("/tap-du-lieu")
async def create_dataset(req: dict):
    return await finetune_service.create_dataset(req)

@router.get("/tap-du-lieu")
async def list_datasets(user_id: str):
    return await finetune_service.list_datasets(user_id)

@router.get("/tap-du-lieu/{dataset_id}")
async def get_dataset(dataset_id: str, user_id: str):
    return await finetune_service.get_dataset(dataset_id, user_id)

@router.delete("/tap-du-lieu/{dataset_id}")
async def delete_dataset(dataset_id: str, user_id: str):
    return await finetune_service.delete_dataset(dataset_id, user_id)

@router.post("/tap-du-lieu/{dataset_id}/mau-thu")
async def add_samples(dataset_id: str, req: dict):
    return await finetune_service.add_samples(dataset_id, req)

@router.get("/tap-du-lieu/{dataset_id}/mau-thu")
async def get_samples(
    dataset_id: str,
    user_id: str,
    skip: int = 0,
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
):
    return await finetune_service.get_samples(dataset_id, user_id, skip, limit, le)

@router.delete("/tap-du-lieu/{dataset_id}/mau-thu/{sample_id}")
async def delete_sample(dataset_id: str, sample_id: str, user_id: str):
    return await finetune_service.delete_sample(dataset_id, sample_id, user_id)

@router.post("/dau-vao/phan-hoi")
async def import_feedback(req: dict):
    return await finetune_service.import_feedback(req)

@router.post("/dau-vao/tai-lieu")
async def import_documents(req: dict):
    return await finetune_service.import_documents(req)

@router.post("/tien-trinh")
async def create_job(req: dict):
    return await finetune_service.create_job(req)

@router.post("/tien-trinh/{job_id}/bat-dau")
async def start_job(job_id: str, req: dict):
    return await finetune_service.start_job(job_id, req)

@router.get("/tien-trinh")
async def list_jobs(user_id: str):
    return await finetune_service.list_jobs(user_id)

@router.get("/tien-trinh/{job_id}")
async def get_job(job_id: str, user_id: str):
    return await finetune_service.get_job(job_id, user_id)

@router.post("/tien-trinh/{job_id}/huy-bo")
async def cancel_job(job_id: str, req: dict):
    return await finetune_service.cancel_job(job_id, req)

@router.post("/tien-trinh/{job_id}/trien-khai")
async def deploy_model(job_id: str, req: dict):
    return await finetune_service.deploy_model(job_id, req)

@router.post("/tien-trinh/{job_id}/danh-gia")
async def evaluate_model(job_id: str, req: dict):
    return await finetune_service.evaluate_model(job_id, req)
