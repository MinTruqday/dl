from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone
import json
import asyncio
import uuid
from uuid6 import uuid7
from loguru import logger

class NotificationService:
    @staticmethod
    async def sse_generator(user_id: str):
        if not db_client.redis:
            yield {
                "event": "connected",
                "data": json.dumps({"status": "Notifications available (polling mode)"})
            }
            try:
                while True:
                    await asyncio.sleep(30)
                    yield {"event": "heartbeat", "data": ""}
            except asyncio.CancelledError:
                return

        try:
            pubsub = db_client.redis.pubsub()
            await pubsub.subscribe(f"user_notifications:{user_id}")
            
            yield {
                "event": "connected",
                "data": json.dumps({"status": "Listening for notifications"})
            }
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"].decode("utf-8"))
                        if "body" in data and "message" not in data:
                            data["message"] = data["body"]
                        elif "message" in data and "body" not in data:
                            data["body"] = data["message"]
                        payload = json.dumps(data)
                    except Exception:
                        if isinstance(message["data"], bytes):
                            payload = message["data"].decode("utf-8")
                        else:
                            payload = str(message["data"])
                    yield {
                        "event": "notification",
                        "data": payload
                    }
        except asyncio.CancelledError:
            logger.info(f"SSE notification stream cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"SSE generator error for user {user_id}: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"detail": "Mất kết nối với máy chủ thông báo."})
            }
        finally:
            if db_client.redis:
                await pubsub.unsubscribe(f"user_notifications:{user_id}")

    @staticmethod
    async def get_notifications(current_user):
        db = db_client.mongodb.get_default_database()
        cursor = db["notifications"].find({
            "$or": [
                {"target_user_id": str(current_user.id)},
                {"is_global": True}
            ]
        }).sort("created_at", -1).limit(20)
        
        notifs = []
        async for n in cursor:
            n["_id"] = str(n["_id"])
            if "body" in n and "message" not in n:
                n["message"] = n["body"]
            elif "message" in n and "body" not in n:
                n["body"] = n["message"]
            notifs.append(n)
        return notifs

    @staticmethod
    async def mark_notification_read(notif_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        res = await db["notifications"].update_one(
            {"_id": notif_id, "$or": [{"target_user_id": str(current_user.id)}, {"is_global": True}]},
            {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc)}}
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy thông báo.")
        return {"status": "ok"}

    @staticmethod
    async def trigger_test_notification(current_user):
        if not db_client.redis:
            raise HTTPException(status_code=503, detail="Dịch vụ Redis chưa sẵn sàng.")
            
        await db_client.redis.publish(
            f"user_notifications:{current_user.id}", 
            json.dumps({"title": "Thông báo thử nghiệm", "body": "Cập nhật hoàn tất"})
        )
        return {"status": "ok"}

    @staticmethod
    async def trigger_push_notif(title: str, body: str, current_user):
        db = db_client.mongodb.get_default_database()

        await db["notifications"].insert_one({
            "title": title,
            "body": body,
            "created_by": current_user.id,
            "created_at": datetime.now(timezone.utc),
            "is_global": True
        })
        
        if db_client.redis:
            await db_client.redis.publish("global_notifications", json.dumps({"title": title, "body": body}))
            
        logger.info(f"Push notification sent by admin {current_user.id}: {title}")
        return {"message": f"Đã gửi thông báo đẩy: {title}."}

    @staticmethod
    async def subscribe_newsletter(email: str) -> dict:
        db = db_client.mongodb.get_default_database()
        existing = await db["newsletter_subscribers"].find_one({"email": email})
        if existing:
            raise HTTPException(status_code=400, detail="Email này đã đăng ký nhận bản tin.")
        await db["newsletter_subscribers"].insert_one({
            "_id": str(uuid7()),
            "email": email,
            "subscribed_at": datetime.now(timezone.utc),
            "is_active": True,
        })
        logger.info(f"Newsletter subscription: {email}")
        return {"message": "Đăng ký nhận bản tin thành công."}

    @staticmethod
    async def unsubscribe_newsletter(email: str) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["newsletter_subscribers"].update_one(
            {"email": email},
            {"$set": {"is_active": False, "unsubscribed_at": datetime.now(timezone.utc)}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Email chưa đăng ký bản tin.")
        return {"message": "Đã hủy đăng ký bản tin."}

    @staticmethod
    async def get_system_notices() -> list:
        db = db_client.mongodb.get_default_database()
        now = datetime.now(timezone.utc)
        notices = await db["system_notices"].find({
            "is_active": True,
            "$or": [
                {"expires_at": {"$gt": now}},
                {"expires_at": None}
            ]
        }).sort("created_at", -1).to_list(length=10)
        return [
            {
                "_id": str(n["_id"]),
                "title": n.get("title", ""),
                "content": n.get("content", ""),
                "severity": n.get("severity", "info"),
                "created_at": n["created_at"].isoformat() if isinstance(n.get("created_at"), datetime) else n.get("created_at"),
            }
            for n in notices
        ]
    @staticmethod
    async def notify_document_update(document_id: str, title: str, author_id: str, author_name: str):
        db = db_client.mongodb.get_default_database()
        
        author = await db["users"].find_one({"_id": author_id}, {"blocked_users": 1})
        blocked_users = author.get("blocked_users", []) if author else []
        
        BATCH_SIZE = 1000
        last_id = None
        total_notified = 0
        
        while True:
            query = {"document_id": document_id}
            if last_id:
                query["_id"] = {"$gt": last_id}
            
            if blocked_users:
                query["user_id"] = {"$nin": blocked_users}
            
            libraries = await db["libraries"].find(query).sort("_id", 1).limit(BATCH_SIZE).to_list(length=BATCH_SIZE)
            if not libraries:
                break
            
            last_id = libraries[-1]["_id"]
            user_ids = [lib["user_id"] for lib in libraries]
            
            notifications = []
            for uid in user_ids:
                notif_id = str(uuid7())
                notifications.append({
                    "_id": notif_id,
                    "target_user_id": uid,
                    "title": f"Cập nhật mới: {title}",
                    "body": f"Tác giả {author_name} vừa cập nhật nội dung mới cho tài liệu bạn đang theo dõi.",
                    "link": f"/preview?slug={document_id}",
                    "created_at": datetime.now(timezone.utc),
                    "is_read": False
                })
                
                if db_client.redis:
                    await db_client.redis.publish(
                        f"user_notifications:{uid}", 
                        json.dumps({
                            "id": notif_id,
                            "title": f"Cập nhật mới: {title}",
                            "body": f"Tài liệu '{title}' vừa có chương mới!",
                            "link": f"/preview?slug={document_id}"
                        })
                    )
            
            if notifications:
                await db["notifications"].insert_many(notifications)
                total_notified += len(notifications)
        
        if total_notified > 0:
            logger.info(f"Document update notification sent for document {document_id} to {total_notified} users.")

    @staticmethod
    async def get_notification_settings(current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        settings = await db["notification_settings"].find_one({"user_id": str(current_user.id)})
        if not settings:
            return {
                "enable_comment_notifications": True,
                "enable_mention_notifications": True,
                "enable_system_notifications": True,
                "enable_email_digest": False,
            }
        return {
            "enable_comment_notifications": settings.get("enable_comment_notifications", True),
            "enable_mention_notifications": settings.get("enable_mention_notifications", True),
            "enable_system_notifications": settings.get("enable_system_notifications", True),
            "enable_email_digest": settings.get("enable_email_digest", False),
        }

    @staticmethod
    async def update_notification_settings(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["notification_settings"].update_one(
            {"user_id": str(current_user.id)},
            {"$set": {
                "enable_comment_notifications": data.get("enable_comment_notifications", True),
                "enable_mention_notifications": data.get("enable_mention_notifications", True),
                "enable_system_notifications": data.get("enable_system_notifications", True),
                "enable_email_digest": data.get("enable_email_digest", False),
                "updated_at": datetime.now(timezone.utc),
            }},
            upsert=True,
        )
        logger.info(f"Notification settings updated for user {current_user.id}")
        return {"message": "Đã cập nhật tùy chỉnh thông báo thành công."}

    @staticmethod
    async def mark_all_read(current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["notifications"].update_many(
            {"target_user_id": str(current_user.id), "is_read": False},
            {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc)}}
        )
        return {"message": "Đã đánh dấu tất cả thông báo là đã đọc.", "count": result.modified_count}

    @staticmethod
    async def notify_purchase(document_id: str, document_title: str, author_id: str, buyer_name: str):
        db = db_client.mongodb.get_default_database()
        notif_id = str(uuid7())
        notification = {
            "_id": notif_id,
            "target_user_id": author_id,
            "title": "Giao dịch mới",
            "body": f"{buyer_name} vừa mua tài liệu '{document_title}'.",
            "is_read": False,
            "type": "purchase",
            "created_at": datetime.now(timezone.utc),
        }
        await db["notifications"].insert_one(notification)
        if db_client.redis:
            await db_client.redis.publish(
                f"user_notifications:{author_id}",
                json.dumps({"title": notification["title"], "body": notification["body"]})
            )
        logger.info(f"Notification: Purchase notification sent to author {author_id}")


