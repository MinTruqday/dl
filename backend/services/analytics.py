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
        
        top_by_views = await db["documents"].find({"status": "published"}).sort("views", -1).limit(10).to_list(10)
        top_by_rating = await db["documents"].find({"status": "published"}).sort("average_rating", -1).limit(10).to_list(10)
        top_authors_list = await db["users"].find({"role": "author"}).sort("followers_count", -1).limit(10).to_list(10)
        
        if not top_authors_list:
            top_authors_list = await db["users"].find({"role": "author"}).limit(10).to_list(10)
            
        async def hydrate_document(doc):
            author = await db["users"].find_one({"_id": doc.get("author_id")}, {"full_name": 1, "slug": 1})
            return {
                "_id": str(doc["_id"]),
                "title": doc.get("title"),
                "slug": doc.get("slug"),
                "author": {
                    "_id": str(author["_id"]) if author else "",
                    "display_name": author.get("full_name") if author else "Vô danh",
                    "slug": author.get("slug") if author else ""
                },
                "views_count": doc.get("views", 0),
                "rating_avg": doc.get("average_rating", 0),
                "cover_image": doc.get("cover_url")
            }

        return {
            "top_documents_by_views": [await hydrate_document(d) for d in top_by_views],
            "top_documents_by_rating": [await hydrate_document(d) for d in top_by_rating],
            "top_authors": [
                {
                    "_id": str(a["_id"]),
                    "display_name": a.get("full_name"),
                    "slug": a.get("slug"),
                    "avatar_url": a.get("avatar_url"),
                    "followers_count": a.get("followers_count", 0),
                    "badges": a.get("badges", [])
                } for a in top_authors_list
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

    @staticmethod
    async def get_author_revenue_analytics(current_user):
        db = db_client.mongodb.get_default_database()
        author_id = str(current_user.id)
        docs = await db["documents"].find({"author_id": author_id}).to_list(length=200)
        total_views = sum(b.get("views", 0) for b in docs)
        
        purchase_pipeline = [
            {"$match": {"document_id": {"$in": [str(b["_id"]) for b in docs]}, "item_type": "document"}},
            {"$group": {"_id": None, "total_sales": {"$sum": 1}, "total_revenue": {"$sum": "$price"}}},
        ]
        
        sales_data = await db["purchases"].aggregate(purchase_pipeline).to_list(length=1)
        total_sales = sales_data[0]["total_sales"] if sales_data else 0
        total_revenue = sales_data[0]["total_revenue"] if sales_data else 0
        
        recent_sales = await db["purchases"].find(
            {"document_id": {"$in": [str(b["_id"]) for b in docs]}}
        ).sort("purchased_at", -1).limit(10).to_list(length=10)
        
        chart_data = []
        for s in recent_sales:
            doc = next((b for b in docs if str(b["_id"]) == s.get("document_id")), None)
            chart_data.append({
                "document_title": doc.get("title", "") if doc else "Tài liệu ẩn",
                "price": s.get("price", 0),
                "date": s["purchased_at"].isoformat() if isinstance(s.get("purchased_at"), datetime) else s.get("purchased_at"),
            })
            
        return {
            "total_views": total_views,
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "total_documents": len(docs),
            "recent_sales": chart_data,
            "currency": "dl"
        }

    @staticmethod
    async def get_chapter_dropoff(document_id: str, current_user) -> list:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        chapters = doc.get("chapters", [])
        result = []
        for ch in chapters:
            readers = await db["reading_history"].count_documents({
                "document_id": document_id,
                "current_chapter_slug": ch.get("id"),
            })
            result.append({
                "chapter_id": ch.get("id", ""),
                "chapter_title": ch.get("title", ""),
                "order": ch.get("order", 0),
                "readers_at_chapter": readers,
            })
        return result

    @staticmethod
    async def analyze_reader_sentiment(document_id: str, current_user) -> dict:
        from core.config import settings
        import httpx
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc: 
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        reviews = await db["reviews"].find({"document_id": document_id}).to_list(length=100)
        if not reviews: 
            return {"sentiment": "neutral", "summary": "Chưa có đánh giá nào để phân tích."}
            
        rag_url = getattr(settings, "AGENTIC_RAG_URL", None)
        if rag_url:
            texts = [r.get("review_text", "") for r in reviews if r.get("review_text")]
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(f"{rag_url}/api/inference/analyze-sentiment", json={"texts": texts})
                    if resp.status_code == 200: 
                        return resp.json()
            except Exception as e: 
                logger.warning(f"RAG: Phân tích cảm xúc thất bại: {e}")
                
        return {"sentiment": "neutral", "summary": "Dịch vụ AI phân tích hiện không khả dụng."}