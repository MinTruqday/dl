from fastapi import APIRouter, Depends
from models.user import UserInDB
from api.dependencies import get_current_user
from services.version import VersionsService

router = APIRouter(prefix="/versions")

@router.post("/save/{document_id}")
async def save_version(document_id: str, version_note: str, current_user: UserInDB = Depends(get_current_user)):
    return await VersionsService.save_version(document_id, version_note, current_user)
