import uuid
import datetime
from datetime import timezone
from fastapi import HTTPException
from core.database import db_client
from loguru import logger

def serialize_document(document):
    if not document:
        return None
    if "_id" in document:
        document["_id"] = str(document["_id"])
    if "created_at" not in document:
        document["created_at"] = datetime.datetime.now(timezone.utc)
    return document

class SeriesService:
    @staticmethod
    async def create_series(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        series_id = str(uuid.uuid4())
        series = {
            "_id": series_id,
            "author_id": str(current_user.id),
            "title": data["title"],
            "description": data.get("description", ""),
            "document_ids": data.get("document_ids", []),
            "created_at": datetime.datetime.now(timezone.utc),
        }
        await db["series"].insert_one(series)
        if series["document_ids"]:
            await db["documents"].update_many(
                {"_id": {"$in": series["document_ids"]}, "author_id": str(current_user.id)},
                {"$set": {"series_id": series_id}}
            )
        logger.info(f"Workspace: Series created {series_id} by {current_user.id}")
        return {"message": "Tạo Series thành công.", "series_id": series_id}

    @staticmethod
    async def get_my_series(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        series_docs = await db["series"].find({"author_id": str(current_user.id)}).sort("created_at", -1).to_list(length=100)
        return [serialize_document(s) for s in series_docs]

    @staticmethod
    async def get_series_by_id(series_id: str) -> dict:
        db = db_client.mongodb.get_default_database()
        series = await db["series"].find_one({"_id": series_id})
        if not series:
            raise HTTPException(status_code=404, detail="Không tìm thấy chuỗi tài liệu.")
            
        series = serialize_document(series)
        if series.get("document_ids"):
            docs = await db["documents"].find({"_id": {"$in": series["document_ids"]}}).to_list(length=100)
            series["documents"] = [serialize_document(d) for d in docs]
            
        return series

    @staticmethod
    async def update_series(series_id: str, data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        
        series = await db["series"].find_one({"_id": series_id, "author_id": str(current_user.id)})
        if not series:
            raise HTTPException(status_code=404, detail="Không tìm thấy chuỗi tài liệu hoặc không có quyền.")
        
        update_fields = {}
        if "title" in data and data["title"]:
            update_fields["title"] = data["title"]
        if "description" in data:
            update_fields["description"] = data["description"]
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="Không có trường nào để cập nhật.")
        
        update_fields["updated_at"] = datetime.datetime.now(timezone.utc)
        
        await db["series"].update_one(
            {"_id": series_id},
            {"$set": update_fields}
        )
        
        logger.info(f"Series {series_id} updated by {current_user.id}")
        return {"message": "Cập nhật chuỗi thành công.", "series_id": series_id}

    @staticmethod
    async def delete_series(series_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        
        series = await db["series"].find_one({"_id": series_id, "author_id": str(current_user.id)})
        if not series:
            raise HTTPException(status_code=404, detail="Không tìm thấy chuỗi tài liệu hoặc không có quyền.")
        
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                # Delete series
                await db["series"].delete_one({"_id": series_id}, session=session)
                
                # Remove series_id from linked documents
                if series.get("document_ids"):
                    await db["documents"].update_many(
                        {"_id": {"$in": series["document_ids"]}},
                        {"$unset": {"series_id": ""}},
                        session=session
                    )
                
                await session.commit_transaction()
                logger.info(f"Series {series_id} deleted by {current_user.id}")
                return {"message": "Xóa chuỗi thành công."}
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Delete series failed for {series_id}: {e}")
            raise HTTPException(status_code=500, detail="Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.")
        finally:
            await session.end_session()

    @staticmethod
    async def reorder_series_documents(series_id: str, document_ids: list, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        
        series = await db["series"].find_one({"_id": series_id, "author_id": str(current_user.id)})
        if not series:
            raise HTTPException(status_code=404, detail="Không tìm thấy chuỗi tài liệu hoặc không có quyền.")
        
        docs = await db["documents"].find({
            "_id": {"$in": document_ids},
            "author_id": str(current_user.id)
        }).to_list(length=500)
        
        if len(docs) != len(document_ids):
            raise HTTPException(status_code=400, detail="Một số tài liệu không tồn tại hoặc không thuộc về bạn.")
        
        await db["series"].update_one(
            {"_id": series_id},
            {"$set": {"document_ids": document_ids, "updated_at": datetime.datetime.now(timezone.utc)}}
        )
        
        logger.info(f"Series {series_id} documents reordered by {current_user.id}")
        return {"message": "Sắp xếp lại thứ tự thành công."}

    @staticmethod
    async def link_series(document_id: str, series_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        series = await db["series"].find_one({"_id": series_id, "author_id": str(current_user.id)})
        if not series:
            raise HTTPException(status_code=404, detail="Không tìm thấy chuỗi tài liệu.")
            
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        await db["series"].update_one({"_id": series_id}, {"$addToSet": {"document_ids": document_id}})
        await db["documents"].update_one({"_id": document_id}, {"$set": {"series_id": series_id}})
        
        logger.info(f"Workspace: Document {document_id} linked to series {series_id} by {current_user.id}")
        return {"message": "Liên kết chuỗi tài liệu thành công."}
