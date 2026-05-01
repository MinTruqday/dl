from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import uuid
from loguru import logger

class AssetService:
    @staticmethod
    async def get_assets(current_user, asset_type: str = "all") -> list:
        db = db_client.mongodb.get_default_database()
        query = {"author_id": str(current_user.id)}
        if asset_type != "all":
            query["type"] = {"$regex": asset_type, "$options": "i"}
        
        assets = await db["assets"].find(query).sort("created_at", -1).to_list(length=200)
        return [
            {
                "id": str(a["_id"]),
                "filename": a.get("filename", ""),
                "type": a.get("type", "unknown"),
                "size_bytes": a.get("size_bytes", 0),
                "url": a.get("url", ""),
                "created_at": a["created_at"].isoformat() if isinstance(a.get("created_at"), datetime) else a.get("created_at"),
            }
            for a in assets
        ]

    @staticmethod
    async def upload_asset(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        asset = {
            "_id": str(uuid.uuid4()),
            "author_id": str(current_user.id),
            "filename": data["filename"],
            "type": data.get("type", "image"),
            "size_bytes": data.get("size_bytes", 0),
            "url": data["url"],
            "created_at": datetime.utcnow(),
        }
        await db["assets"].insert_one(asset)
        logger.info(f"Workspace: Author {current_user.id} uploaded asset {data['filename']}")
        return {"message": "Tải lên tài nguyên thành công.", "asset": asset}

    @staticmethod
    async def delete_asset(asset_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["assets"].delete_one({"_id": asset_id, "author_id": str(current_user.id)})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
            
        logger.info(f"Workspace: Asset {asset_id} deleted by author {current_user.id}")
        return {"message": "Đã xóa tài nguyên thành công."}
