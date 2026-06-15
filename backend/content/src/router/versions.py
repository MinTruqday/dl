from typing import Any
from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends
from src.dependencies import get_current_user, get_db
from src.services.versions import VersionsService

router = APIRouter(prefix="/versions")

@router.post("/save/{document_id}", response_model=APIResponse[Any])
async def save_version(document_id: str, version_note: str, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await VersionsService.save_version(document_id, version_note, current_user, db=db),
        message="New chronological static structural architectural state mapping effectively constructed stored accurately",
        status=201,
    )

@router.get("/documents/{document_id}", response_model=APIResponse[Any])
async def get_document_versions(document_id: str, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await VersionsService.get_versions(document_id, current_user, db=db),
        message="Linear sequential array enumerating past functional historical checkpoints seamlessly restored rendering",
    )

@router.post("/{version_id}/restore", response_model=APIResponse[Any])
async def restore_version(version_id: str, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await VersionsService.restore_version(version_id, current_user, db=db),
        message="Targeted digital object fundamentally relocated matching chosen distinct prior preservation format",
    )