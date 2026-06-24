import base64
import os
import uuid
import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger

from shared.infrastructure.database import database

router = APIRouter(prefix="/drm")

class Registration(BaseModel):
    document_id: str
    user_id: str

class Confirmation(BaseModel):
    file_id: str
    aes_key: str  # Base64 encoded 256-bit key

class Acquisition(BaseModel):
    file_id: str

class Token(BaseModel):
    aes_key: str

@router.post("/dang-ky", response_model=Confirmation)
async def register_file(req: Registration):
    try:
        file_id = str(uuid.uuid4())
        raw_key = os.urandom(32)
        encoded_key = base64.b64encode(raw_key).decode('utf-8')
        
        db = database.mongodb.get_default_database()
        licenses_col = db["drm_licenses"]
        
        await licenses_col.insert_one({
            "file_id": file_id,
            "aes_key": encoded_key,
            "document_id": req.document_id,
            "user_id": req.user_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
            "status": "ACTIVE",
            "open_count": 0
        })
        
        logger.info(f"Registered new DRM file: {file_id} for user {req.user_id}")
        return Confirmation(file_id=file_id, aes_key=encoded_key)
    except Exception as e:
        logger.error(f"Error registering DRM file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/kiem-tra", response_model=Token)
async def acquire_license(req: Acquisition):
    try:
        db = database.mongodb.get_default_database()
        licenses_col = db["drm_licenses"]
        
        license_doc = await licenses_col.find_one({"file_id": req.file_id})
        if not license_doc:
            raise HTTPException(status_code=404, detail="File license not found")
            
        if license_doc.get("status") != "ACTIVE":
            raise HTTPException(status_code=403, detail="License revoked or expired")
            
        # Simplified for testing:
        user_id = license_doc.get("user_id")
            
        # Update open count
        await licenses_col.update_one(
            {"_id": license_doc["_id"]},
            {"$inc": {"open_count": 1}, "$set": {"last_opened_at": datetime.datetime.now(datetime.timezone.utc)}}
        )
        
        logger.info(f"License granted for file {req.file_id} to user {user_id}")
        return Token(aes_key=license_doc["aes_key"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acquiring license: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
