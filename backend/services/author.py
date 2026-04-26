from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timedelta
import uuid
import json
import httpx
from loguru import logger
from bson import ObjectId
import os
from models.wallet import Transaction, TransactionType
from models.user import UserInDB

class AuthorService:
    @staticmethod
    async def invite_coauthor(document_id: str, invitee_id_or_email: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại hoặc bạn không có quyền truy cập.")

        invitee = await db["users"].find_one({
            "$or": [{"_id": invitee_id_or_email}, {"email": invitee_id_or_email}]
        })
        if not invitee:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng này trên hệ thống.")
        
        invitee_id = str(invitee["_id"])
        if invitee_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Bạn không thể tự mời chính mình làm đồng tác giả.")
            
        coauthors = doc.get("coauthors", [])
        if invitee_id in coauthors:
            raise HTTPException(status_code=400, detail="Người này đã là đồng tác giả của tài liệu.")
            
        await db["documents"].update_one(
            {"_id": document_id},
            {"$push": {"coauthors": invitee_id}, "$set": {"updated_at": datetime.utcnow()}}
        )
        logger.info(f"User {current_user.id} invited {invitee_id} as co-author for document {document_id}")
        return {"message": "Đã thêm đồng tác giả thành công."}

    @staticmethod
    async def reply_to_review(review_id: str, reply_text: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        review = await db["reviews"].find_one({"_id": ObjectId(review_id)})
        if not review:
            raise HTTPException(status_code=404, detail="Bản đánh giá không tồn tại.")
        
        doc = await db["documents"].find_one({"_id": review["document_id"]})
        if not doc or (doc["author_id"] != str(current_user.id) and str(current_user.id) not in doc.get("coauthors", [])):
            raise HTTPException(status_code=403, detail="Bạn không có quyền phản hồi đánh giá cho tài liệu này.")
            
        await db["reviews"].update_one(
            {"_id": ObjectId(review_id)},
            {"$set": {"author_reply": reply_text, "replied_at": datetime.utcnow()}}
        )
        logger.info(f"Author {current_user.id} replied to review {review_id}")
        return {"message": "Đã gửi phản hồi thành công."}

    @staticmethod
    async def get_my_documents(current_user, skip: int = 0, limit: int = 50) -> list:
        db = db_client.mongodb.get_default_database()
        docs = await db["documents"].find(
            {"author_id": str(current_user.id)}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        return [
            {
                "id": str(b["_id"]),
                "title": b.get("title", ""),
                "slug": b.get("slug", ""),
                "status": b.get("status", "draft"),
                "cover_url": b.get("cover_url"),
                "views": b.get("views", 0),
                "average_rating": b.get("average_rating"),
                "chapters_count": len(b.get("chapters", [])),
                "created_at": b["created_at"].isoformat() if isinstance(b.get("created_at"), datetime) else b.get("created_at"),
            }
            for b in docs
        ]

    @staticmethod
    async def set_document_pricing(document_id: str, data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại hoặc bạn không có quyền thiết lập giá.")
        update = {
            "price_dl": max(0, data.get("price_dl", 0)),
            "is_drm_protected": data.get("is_drm_protected", True),
            "updated_at": datetime.utcnow(),
        }
        await db["documents"].update_one({"_id": document_id}, {"$set": update})
        logger.info(f"Pricing updated for document {document_id} by author {current_user.id}: {update['price_dl']} dl")
        return {"message": "Đã cập nhật giá bán và thiết lập bản quyền thành công."}

    @staticmethod
    async def get_revenue_analytics(current_user) -> dict:
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
    async def get_reader_feedback(document_id: str, current_user) -> list:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại hoặc bạn không có quyền.")
        reviews = await db["reviews"].find({"document_id": document_id}).sort("created_at", -1).to_list(length=50)
        result = []
        for r in reviews:
            user = await db["users"].find_one({"_id": r["user_id"]}, {"full_name": 1, "avatar_url": 1})
            result.append({
                "id": str(r["_id"]) if "_id" in r else "",
                "user_name": user.get("full_name", "Ẩn danh") if user else "Ẩn danh",
                "user_avatar": user.get("avatar_url") if user else None,
                "rating": r.get("rating", 0),
                "review_text": r.get("review_text", ""),
                "created_at": r["created_at"].isoformat() if isinstance(r.get("created_at"), datetime) else r.get("created_at"),
            })
        return result

    @staticmethod
    async def schedule_publish(document_id: str, publish_at: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
        scheduled_time = datetime.fromisoformat(publish_at)
        if scheduled_time <= datetime.utcnow():
            raise HTTPException(status_code=400, detail="Thời gian xuất bản dự kiến phải ở tương lai.")
        await db["documents"].update_one(
            {"_id": document_id},
            {"$set": {"scheduled_publish_at": scheduled_time, "status": "scheduled", "updated_at": datetime.utcnow()}}
        )
        logger.info(f"Document {document_id} scheduled for publish at {publish_at}")
        return {"message": "Đã lên lịch xuất bản thành công.", "scheduled_at": publish_at}

    @staticmethod
    async def set_free_preview(document_id: str, chapter_ids: list, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại hoặc bạn không có quyền.")
        chapters = doc.get("chapters", [])
        for ch in chapters:
            ch["is_premium"] = ch["id"] not in chapter_ids
        await db["documents"].update_one({"_id": document_id}, {"$set": {"chapters": chapters, "updated_at": datetime.utcnow()}})
        logger.info(f"Free preview chapters configured for document {document_id}")
        return {"message": "Đã thiết lập các chương đọc thử miễn phí thành công."}

    @staticmethod
    async def create_coupon(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        coupon = {
            "_id": str(uuid.uuid4()),
            "author_id": str(current_user.id),
            "code": data["code"].upper(),
            "discount_percent": min(100, max(1, data.get("discount_percent", 10))),
            "max_uses": data.get("max_uses", 100),
            "used_count": 0,
            "document_id": data.get("document_id"),
            "expires_at": datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        existing = await db["coupons"].find_one({"code": coupon["code"]})
        if existing:
            raise HTTPException(status_code=400, detail="Mã giảm giá này đã tồn tại trên hệ thống.")
        await db["coupons"].insert_one(coupon)
        logger.info(f"Author {current_user.id} created coupon {coupon['code']}")
        return {"message": "Tạo mã giảm giá thành công.", "coupon_id": coupon["_id"]}

    @staticmethod
    async def get_my_coupons(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        coupons = await db["coupons"].find(
            {"author_id": str(current_user.id)}
        ).sort("created_at", -1).to_list(length=50)
        return [
            {
                "id": c["_id"],
                "code": c.get("code", ""),
                "discount_percent": c.get("discount_percent", 0),
                "max_uses": c.get("max_uses", 0),
                "used_count": c.get("used_count", 0),
                "document_id": c.get("document_id"),
                "is_active": c.get("is_active", True),
                "expires_at": c["expires_at"].isoformat() if isinstance(c.get("expires_at"), datetime) else c.get("expires_at"),
            }
            for c in coupons
        ]

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
    async def create_series(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        series = {
            "_id": str(uuid.uuid4()),
            "author_id": str(current_user.id),
            "title": data["title"],
            "description": data.get("description", ""),
            "document_ids": data.get("document_ids", []),
            "created_at": datetime.utcnow(),
        }
        await db["series"].insert_one(series)
        if series["document_ids"]:
            await db["documents"].update_many(
                {"_id": {"$in": series["document_ids"]}, "author_id": str(current_user.id)},
                {"$set": {"series_id": series["_id"]}}
            )
        logger.info(f"Author {current_user.id} created series: {data['title']}")
        return {"message": "Tạo chuỗi tài liệu (Series) thành công.", "series_id": series["_id"]}

    @staticmethod
    async def update_brand_page(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        update = {
            "brand_tagline": data.get("tagline", "")[:200],
            "brand_about": data.get("about", "")[:2000],
            "brand_links": data.get("links", {}),
            "welcome_message": data.get("welcome_message", "")[:1000],
            "updated_at": datetime.utcnow(),
        }
        await db["users"].update_one({"_id": str(current_user.id)}, {"$set": update})
        logger.info(f"Author {current_user.id} updated brand page profile")
        return {"message": "Đã cập nhật trang thương hiệu và lời chào thành công."}

    @staticmethod
    async def set_document_password(document_id: str, password: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash(password)
        await db["documents"].update_one(
            {"_id": document_id},
            {"$set": {"access_password_hash": hashed, "is_password_protected": True, "updated_at": datetime.utcnow()}}
        )
        logger.info(f"Password protection enabled for document {document_id}")
        return {"message": "Mật khẩu bảo vệ tài liệu đã được thiết lập thành công."}

    @staticmethod
    async def request_payout(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)})
        balance = user.get("wallet_balance", 0)
        amount = data.get("amount", 0)
        if amount <= 0 or amount > balance:
            raise HTTPException(status_code=400, detail="Số dl yêu cầu không hợp lệ hoặc vượt quá số dư hiện có.")
        payout_req = {
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "amount": amount,
            "bank_info": data.get("bank_info", {}),
            "status": "pending",
            "created_at": datetime.utcnow(),
        }
        await db["payout_requests"].insert_one(payout_req)
        await db["users"].update_one({"_id": str(current_user.id)}, {"$inc": {"wallet_balance": -amount}})
        logger.info(f"Author {current_user.id} requested payout of {amount} dl")
        return {"message": "Yêu cầu rút tiền đã được gửi thành công và đang chờ hệ thống phê duyệt.", "payout_id": payout_req["_id"]}

    @staticmethod
    async def analyze_reader_sentiment(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc: raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
        reviews = await db["reviews"].find({"document_id": document_id}).to_list(length=100)
        if not reviews: return {"sentiment": "neutral", "summary": "Chưa có đánh giá nào để phân tích."}
        rag_url = os.environ.get("AGENTIC_RAG_URL")
        if rag_url:
            texts = [r.get("review_text", "") for r in reviews if r.get("review_text")]
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(f"{rag_url}/api/inference/analyze-sentiment", json={"texts": texts})
                    if resp.status_code == 200: return resp.json()
            except Exception as e: logger.warning(f"RAG sentiment analysis failed: {e}")
        return {"sentiment": "neutral", "summary": "Dịch vụ AI phân tích hiện không khả dụng."}

    @staticmethod
    async def check_grammar(document_id: str, chapter_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc: raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
        chapter = next((ch for ch in doc.get("chapters", []) if ch.get("id") == chapter_id), None)
        if not chapter: raise HTTPException(status_code=404, detail="Chương không tồn tại.")
        rag_url = os.environ.get("AGENTIC_RAG_URL")
        if rag_url:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(f"{rag_url}/api/inference/grammar-check", json={"text": chapter.get("content", "")[:5000]})
                    if resp.status_code == 200: return resp.json()
            except Exception as e: logger.warning(f"RAG grammar check failed: {e}")
        return {"score": 100, "message": "Dịch vụ AI kiểm tra ngữ pháp hiện không khả dụng."}

    @staticmethod
    async def generate_cover(document_id: str, style: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc: raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
        rag_url = os.environ.get("AGENTIC_RAG_URL")
        if rag_url:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(f"{rag_url}/api/inference/generate-cover", json={"title": doc.get("title", ""), "description": doc.get("description", ""), "style": style})
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("cover_url"):
                            await db["documents"].update_one({"_id": document_id}, {"$set": {"cover_url": data["cover_url"], "updated_at": datetime.utcnow()}})
                        return data
            except Exception as e: logger.warning(f"RAG cover generation failed: {e}")
        return {"message": "Dịch vụ tạo ảnh bìa bằng AI hiện chưa khả dụng."}

    @staticmethod
    async def notify_purchase(document_id: str, buyer_id: str):
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id})
        if not doc: return
        author_id = doc.get("author_id")
        if not author_id: return
        buyer = await db["users"].find_one({"_id": buyer_id}, {"full_name": 1})
        buyer_name = buyer.get("full_name", "Một độc giả") if buyer else "Một độc giả"
        notification = {
            "_id": str(uuid.uuid4()),
            "user_id": author_id,
            "title": "Giao dịch mới",
            "message": f"{buyer_name} vừa mua tài liệu '{doc.get('title', '')}'.",
            "is_read": False,
            "type": "purchase",
            "created_at": datetime.utcnow(),
        }
        await db["notifications"].insert_one(notification)
        if db_client.redis:
            await db_client.redis.publish(
                f"user_notifications:{author_id}",
                json.dumps({"title": notification["title"], "body": notification["message"]})
            )
        logger.info(f"Purchase notification sent to author {author_id} for document {document_id}")

    @staticmethod
    async def soft_delete_document(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["documents"].update_one(
            {"_id": document_id, "author_id": str(current_user.id), "is_deleted": {"$ne": True}},
            {"$set": {"is_deleted": True, "deleted_at": datetime.utcnow()}}
        )
        if res.modified_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu hoặc bạn không có quyền thực hiện.")
        logger.info(f"Author {current_user.id} moved document {document_id} to trash")
        return {"message": "Đã chuyển tài liệu vào thùng rác thành công."}

    @staticmethod
    async def restore_document(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["documents"].update_one(
            {"_id": document_id, "author_id": str(current_user.id), "is_deleted": True},
            {"$set": {"is_deleted": False, "deleted_at": None}}
        )
        if res.modified_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu trong thùng rác.")
        logger.info(f"Author {current_user.id} restored document {document_id} from trash")
        return {"message": "Đã khôi phục tài liệu thành công."}

    @staticmethod
    async def get_trash(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        docs = await db["documents"].find(
            {"author_id": str(current_user.id), "is_deleted": True}
        ).sort("deleted_at", -1).to_list(length=100)
        return [
            {
                "id": str(b["_id"]),
                "title": b.get("title", ""),
                "deleted_at": b["deleted_at"].isoformat() if isinstance(b.get("deleted_at"), datetime) else b.get("deleted_at"),
            }
            for b in docs
        ]

    @staticmethod
    async def set_flash_sale(document_id: str, data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
        
        flash_sale_price = int(data.get("price", 0))
        expires_at = datetime.fromisoformat(data["expires_at"])
        
        await db["documents"].update_one(
            {"_id": document_id},
            {"$set": {
                "flash_sale": {
                    "price_dl": flash_sale_price,
                    "expires_at": expires_at,
                    "is_active": True
                },
                "updated_at": datetime.utcnow()
            }}
        )
        logger.info(f"Flash sale set for document {document_id} at {flash_sale_price} dl until {expires_at}")
        return {"message": f"Chương trình Flash Sale đã được thiết lập thành công (Giá: {flash_sale_price} dl)."}

    @staticmethod
    async def get_conversion_rate(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        views = doc.get("views", 1)
        sales = await db["purchases"].count_documents({"item_id": document_id, "item_type": "document"})
        
        conversion_rate = (sales / views) * 100 if views > 0 else 0
        return {
            "document_id": document_id,
            "views": views,
            "sales": sales,
            "conversion_rate_percent": round(conversion_rate, 2)
        }

    @staticmethod
    async def get_buyer_list(document_id: str, current_user) -> list:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        purchases = await db["purchases"].find({"item_id": document_id, "item_type": "document"}).to_list(length=1000)
        buyer_ids = [p["user_id"] for p in purchases]
        
        buyers = await db["users"].find({"_id": {"$in": buyer_ids}}, {"full_name": 1, "email": 1, "avatar_url": 1}).to_list(length=1000)
        result = []
        for b in buyers:
            p = next((x for x in purchases if x["user_id"] == str(b["_id"])), None)
            result.append({
                "user_id": str(b["_id"]),
                "full_name": b.get("full_name", ""),
                "email": b.get("email", ""),
                "avatar_url": b.get("avatar_url"),
                "purchased_at": p["purchased_at"].isoformat() if p and isinstance(p.get("purchased_at"), datetime) else None
            })
        return result

    # Monetization methods
    @staticmethod
    async def create_subscription_plan(plan_data: dict, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        if current_user.role != 'AUTHOR':
            raise HTTPException(status_code=403, detail="Chỉ tác giả mới có quyền tạo gói đăng ký hội viên.")
        
        plan_doc = {
            "_id": str(uuid.uuid4()),
            "author_id": str(current_user.id),
            "name": plan_data["name"],
            "description": plan_data["description"],
            "price_dl": plan_data.get("price_dl"),
            "benefits": plan_data.get("benefits", []),
            "created_at": datetime.utcnow()
        }
        await db["subscription_plans"].insert_one(plan_doc)
        logger.info(f"Author {current_user.id} created a new subscription plan: {plan_doc['name']}")
        return plan_doc

    @staticmethod
    async def subscribe_to_author(plan_id: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        plan = await db["subscription_plans"].find_one({"_id": plan_id})
        if not plan:
            raise HTTPException(status_code=404, detail="Gói đăng ký không tồn tại trên hệ thống.")
        
        author_id = plan["author_id"]
        if author_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Bạn không thể đăng ký gói hội viên của chính mình.")
            
        price = plan.get("price_dl", 0)
        user = await db["users"].find_one({"_id": str(current_user.id)})
        if not user or user.get("wallet_balance", 0) < price:
            raise HTTPException(status_code=400, detail=f"Số dư tài khoản không đủ để thực hiện đăng ký (Cần {price} dl).")
            

        await db["users"].update_one({"_id": str(current_user.id)}, {"$inc": {"wallet_balance": -price}})
        await db["users"].update_one({"_id": author_id}, {"$inc": {"wallet_balance": price}})
        
        subscription = {
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "author_id": author_id,
            "plan_id": plan_id,
            "start_date": datetime.utcnow(),
            "end_date": datetime.utcnow() + timedelta(days=30),
            "status": "ACTIVE"
        }
        await db["subscriptions"].insert_one(subscription)
        
        tx_buyer = Transaction(
            user_id=str(current_user.id),
            type=TransactionType.SUBSCRIPTION,
            amount=-price,
            note=f"Đăng ký hội viên: {plan['name']} (Tác giả ID: {author_id})"
        )
        tx_seller = Transaction(
            user_id=author_id,
            type=TransactionType.RECEIVE,
            amount=price,
            note=f"Hội viên mới đăng ký: {plan['name']} (User ID: {current_user.id})"
        )
        await db["transactions"].insert_many([tx_buyer.model_dump(by_alias=True), tx_seller.model_dump(by_alias=True)])
        
        logger.info(f"User {current_user.id} subscribed to author {author_id} plan {plan_id}")
        return {"message": "Đăng ký hội viên thành công.", "end_date": subscription["end_date"]}

    @staticmethod
    async def get_author_plans(author_id: str):
        db = db_client.mongodb.get_default_database()
        cursor = db["subscription_plans"].find({"author_id": author_id})
        return await cursor.to_list(length=10)

    @staticmethod
    async def tip_author(author_id: str, amount: int, current_user: UserInDB, message: str = ""):
        db = db_client.mongodb.get_default_database()
        if author_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Bạn không thể tự tặng dl cho chính mình.")
            
        user = await db["users"].find_one({"_id": str(current_user.id)})
        if not user or user.get("wallet_balance", 0) < amount:
            raise HTTPException(status_code=400, detail=f"Số dư không đủ để thực hiện ủng hộ (Cần {amount} dl).")
            
        await db["users"].update_one({"_id": str(current_user.id)}, {"$inc": {"wallet_balance": -amount}})
        await db["users"].update_one({"_id": author_id}, {"$inc": {"wallet_balance": amount}})
        
        tx_sender = Transaction(
            user_id=str(current_user.id),
            type=TransactionType.TIP,
            amount=-amount,
            note=f"Ủng hộ tác giả: {message}"
        )
        tx_receiver = Transaction(
            user_id=author_id,
            type=TransactionType.RECEIVE,
            amount=amount,
            note=f"Nhận ủng hộ từ người dùng: {message}"
        )
        await db["transactions"].insert_many([tx_sender.model_dump(by_alias=True), tx_receiver.model_dump(by_alias=True)])
        
        logger.info(f"User {current_user.id} tipped {amount} dl to author {author_id}")
        return {"message": f"Bạn đã gửi {amount} dl ủng hộ tác giả thành công."}
