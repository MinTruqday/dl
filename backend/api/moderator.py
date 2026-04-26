from fastapi import APIRouter, Depends, Query
from api.dependencies import require_role, get_current_user
from models.user import UserInDB, RoleEnum
from services.moderator import ModeratorService
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/moderator")

class ModerationActionRequest(BaseModel):
    reason: str
    duration_hours: Optional[int] = 24

class TagRequest(BaseModel):
    name: str

class BlacklistRequest(BaseModel):
    keyword: str

class ContentRemovalRequest(BaseModel):
    item_type: str
    item_id: str
    reason: str

@router.get("/reports", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_reports(status: str = "pending", skip: int = 0, limit: int = 30):
    return await ModeratorService.get_report_queue(status, skip, limit)

@router.post("/users/{user_id}/warn", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def warn_user(user_id: str, req: ModerationActionRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.warn_user(user_id, req.reason, current_user)

@router.post("/users/{user_id}/lock", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def lock_user(user_id: str, req: ModerationActionRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.lock_user(user_id, req.reason, req.duration_hours, current_user)

@router.post("/tags", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def create_tag(req: TagRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.manage_tags("create", req.name, current_user)

@router.delete("/tags/{tag_name}", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def delete_tag(tag_name: str, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.manage_tags("delete", tag_name, current_user)

@router.get("/tags")
async def get_tags():
    return await ModeratorService.get_all_tags()

@router.post("/blacklist", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def add_to_blacklist(req: BlacklistRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.manage_blacklist("add", req.keyword, current_user)

@router.delete("/blacklist/{keyword}", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def remove_from_blacklist(keyword: str, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.manage_blacklist("remove", keyword, current_user)

@router.get("/blacklist", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_blacklist():
    return await ModeratorService.get_blacklist()

@router.post("/content/remove", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def remove_content(req: ContentRemovalRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.remove_violating_content(req.item_type, req.item_id, req.reason, current_user)

@router.get("/metrics", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_metrics():
    return await ModeratorService.get_community_metrics()

@router.get("/activity", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_activity(current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.get_moderator_activity_log(str(current_user.id))
@router.get("/payouts", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_payouts(status: str = "pending"):
    return await ModeratorService.get_payout_queue(status)

@router.post("/payouts/{payout_id}/{action}", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_payout(payout_id: str, action: str, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.verify_payout(payout_id, action, current_user)

@router.get("/approval-queue", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_approval_queue(skip: int = 0, limit: int = 30):
    return await ModeratorService.get_approval_queue(skip, limit)

class ModerateDocumentRequest(BaseModel):
    action: str
    reason: str

@router.post("/documents/{document_id}/moderate", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def moderate_document(document_id: str, req: ModerateDocumentRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.moderate_document(document_id, req.action, req.reason, current_user)

@router.post("/users/{user_id}/shadowban", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def shadowban_user(user_id: str, is_banned: bool, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.shadowban_user(user_id, is_banned, current_user)

@router.post("/users/{user_id}/kyc/{status}", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_kyc(user_id: str, status: str, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.verify_kyc(user_id, status, current_user)

@router.delete("/users/{user_id}/comments", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def bulk_delete_comments(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.bulk_delete_comments(user_id, current_user)

@router.get("/users/{user_id}/notes", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_moderator_notes(user_id: str):
    return await ModeratorService.get_moderator_notes(user_id)

class NoteRequest(BaseModel):
    note: str

@router.post("/users/{user_id}/notes", dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def add_moderator_note(user_id: str, req: NoteRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ModeratorService.add_moderator_note(user_id, req.note, current_user)
