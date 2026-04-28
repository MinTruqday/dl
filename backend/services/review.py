from core.database import db_client
from fastapi import HTTPException
from loguru import logger

class ReviewService:
    @staticmethod
    async def create_review(document_id: str, review_in, current_user):
        if review_in.rating < 1 or review_in.rating > 5:
            raise HTTPException(status_code=400, detail="Xếp hạng phải từ 1 đến 5 sao.")
            
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"$or": [{"_id": document_id}, {"slug": document_id}]})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu bạn đang cố đánh giá.")
            
        real_document_id = str(doc["_id"])
        
        review_dict = review_in.model_dump()
        review_dict["document_id"] = real_document_id
        review_dict["user_id"] = str(current_user.id)
        review_dict["full_name"] = current_user.full_name
        review_dict["avatar_url"] = current_user.avatar_url
        
        await db["reviews"].insert_one(review_dict)
        
        pipeline = [
            {"$match": {"document_id": real_document_id}},
            {"$group": {"_id": "$document_id", "avg_rating": {"$avg": "$rating"}, "count": {"$sum": 1}}}
        ]
        aggr = await db["reviews"].aggregate(pipeline).to_list(1)
        if aggr:
            avg_rating = aggr[0]["avg_rating"]
            count = aggr[0]["count"]
            await db["documents"].update_one({"_id": real_document_id}, {"$set": {"avg_rating": avg_rating, "review_count": count}})
            
        logger.info(f"Review created for document {real_document_id} by user {current_user.id}")
        return review_dict

    @staticmethod
    async def get_reviews(document_id: str):
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"$or": [{"_id": document_id}, {"slug": document_id}]})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        real_document_id = str(doc["_id"])
        reviews_cursor = db["reviews"].find({"document_id": real_document_id}).sort("created_at", -1)
        return await reviews_cursor.to_list(length=100)
