from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from models.user import UserInDB
from api.dependencies import get_current_user, RateLimiter
from services.profile import ProfileService
from pydantic import BaseModel
import json
import io

class AuthorApplicationBase(BaseModel):
    portfolio_url: str
    reason: str

router = APIRouter(prefix="/profile")

@router.get("/me")
async def get_my_profile(current_user: UserInDB = Depends(get_current_user)):
    return await ProfileService.get_user_profile(current_user)

@router.put("/me")
async def update_my_profile(data: dict, current_user: UserInDB = Depends(get_current_user)):
    return await ProfileService.update_profile(data, current_user)

@router.get("/settings")
async def get_settings(current_user: UserInDB = Depends(get_current_user)):
    from core.database import db_client
    db = db_client.mongodb.get_default_database()
    user = await db["users"].find_one({"_id": str(current_user.id)}, {"settings": 1})
    defaults = {
        "appearance": "light",
        "fontSize": "medium",
        "notifications": True,
        "privacyProfile": "public",
        "privacyActivity": True,
        "twoFactor": False,
        "notifyCommunity": {"email": True, "inapp": True},
        "notifyFinance": {"email": True, "inapp": True},
        "notifyUpdates": {"email": False, "inapp": True},
        "notifyNewsletter": {"email": True, "inapp": False},
    }
    if user and "settings" in user:
        defaults.update(user["settings"])
    return defaults

@router.put("/settings")
async def update_settings(data: dict, current_user: UserInDB = Depends(get_current_user)):
    from core.database import db_client
    from datetime import datetime
    db = db_client.mongodb.get_default_database()
    await db["users"].update_one(
        {"_id": str(current_user.id)},
        {"$set": {"settings": data, "updated_at": datetime.utcnow()}}
    )
    return {"message": "Đã lưu cài đặt."}

@router.get("/takeout", dependencies=[Depends(RateLimiter(calls=2, period=3600))])
async def request_data_takeout(current_user: UserInDB = Depends(get_current_user)):
    takeout_payload = await ProfileService.request_data_takeout(current_user)
    stream = io.StringIO(json.dumps(takeout_payload, ensure_ascii=False, indent=2, default=str))
    return StreamingResponse(
        iter([stream.getvalue()]), 
        media_type="application/json", 
        headers={"Content-Disposition": f"attachment; filename=doclib_takeout_{current_user.slug}.json"}
    )

@router.post("/apply-author")
async def apply_author(application: AuthorApplicationBase, current_user: UserInDB = Depends(get_current_user)):
    return await ProfileService.apply_author(application, current_user)

@router.post("/upload-kyc")
async def upload_kyc(file: UploadFile = File(...), current_user: UserInDB = Depends(get_current_user)):
    return await ProfileService.upload_kyc(file, current_user)

@router.delete("/right-to-be-forgotten", dependencies=[Depends(RateLimiter(calls=1, period=86400))])
async def right_to_be_forgotten(current_user: UserInDB = Depends(get_current_user)):
    return await ProfileService.right_to_be_forgotten(current_user)

@router.get("/streaks")
async def get_reading_streaks(current_user: UserInDB = Depends(get_current_user)):
    return await ProfileService.get_reading_streaks(current_user)

@router.get("/badges")
async def get_badges(current_user: UserInDB = Depends(get_current_user)):
    return await ProfileService.get_badges(current_user)

@router.post("/block/{target_id}")
async def block_user(target_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await ProfileService.block_user(target_id, current_user)

@router.post("/gdpr/export")
async def request_data_export(current_user: UserInDB = Depends(get_current_user)):
    return await ProfileService.request_data_export(current_user)

@router.post("/gdpr/delete")
async def request_data_deletion(current_user: UserInDB = Depends(get_current_user)):
    return await ProfileService.right_to_be_forgotten(current_user)
