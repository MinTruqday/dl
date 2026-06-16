import httpx
from datetime import datetime, timezone
from core.config import settings
from core.database import db_client
from core.repositories.base import RepositoryFactory
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

class CollaborationService:
    @staticmethod
    async def log_activity(document_id: str, user_name: str, action: str, details: str, db=None):
        db = db or db_client.mongodb.get_default_database()
        await RepositoryFactory.get("collaboration_activities").insert_one({"_id": str(uuid7()), "document_id": document_id, "user_name": user_name, "action": action, "details": details, "timestamp": datetime.now(timezone.utc)})

    @staticmethod
    async def send_collaboration_invite(document_id: str, invitee_email: str, role: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id, "creator_id": str(current_user.get("id"))})
        if not doc: raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        invitee = None
        try:
            async with httpx.AsyncClient() as client:
                if (resp := await client.get(f"{settings.MANAGEMENT_URL}/nguoi-dung/thu-dien/{invitee_email}", timeout=settings.DEFAULT_HTTP_TIMEOUT)).status_code == 200: invitee = resp.json().get("data")
        except Exception: pass
        if not invitee: raise HTTPException(status_code=404, detail="Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        if str(invitee["_id"]) == str(current_user.get("id")): raise HTTPException(status_code=400, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        if await RepositoryFactory.get("collaboration_invites").find_one({"document_id": document_id, "invitee_id": str(invitee["_id"]), "status": "PENDING"}): raise HTTPException(status_code=400, detail="Lỗi truy xuất cơ sở dữ liệu hệ thống")
        if str(invitee["_id"]) in doc.get("coauthors", []): raise HTTPException(status_code=400, detail="Lỗi truy xuất cơ sở dữ liệu hệ thống")
        invite = {"_id": str(uuid7()), "document_id": document_id, "document_title": doc.get("title", "Untitled Document"), "inviter_id": str(current_user.get("id")), "inviter_name": current_user.get("full_name"), "invitee_id": str(invitee["_id"]), "role": role, "status": "PENDING", "created_at": datetime.now(timezone.utc)}
        await RepositoryFactory.get("collaboration_invites").insert_one(invite)
        await CollaborationService.log_activity(document_id, current_user.get("full_name"), "Send invitation", "A new editorial collaboration invitation has been processed and dispatched")
        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", "invite_id": invite["_id"]}

    @staticmethod
    async def get_my_collaboration_invites(current_user, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        return await RepositoryFactory.get("collaboration_invites").find({"invitee_id": str(current_user.get("id")), "status": "PENDING"}).sort("created_at", -1).to_list(length=100)

    @staticmethod
    async def respond_to_collaboration_invite(invite_id: str, status: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        invite = await RepositoryFactory.get("collaboration_invites").find_one({"_id": invite_id, "invitee_id": str(current_user.get("id")), "status": "PENDING"})
        if not invite: raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        if status not in ["ACCEPTED", "REJECTED"]: raise HTTPException(status_code=400, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        await RepositoryFactory.get("collaboration_invites").update_one({"_id": invite_id}, {"$set": {"status": status, "responded_at": datetime.now(timezone.utc)}})
        if status == "ACCEPTED": await RepositoryFactory.get("documents").update_one({"_id": invite["document_id"]}, {"$push": {"coauthors": str(current_user.get("id"))}, "$set": {"updated_at": datetime.now(timezone.utc)}})
        await CollaborationService.log_activity(invite["document_id"], current_user.get("full_name"), "Accepted" if status == "ACCEPTED" else "Declined", "The recipient has officially registered their response")
        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}

    @staticmethod
    async def get_collaborators(document_id: str, current_user, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        invites = await RepositoryFactory.get("collaboration_invites").find({"document_id": document_id, "status": "ACCEPTED"}).to_list(length=100)
        collaborators = []
        for inv in invites:
            user_info = None
            try:
                async with httpx.AsyncClient() as client:
                    if (resp := await client.get(f"{settings.MANAGEMENT_URL}/nguoi-dung/{inv['invitee_id']}", timeout=settings.DEFAULT_HTTP_TIMEOUT)).status_code == 200: user_info = resp.json().get("data")
            except Exception: pass
            if user_info: collaborators.append({"collaboration_id": inv["_id"], "user_id": inv["invitee_id"], "email": user_info.get("email", ""), "full_name": user_info.get("full_name", "User"), "role": inv.get("role", "editor")})
        return collaborators

    @staticmethod
    async def remove_collaborator(collaboration_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        invite = await RepositoryFactory.get("collaboration_invites").find_one({"_id": collaboration_id})
        if not invite: raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        if not await RepositoryFactory.get("documents").find_one({"_id": invite["document_id"], "creator_id": str(current_user.get("id"))}): raise HTTPException(status_code=403, detail="Lỗi xử lý tài khoản")
        await RepositoryFactory.get("documents").update_one({"_id": invite["document_id"]}, {"$pull": {"coauthors": invite["invitee_id"]}})
        await RepositoryFactory.get("collaboration_invites").delete_one({"_id": collaboration_id})
        await CollaborationService.log_activity(invite["document_id"], current_user.get("full_name"), "Collaborator removed", "The specified collaborator has been effectively removed")
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}

    @staticmethod
    async def get_activities(document_id: str, current_user, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        activities = await RepositoryFactory.get("collaboration_activities").find({"document_id": document_id}).sort("timestamp", -1).limit(50).to_list(length=50)
        return [{"id": act["_id"], "user_name": act["user_name"], "action": act["action"], "details": act["details"], "timestamp": (act["timestamp"].isoformat() if isinstance(act.get("timestamp"), datetime) else act.get("timestamp"))} for act in activities]

    @staticmethod
    async def transfer_ownership(document_id: str, target_user_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id, "creator_id": str(current_user.get("id"))})
        if not doc: raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        target_user = None
        try:
            async with httpx.AsyncClient() as client:
                if (resp := await client.get(f"{settings.MANAGEMENT_URL}/nguoi-dung/{target_user_id}", timeout=settings.DEFAULT_HTTP_TIMEOUT)).status_code == 200: target_user = resp.json().get("data")
        except Exception: pass
        if not target_user: raise HTTPException(status_code=404, detail="Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        if target_user_id not in doc.get("coauthors", []): raise HTTPException(status_code=400, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        await RepositoryFactory.get("documents").update_one({"_id": document_id}, {"$set": {"creator_id": target_user_id, "updated_at": datetime.now(timezone.utc)}, "$pull": {"coauthors": target_user_id}})
        await RepositoryFactory.get("documents").update_one({"_id": document_id}, {"$push": {"coauthors": str(current_user.get("id"))}})
        await CollaborationService.log_activity(document_id, current_user.get("full_name"), "Transfer ownership", "The primary administrative ownership rights of the document have been securely reassigned")
        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}

    @staticmethod
    async def update_status(document_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        await RepositoryFactory.get("collaboration_status").update_one({"document_id": document_id, "user_id": str(current_user.get("id"))}, {"$set": {"last_seen": datetime.now(timezone.utc), "full_name": current_user.get("full_name")}}, upsert=True)
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}

    @staticmethod
    async def get_online_collaborators(document_id: str, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        online_users = await RepositoryFactory.get("collaboration_status").find({"document_id": document_id}).to_list(length=100)
        return [{"user_id": u["user_id"], "full_name": u.get("full_name", "Collaborator"), "status": "online" if ((u.get("last_seen").timestamp() if isinstance(u.get("last_seen"), datetime) else 0) > cutoff) else "offline"} for u in online_users]

    @staticmethod
    async def update_collaborator_role(collaboration_id: str, role: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        invite = await RepositoryFactory.get("collaboration_invites").find_one({"_id": collaboration_id})
        if not invite: raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        if not await RepositoryFactory.get("documents").find_one({"_id": invite["document_id"], "creator_id": str(current_user.get("id"))}): raise HTTPException(status_code=403, detail="Lỗi xử lý tài khoản")
        if role not in ["editor", "viewer"]: raise HTTPException(status_code=400, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        await RepositoryFactory.get("collaboration_invites").update_one({"_id": collaboration_id}, {"$set": {"role": role}})
        await CollaborationService.log_activity(invite["document_id"], current_user.get("full_name"), "Update role", "Specific access privileges and system roles modified")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}

    @staticmethod
    async def send_memo(document_id: str, message: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        memo = {"_id": str(uuid7()), "document_id": document_id, "sender_name": current_user.get("full_name"), "sender_id": str(current_user.get("id")), "message": message, "timestamp": datetime.now(timezone.utc)}
        await RepositoryFactory.get("collaboration_memos").insert_one(memo)
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", "memo": memo}

    @staticmethod
    async def get_memos(document_id: str, current_user, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        memos = await RepositoryFactory.get("collaboration_memos").find({"document_id": document_id}).sort("timestamp", 1).limit(100).to_list(length=100)
        return [{"id": m["_id"], "sender_name": m["sender_name"], "sender_id": m["sender_id"], "message": m["message"], "timestamp": (m["timestamp"].isoformat() if isinstance(m.get("timestamp"), datetime) else m.get("timestamp"))} for m in memos]

    @staticmethod
    async def update_collab_access(document_id: str, access_level: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "creator_id": str(current_user.get("id"))}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        if access_level not in ["invite_only", "anyone_with_link"]: raise HTTPException(status_code=400, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        await RepositoryFactory.get("documents").update_one({"_id": document_id}, {"$set": {"collab_access_level": access_level}})
        await CollaborationService.log_activity(document_id, current_user.get("full_name"), "Permission settings", "Core collaborative access permissions adjusted")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", "collab_access_level": access_level}

    @staticmethod
    async def get_sent_pending_invites(document_id: str, current_user, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "creator_id": str(current_user.get("id"))}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return await RepositoryFactory.get("collaboration_invites").find({"document_id": document_id, "status": "PENDING"}).sort("created_at", -1).to_list(length=100)

    @staticmethod
    async def revoke_invite(invite_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        invite = await RepositoryFactory.get("collaboration_invites").find_one({"_id": invite_id, "status": "PENDING"})
        if not invite: raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        if not await RepositoryFactory.get("documents").find_one({"_id": invite["document_id"], "creator_id": str(current_user.get("id"))}): raise HTTPException(status_code=403, detail="Lỗi xử lý tài khoản")
        await RepositoryFactory.get("collaboration_invites").delete_one({"_id": invite_id})
        await CollaborationService.log_activity(invite["document_id"], current_user.get("full_name"), "Invitation revoked", "The active collaboration invitation token securely invalidated")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}

    @staticmethod
    async def get_contribution_stats(document_id: str, current_user, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        stats = await RepositoryFactory.get("collaboration_activities").aggregate([{"$match": {"document_id": document_id}}, {"$group": {"_id": "$user_name", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]).to_list(length=100)
        return [{"user_name": s["_id"], "count": s["count"]} for s in stats]

    @staticmethod
    async def create_snapshot(document_id: str, version_name: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id, "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]})
        if not doc: raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        snapshot = {"_id": str(uuid7()), "document_id": document_id, "version_name": version_name, "content": doc.get("content", ""), "created_by": current_user.get("full_name"), "timestamp": datetime.now(timezone.utc)}
        await RepositoryFactory.get("collaboration_drafts").insert_one(snapshot)
        await CollaborationService.log_activity(document_id, current_user.get("full_name"), "Create draft", "Structural milestone snapshot permanently recorded")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", "snapshot": snapshot}

    @staticmethod
    async def get_snapshots(document_id: str, current_user, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        drafts = await RepositoryFactory.get("collaboration_drafts").find({"document_id": document_id}).sort("timestamp", -1).to_list(length=100)
        return [{"id": d["_id"], "version_name": d["version_name"], "created_by": d["created_by"], "timestamp": (d["timestamp"].isoformat() if isinstance(d.get("timestamp"), datetime) else d.get("timestamp"))} for d in drafts]

    @staticmethod
    async def acquire_lock(document_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        if (existing := await RepositoryFactory.get("collaboration_locks").find_one({"document_id": document_id})):
            if (existing.get("locked_at").timestamp() if isinstance(existing.get("locked_at"), datetime) else 0) > cutoff and existing.get("user_id") != str(current_user.get("id")):
                raise HTTPException(status_code=400, detail="Lỗi truy xuất cơ sở dữ liệu hệ thống")
        await RepositoryFactory.get("collaboration_locks").update_one({"document_id": document_id}, {"$set": {"user_id": str(current_user.get("id")), "user_name": current_user.get("full_name"), "locked_at": datetime.now(timezone.utc)}}, upsert=True)
        await CollaborationService.log_activity(document_id, current_user.get("full_name"), "Document locked", "Exclusive access token acquired")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}

    @staticmethod
    async def release_lock(document_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        if (existing := await RepositoryFactory.get("collaboration_locks").find_one({"document_id": document_id})) and existing.get("user_id") == str(current_user.get("id")):
            await RepositoryFactory.get("collaboration_locks").delete_one({"document_id": document_id})
            await CollaborationService.log_activity(document_id, current_user.get("full_name"), "Unlock document", "Exclusive editorial lock safely released")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}

    @staticmethod
    async def get_lock_status(document_id: str, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        if not (existing := await RepositoryFactory.get("collaboration_locks").find_one({"document_id": document_id})): return {"is_locked": False}
        if (existing.get("locked_at").timestamp() if isinstance(existing.get("locked_at"), datetime) else 0) <= datetime.now(timezone.utc).timestamp() - 60: return {"is_locked": False}
        return {"is_locked": True, "user_id": existing.get("user_id"), "user_name": existing.get("user_name"), "locked_at": (existing.get("locked_at").isoformat() if isinstance(existing.get("locked_at"), datetime) else None)}

    @staticmethod
    async def generate_invite_code(document_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "creator_id": str(current_user.get("id"))}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        invite_code = str(uuid7())[:8].upper()
        await RepositoryFactory.get("collaboration_invite_codes").update_one({"document_id": document_id}, {"$set": {"invite_code": invite_code, "created_at": datetime.now(timezone.utc)}}, upsert=True)
        await CollaborationService.log_activity(document_id, current_user.get("full_name"), "Generate collaboration code", "Secure time-limited invitation token generated")
        return {"invite_code": invite_code}

    @staticmethod
    async def join_via_invite_code(invite_code: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        if not (code_entry := await RepositoryFactory.get("collaboration_invite_codes").find_one({"invite_code": invite_code.upper()})): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        if not (doc := await RepositoryFactory.get("documents").find_one({"_id": code_entry["document_id"]})): raise HTTPException(status_code=404, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        if doc.get("creator_id") == str(current_user.get("id")) or str(current_user.get("id")) in doc.get("coauthors", []): raise HTTPException(status_code=400, detail="Lỗi truy xuất cơ sở dữ liệu hệ thống")
        await RepositoryFactory.get("documents").update_one({"_id": code_entry["document_id"]}, {"$push": {"coauthors": str(current_user.get("id"))}, "$set": {"updated_at": datetime.now(timezone.utc)}})
        await RepositoryFactory.get("collaboration_invites").insert_one({"_id": str(uuid7()), "document_id": code_entry["document_id"], "document_title": doc.get("title", "Untitled Document"), "inviter_id": doc["creator_id"], "inviter_name": "Owner", "invitee_id": str(current_user.get("id")), "role": "editor", "status": "ACCEPTED", "created_at": datetime.now(timezone.utc), "responded_at": datetime.now(timezone.utc)})
        await CollaborationService.log_activity(code_entry["document_id"], current_user.get("full_name"), "Join via code", "Authenticated user successfully claimed invitation token")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", "document_id": code_entry["document_id"]}

    @staticmethod
    async def create_task(document_id: str, task_desc: str, assigned_to: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        task = {"_id": str(uuid7()), "document_id": document_id, "task_desc": task_desc, "is_done": False, "assigned_to": assigned_to or "Unassigned", "created_by": current_user.get("full_name"), "created_at": datetime.now(timezone.utc)}
        await RepositoryFactory.get("collaboration_tasks").insert_one(task)
        await CollaborationService.log_activity(document_id, current_user.get("full_name"), "Create task", "Structured operational assignment successfully integrated")
        return {"task": task}

    @staticmethod
    async def get_tasks(document_id: str, current_user, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        tasks = await RepositoryFactory.get("collaboration_tasks").find({"document_id": document_id}).sort("created_at", -1).to_list(length=100)
        return [{"id": t["_id"], "task_desc": t["task_desc"], "is_done": t["is_done"], "assigned_to": t["assigned_to"], "created_by": t["created_by"], "created_at": (t["created_at"].isoformat() if isinstance(t.get("created_at"), datetime) else t.get("created_at"))} for t in tasks]

    @staticmethod
    async def update_task(task_id: str, is_done: bool, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        task = await RepositoryFactory.get("collaboration_tasks").find_one({"_id": task_id})
        if not task: raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        if not await RepositoryFactory.get("documents").find_one({"_id": task["document_id"], "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]}): raise HTTPException(status_code=403, detail="Lỗi xử lý tài khoản")
        await RepositoryFactory.get("collaboration_tasks").update_one({"_id": task_id}, {"$set": {"is_done": is_done}})
        await CollaborationService.log_activity(task["document_id"], current_user.get("full_name"), "Update task", "Execution status of designated collaborative task modified")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}

    @staticmethod
    async def add_task_comment(task_id: str, comment_text: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        task = await RepositoryFactory.get("collaboration_tasks").find_one({"_id": task_id})
        if not task: raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        if not await RepositoryFactory.get("documents").find_one({"_id": task["document_id"], "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]}): raise HTTPException(status_code=403, detail="Lỗi xử lý tài khoản")
        comment = {"_id": str(uuid7()), "task_id": task_id, "sender_name": current_user.get("full_name"), "comment_text": comment_text, "timestamp": datetime.now(timezone.utc)}
        await RepositoryFactory.get("collaboration_task_comments").insert_one(comment)
        return {"comment": comment}

    @staticmethod
    async def get_task_comments(task_id: str, current_user, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        task = await RepositoryFactory.get("collaboration_tasks").find_one({"_id": task_id})
        if not task: raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        if not await RepositoryFactory.get("documents").find_one({"_id": task["document_id"], "$or": [{"creator_id": str(current_user.get("id"))}, {"coauthors": str(current_user.get("id"))}]}): raise HTTPException(status_code=403, detail="Lỗi xử lý tài khoản")
        comments = await RepositoryFactory.get("collaboration_task_comments").find({"task_id": task_id}).sort("timestamp", 1).to_list(length=100)
        return [{"id": c["_id"], "sender_name": c["sender_name"], "comment_text": c["comment_text"], "timestamp": (c["timestamp"].isoformat() if isinstance(c.get("timestamp"), datetime) else c.get("timestamp"))} for c in comments]