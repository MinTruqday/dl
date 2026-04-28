from core.database import db_client
from fastapi import HTTPException
from bson import ObjectId
from datetime import datetime
from loguru import logger

class AnalyticsService:
    @staticmethod
    async def get_dashboard_stats(current_user):
        db = db_client.mongodb.get_default_database()
        total_users = await db["users"].count_documents({})
        total_documents = await db["documents"].count_documents({})
        total_comments = await db["comments"].count_documents({})
        
        pipeline = [
            {"$group": {"_id": "$author_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_authors_aggr = await db["documents"].aggregate(pipeline).to_list(5)
        
        top_authors = []
        for author_stat in top_authors_aggr:
            author = await db["users"].find_one({"_id": author_stat["_id"]})
            if author:
                top_authors.append({
                    "full_name": author["full_name"],
                    "document_count": author_stat["count"]
                })
        
        logger.info(f"System statistics requested by admin {current_user.id}")
        return {
            "system_stats": {
                "users": total_users,
                "documents": total_documents,
                "comments": total_comments
            },
            "top_authors": top_authors
        }

    @staticmethod
    async def get_leaderboard():
        db = db_client.mongodb.get_default_database()
        top_docs = await db["documents"].find({"status": "published"}).sort("views", -1).limit(10).to_list(10)
        top_authors = await db["users"].find({"role": "author"}).sort("followers_count", -1).limit(10).to_list(10)
        if not top_authors:
            top_authors = await db["users"].find({"role": "author"}).limit(10).to_list(10)
            
        return {
            "top_documents": [
                {
                    "id": str(b["_id"]),
                    "title": b.get("title"),
                    "slug": b.get("slug"),
                    "author_id": b.get("author_id"),
                    "views": b.get("views", 0),
                    "average_rating": b.get("average_rating", 0),
                    "cover_url": b.get("cover_url")
                } for b in top_docs
            ],
            "top_authors": [
                {
                    "id": str(a["_id"]),
                    "full_name": a.get("full_name"),
                    "slug": a.get("slug"),
                    "avatar_url": a.get("avatar_url"),
                    "followers_count": a.get("followers_count", 0),
                    "badges": a.get("badges", [])
                } for a in top_authors
            ]
        }

    @staticmethod
    async def get_author_stats(current_user):
        if current_user.role != "author":
            raise HTTPException(status_code=403, detail="Tính năng này chỉ dành cho tài khoản Tác giả.")
            
        db = db_client.mongodb.get_default_database()
        docs = await db["documents"].find({"author_id": str(current_user.id)}).to_list(length=1000)
        total_views = sum([b.get("views", 0) for b in docs])
        
        logger.info(f"Author stats requested by user {current_user.id}")
        return {
            "total_documents": len(docs),
            "total_views": total_views,
            "followers_count": getattr(current_user, "followers_count", 0),
            "documents": [
                {
                    "id": str(b["_id"]),
                    "title": b.get("title"),
                    "views": b.get("views", 0),
                    "rating": b.get("average_rating", 0.0)
                } for b in docs
            ]
        }

    @staticmethod
    async def record_funnel_dropoff(payload, current_user):
        db = db_client.mongodb.get_default_database()
        document_id = payload.get("document_id") or payload.get("document_id")
        await db["reading_funnels"].insert_one({
            "document_id": document_id,
            "user_id": str(current_user.id),
            "drop_chapter": payload.get("chapter"),
            "drop_scroll_percent": payload.get("scroll_percent"),
            "reading_time_seconds": payload.get("dwell_time"),
            "timestamp": datetime.utcnow()
        })
        logger.info(f"Funnel dropoff recorded for user {current_user.id} on document {document_id}")
        return {"status": "ok"}

    @staticmethod
    async def extract_entity_profiling(document_id):
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": str(document_id)})
        if not doc:
            return {}
        
        content = str(doc.get("content", ""))
        words = content.split()
        entities = {}
        for w in words:
            if w.istitle() and len(w) > 2:
                entities[w] = entities.get(w, 0) + 1
                
        top_entities = dict(sorted(entities.items(), key=lambda item: item[1], reverse=True)[:10])
        return {"top_characters_or_places": top_entities}

    @staticmethod
    async def log_read_event(event, current_user):
        db = db_client.mongodb.get_default_database()
        await db["read_events"].insert_one({
            "user_id": str(current_user.id) if current_user else "anonymous",
            **event.model_dump(),
            "created_at": datetime.utcnow()
        })
        return {"message": "Đã ghi nhận sự kiện đọc."}

    @staticmethod
    async def get_mention_analytics(target_id: str):
        db = db_client.mongodb.get_default_database()
        
        query = {"$regex": f"@{target_id}", "$options": "i"}
        comment_mentions = await db["comments"].count_documents({"content": query})
        post_mentions = await db["posts"].count_documents({"content": query})
        
        return {
            "target_id": target_id,
            "total_mentions": comment_mentions + post_mentions,
            "breakdown": {
                "comments": comment_mentions,
                "social_posts": post_mentions
            },
            "last_updated": datetime.utcnow()
        }

    @staticmethod
    async def get_author_demographics(current_user):
        db = db_client.mongodb.get_default_database()
        logger.info(f"Author demographics requested by user {current_user.id}")
        
        return {
            "age_groups": {}, 
            "locations": {},
            "gender_ratio": {}
        }