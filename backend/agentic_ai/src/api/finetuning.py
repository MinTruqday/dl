import asyncio
from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Query, HTTPException, Depends
import src.services.finetuning as finetune_service
from src.core.dependency import get_current_user, CurrentUser
from src.core.infrastructure.configuration import settings

router = APIRouter(route_class=LoggingRoute, prefix="/tinh-chinh")

@router.post("/tap-du-lieu")
async def create_dataset(req: dict):
    return await finetune_service.create_dataset(req)

@router.get("/tap-du-lieu")
async def list_datasets(current_user: CurrentUser = Depends(get_current_user)):
    return await finetune_service.list_datasets(str(current_user.id))

@router.get("/tap-du-lieu/{dataset_id}")
async def get_dataset(dataset_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await finetune_service.get_dataset(dataset_id, str(current_user.id))

@router.delete("/tap-du-lieu/{dataset_id}")
async def delete_dataset(dataset_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await finetune_service.delete_dataset(dataset_id, str(current_user.id))

@router.post("/tap-du-lieu/{dataset_id}/mau-thu")
async def add_samples(dataset_id: str, req: dict):
    return await finetune_service.add_samples(dataset_id, req)

@router.get("/tap-du-lieu/{dataset_id}/mau-thu")
async def get_samples(
    dataset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(default=20, le=100),
):
    return await finetune_service.get_samples(dataset_id, str(current_user.id), skip, limit)

@router.delete("/tap-du-lieu/{dataset_id}/mau-thu/{sample_id}")
async def delete_sample(dataset_id: str, sample_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await finetune_service.delete_sample(dataset_id, sample_id, str(current_user.id))

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
async def list_jobs(current_user: CurrentUser = Depends(get_current_user)):
    return await finetune_service.list_jobs(str(current_user.id))

@router.get("/tien-trinh/{job_id}")
async def get_job(job_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await finetune_service.get_job(job_id, str(current_user.id))

@router.post("/tien-trinh/{job_id}/huy-bo")
async def cancel_job(job_id: str, req: dict):
    return await finetune_service.cancel_job(job_id, req)

@router.post("/tien-trinh/{job_id}/trien-khai")
async def deploy_model(job_id: str, req: dict):
    return await finetune_service.deploy_model(job_id, req)

@router.post("/tien-trinh/{job_id}/danh-gia")
async def evaluate_model(job_id: str, req: dict):
    return await finetune_service.evaluate_model(job_id, req)
