import uuid
from datetime import datetime, timezone

from core.config import settings
from core.database import db_client
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7


class CollaborationService:

    @staticmethod
    async def log_activity(
        document_id: str, user_name: str, action: str, details: str, db=None
    ):
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db["collaboration_activities"].insert_one(
            {
                "_id": str(uuid7()),
                "document_id": document_id,
                "user_name": user_name,
                "action": action,
                "details": details,
                "timestamp": datetime.now(timezone.utc),
            }
        )

    @staticmethod
    async def send_collaboration_invite(
        document_id: str, invitee_email: str, role: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {"_id": document_id, "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền truy cập",
            )
        import httpx

        invitee = None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.PROVISION_URL}/nguoi-dung/noi-bo/email/{invitee_email}",
                    timeout=3.0,
                )
                if resp.status_code == 200:
                    invitee = resp.json().get("data")
        except Exception:
            pass
        if not invitee:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy người dùng với email này"
            )
        invitee_id = str(invitee["_id"])
        if invitee_id == str(current_user.id):
            raise HTTPException(
                status_code=400, detail="Không thể tự mời bản thân làm cộng tác viên"
            )
        existing_invite = await db["collaboration_invites"].find_one(
            {"document_id": document_id, "invitee_id": invitee_id, "status": "PENDING"}
        )
        if existing_invite:
            raise HTTPException(
                status_code=400, detail="Có lời mời đang chờ người này xác nhận"
            )
        coauthors = doc.get("coauthors", [])
        if invitee_id in coauthors:
            raise HTTPException(status_code=400, detail="Người này đã là cộng tác viên")
        invite = {
            "_id": str(uuid7()),
            "document_id": document_id,
            "document_title": doc.get("title", "Tài liệu không tên"),
            "inviter_id": str(current_user.id),
            "inviter_name": current_user.full_name,
            "invitee_id": invitee_id,
            "role": role,
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc),
        }
        await db["collaboration_invites"].insert_one(invite)
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Gửi lời mời",
            f"Đã gửi lời mời cộng tác tới {invitee_email} với vai trò {role}",
        )
        logger.info(
            f"Người dùng {current_user.id} mời {invitee_id} chỉnh sửa tài liệu {document_id}"
        )
        return {"message": "Đã gửi lời mời cộng tác", "invite_id": invite["_id"]}

    @staticmethod
    async def get_my_collaboration_invites(current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        invites = (
            await db["collaboration_invites"]
            .find({"invitee_id": str(current_user.id), "status": "PENDING"})
            .sort("created_at", -1)
            .to_list(length=100)
        )
        return invites

    @staticmethod
    async def respond_to_collaboration_invite(
        invite_id: str, status: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        invite = await db["collaboration_invites"].find_one(
            {"_id": invite_id, "invitee_id": str(current_user.id), "status": "PENDING"}
        )
        if not invite:
            raise HTTPException(
                status_code=404, detail="Lời mời không tồn tại hoặc đã xử lý"
            )
        if status not in ["ACCEPTED", "REJECTED"]:
            raise HTTPException(
                status_code=400, detail="Trạng thái phản hồi không hợp lệ"
            )
        await db["collaboration_invites"].update_one(
            {"_id": invite_id},
            {"$set": {"status": status, "responded_at": datetime.now(timezone.utc)}},
        )
        if status == "ACCEPTED":
            await db["documents"].update_one(
                {"_id": invite["document_id"]},
                {
                    "$push": {"coauthors": str(current_user.id)},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
            )
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Chấp nhận" if status == "ACCEPTED" else "Từ chối",
            (
                "Đã chấp nhận lời mời cộng tác"
                if status == "ACCEPTED"
                else "Đã từ chối lời mời cộng tác"
            ),
        )
        logger.info(
            f"Người dùng {current_user.id} {status} lời mời cộng tác {invite_id}"
        )
        return {
            "message": f"Đã {('chấp nhận' if status == 'ACCEPTED' else 'từ chối')} lời mời cộng tác"
        }

    @staticmethod
    async def get_collaborators(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {
                "_id": document_id,
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền truy cập",
            )
        invites = (
            await db["collaboration_invites"]
            .find({"document_id": document_id, "status": "ACCEPTED"})
            .to_list(length=100)
        )
        collaborators = []
        for inv in invites:
            import httpx

            user_info = None
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"{settings.PROVISION_URL}/nguoi-dung/noi-bo/{inv['invitee_id']}",
                        timeout=3.0,
                    )
                    if resp.status_code == 200:
                        user_info = resp.json().get("data")
            except Exception:
                pass
            if user_info:
                collaborators.append(
                    {
                        "collaboration_id": inv["_id"],
                        "user_id": inv["invitee_id"],
                        "email": user_info.get("email", ""),
                        "full_name": user_info.get("full_name", "Người dùng"),
                        "role": inv.get("role", "editor"),
                    }
                )
        return collaborators

    @staticmethod
    async def remove_collaborator(collaboration_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        invite = await db["collaboration_invites"].find_one({"_id": collaboration_id})
        if not invite:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy thông tin cộng tác"
            )
        doc = await db["documents"].find_one(
            {"_id": invite["document_id"], "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=403,
                detail="Không có quyền quản lý cộng tác viên tài liệu này",
            )
        await db["documents"].update_one(
            {"_id": invite["document_id"]},
            {"$pull": {"coauthors": invite["invitee_id"]}},
        )
        await db["collaboration_invites"].delete_one({"_id": collaboration_id})
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Xóa cộng tác viên",
            f"Đã xóa cộng tác viên có ID {invite['invitee_id']}",
        )
        logger.info(
            f"Chủ sở hữu {current_user.id} xóa cộng tác viên {invite['invitee_id']} khỏi tài liệu {invite['document_id']}"
        )
        return {"message": "Đã xóa người dùng khỏi danh sách cộng tác"}

    @staticmethod
    async def get_activities(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {
                "_id": document_id,
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền truy cập",
            )
        activities = (
            await db["collaboration_activities"]
            .find({"document_id": document_id})
            .sort("timestamp", -1)
            .limit(50)
            .to_list(length=50)
        )
        return [
            {
                "id": act["_id"],
                "user_name": act["user_name"],
                "action": act["action"],
                "details": act["details"],
                "timestamp": (
                    act["timestamp"].isoformat()
                    if isinstance(act.get("timestamp"), datetime)
                    else act.get("timestamp")
                ),
            }
            for act in activities
        ]

    @staticmethod
    async def transfer_ownership(
        document_id: str, target_user_id: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {"_id": document_id, "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền chuyển sở hữu",
            )
        import httpx

        target_user = None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.PROVISION_URL}/nguoi-dung/noi-bo/{target_user_id}",
                    timeout=3.0,
                )
                if resp.status_code == 200:
                    target_user = resp.json().get("data")
        except Exception:
            pass
        if not target_user:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy thông tin người nhận chuyển nhượng",
            )
        if target_user_id not in doc.get("coauthors", []):
            raise HTTPException(
                status_code=400,
                detail="Chỉ cộng tác viên mới được nhận chuyển nhượng tài liệu",
            )
        await db["documents"].update_one(
            {"_id": document_id},
            {
                "$set": {
                    "author_id": target_user_id,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$pull": {"coauthors": target_user_id},
            },
        )
        await db["documents"].update_one(
            {"_id": document_id}, {"$push": {"coauthors": str(current_user.id)}}
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Chuyển sở hữu",
            f"Đã chuyển quyền sở hữu tài liệu cho {target_user.get('full_name')}",
        )
        logger.info(
            f"Đã chuyển quyền sở hữu tài liệu {document_id} từ {current_user.id} sang {target_user_id}"
        )
        return {"message": "Đã chuyển giao quyền sở hữu tài liệu"}

    @staticmethod
    async def update_status(document_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db["collaboration_status"].update_one(
            {"document_id": document_id, "user_id": str(current_user.id)},
            {
                "$set": {
                    "last_seen": datetime.now(timezone.utc),
                    "full_name": current_user.full_name,
                }
            },
            upsert=True,
        )
        return {"message": "Đã cập nhật trạng thái trực tuyến"}

    @staticmethod
    async def get_online_collaborators(document_id: str, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        online_users = (
            await db["collaboration_status"]
            .find({"document_id": document_id})
            .to_list(length=100)
        )
        result = []
        for u in online_users:
            last_seen = u.get("last_seen")
            last_seen_ts = (
                last_seen.timestamp() if isinstance(last_seen, datetime) else 0
            )
            is_online = last_seen_ts > cutoff
            result.append(
                {
                    "user_id": u["user_id"],
                    "full_name": u.get("full_name", "Cộng tác viên"),
                    "status": "online" if is_online else "offline",
                }
            )
        return result

    @staticmethod
    async def update_collaborator_role(
        collaboration_id: str, role: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        invite = await db["collaboration_invites"].find_one({"_id": collaboration_id})
        if not invite:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy thông tin cộng tác"
            )
        doc = await db["documents"].find_one(
            {"_id": invite["document_id"], "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=403,
                detail="Không có quyền quản lý cộng tác viên tài liệu này",
            )
        if role not in ["editor", "viewer"]:
            raise HTTPException(status_code=400, detail="Vai trò cộng tác không hợp lệ")
        await db["collaboration_invites"].update_one(
            {"_id": collaboration_id}, {"$set": {"role": role}}
        )
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Cập nhật vai trò",
            f"Đã thay đổi vai trò của cộng tác viên có ID {invite['invitee_id']} sang {role}",
        )
        return {"message": "Đã cập nhật vai trò cộng tác viên"}

    @staticmethod
    async def send_memo(document_id: str, message: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {
                "_id": document_id,
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền truy cập",
            )
        memo = {
            "_id": str(uuid7()),
            "document_id": document_id,
            "sender_name": current_user.full_name,
            "sender_id": str(current_user.id),
            "message": message,
            "timestamp": datetime.now(timezone.utc),
        }
        await db["collaboration_memos"].insert_one(memo)
        return {"message": "Đã gửi tin nhắn trao đổi", "memo": memo}

    @staticmethod
    async def get_memos(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {
                "_id": document_id,
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền truy cập",
            )
        memos = (
            await db["collaboration_memos"]
            .find({"document_id": document_id})
            .sort("timestamp", 1)
            .limit(100)
            .to_list(length=100)
        )
        return [
            {
                "id": m["_id"],
                "sender_name": m["sender_name"],
                "sender_id": m["sender_id"],
                "message": m["message"],
                "timestamp": (
                    m["timestamp"].isoformat()
                    if isinstance(m.get("timestamp"), datetime)
                    else m.get("timestamp")
                ),
            }
            for m in memos
        ]

    @staticmethod
    async def update_collab_access(
        document_id: str, access_level: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {"_id": document_id, "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền cập nhật cài đặt",
            )
        if access_level not in ["invite_only", "anyone_with_link"]:
            raise HTTPException(
                status_code=400, detail="Mức quyền truy cập không hợp lệ"
            )
        await db["documents"].update_one(
            {"_id": document_id}, {"$set": {"collab_access_level": access_level}}
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Cài đặt quyền",
            f"Đã cập nhật mức độ tiếp cận tài liệu thành: {access_level}",
        )
        return {
            "message": "Đã cập nhật quyền truy cập mặc định",
            "collab_access_level": access_level,
        }

    @staticmethod
    async def get_sent_pending_invites(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {"_id": document_id, "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền truy cập",
            )
        invites = (
            await db["collaboration_invites"]
            .find({"document_id": document_id, "status": "PENDING"})
            .sort("created_at", -1)
            .to_list(length=100)
        )
        return invites

    @staticmethod
    async def revoke_invite(invite_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        invite = await db["collaboration_invites"].find_one(
            {"_id": invite_id, "status": "PENDING"}
        )
        if not invite:
            raise HTTPException(
                status_code=404, detail="Lời mời không tồn tại hoặc đã được chấp nhận"
            )
        doc = await db["documents"].find_one(
            {"_id": invite["document_id"], "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="Không có quyền thu hồi lời mời này"
            )
        await db["collaboration_invites"].delete_one({"_id": invite_id})
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Thu hồi lời mời",
            "Đã thu hồi lời mời cộng tác chưa duyệt",
        )
        return {"message": "Đã thu hồi lời mời cộng tác"}

    @staticmethod
    async def get_contribution_stats(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {
                "_id": document_id,
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền xem thống kê",
            )
        pipeline = [
            {"$match": {"document_id": document_id}},
            {"$group": {"_id": "$user_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        stats = (
            await db["collaboration_activities"].aggregate(pipeline).to_list(length=100)
        )
        return [{"user_name": s["_id"], "count": s["count"]} for s in stats]

    @staticmethod
    async def create_snapshot(
        document_id: str, version_name: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {
                "_id": document_id,
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền truy cập",
            )
        snapshot = {
            "_id": str(uuid7()),
            "document_id": document_id,
            "version_name": version_name,
            "content": doc.get("content", ""),
            "created_by": current_user.full_name,
            "timestamp": datetime.now(timezone.utc),
        }
        await db["collaboration_drafts"].insert_one(snapshot)
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Tạo nháp",
            f"Đã lưu trữ phiên bản nháp cộng tác: {version_name}",
        )
        return {"message": "Bản nháp cộng tác đã được tạo", "snapshot": snapshot}

    @staticmethod
    async def get_snapshots(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {
                "_id": document_id,
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền truy cập",
            )
        drafts = (
            await db["collaboration_drafts"]
            .find({"document_id": document_id})
            .sort("timestamp", -1)
            .to_list(length=100)
        )
        return [
            {
                "id": d["_id"],
                "version_name": d["version_name"],
                "created_by": d["created_by"],
                "timestamp": (
                    d["timestamp"].isoformat()
                    if isinstance(d.get("timestamp"), datetime)
                    else d.get("timestamp")
                ),
            }
            for d in drafts
        ]

    @staticmethod
    async def acquire_lock(document_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {
                "_id": document_id,
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền truy cập",
            )
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        existing = await db["collaboration_locks"].find_one(
            {"document_id": document_id}
        )
        if existing:
            locked_at = existing.get("locked_at")
            locked_at_ts = (
                locked_at.timestamp() if isinstance(locked_at, datetime) else 0
            )
            if locked_at_ts > cutoff and existing.get("user_id") != str(
                current_user.id
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"Tài liệu hiện đang được khóa độc quyền bởi {existing.get('user_name')}",
                )
        await db["collaboration_locks"].update_one(
            {"document_id": document_id},
            {
                "$set": {
                    "user_id": str(current_user.id),
                    "user_name": current_user.full_name,
                    "locked_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Khóa tài liệu",
            "Đã kích hoạt chế độ khóa biên tập độc quyền",
        )
        return {"message": "Đã khóa tài liệu để biên tập"}

    @staticmethod
    async def release_lock(document_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        existing = await db["collaboration_locks"].find_one(
            {"document_id": document_id}
        )
        if existing and existing.get("user_id") == str(current_user.id):
            await db["collaboration_locks"].delete_one({"document_id": document_id})
            await CollaborationService.log_activity(
                document_id,
                current_user.full_name,
                "Mở khóa tài liệu",
                "Đã tắt chế độ khóa biên tập độc quyền",
            )
        return {"message": "Đã kết thúc biên tập và mở khóa tài liệu"}

    @staticmethod
    async def get_lock_status(document_id: str, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        existing = await db["collaboration_locks"].find_one(
            {"document_id": document_id}
        )
        if not existing:
            return {"is_locked": False}
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        locked_at = existing.get("locked_at")
        locked_at_ts = locked_at.timestamp() if isinstance(locked_at, datetime) else 0
        is_locked = locked_at_ts > cutoff
        if not is_locked:
            return {"is_locked": False}
        return {
            "is_locked": True,
            "user_id": existing.get("user_id"),
            "user_name": existing.get("user_name"),
            "locked_at": (
                existing.get("locked_at").isoformat()
                if isinstance(existing.get("locked_at"), datetime)
                else None
            ),
        }

    @staticmethod
    async def generate_invite_code(document_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {"_id": document_id, "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền sở hữu",
            )
        invite_code = str(uuid7())[:8].upper()
        await db["collaboration_invite_codes"].update_one(
            {"document_id": document_id},
            {
                "$set": {
                    "invite_code": invite_code,
                    "created_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Tạo mã cộng tác",
            f"Đã kích hoạt mã mời nhanh: {invite_code}",
        )
        return {"invite_code": invite_code}

    @staticmethod
    async def join_via_invite_code(invite_code: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        code_entry = await db["collaboration_invite_codes"].find_one(
            {"invite_code": invite_code.upper()}
        )
        if not code_entry:
            raise HTTPException(
                status_code=404, detail="Mã cộng tác không tồn tại hoặc đã hết hạn"
            )
        document_id = code_entry["document_id"]
        doc = await db["documents"].find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")
        if doc.get("author_id") == str(current_user.id):
            raise HTTPException(status_code=400, detail="Đã là chủ sở hữu tài liệu này")
        if str(current_user.id) in doc.get("coauthors", []):
            raise HTTPException(
                status_code=400, detail="Đã là cộng tác viên tài liệu này"
            )
        await db["documents"].update_one(
            {"_id": document_id},
            {
                "$push": {"coauthors": str(current_user.id)},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        await db["collaboration_invites"].insert_one(
            {
                "_id": str(uuid7()),
                "document_id": document_id,
                "document_title": doc.get("title", "Tài liệu không tên"),
                "inviter_id": doc["author_id"],
                "inviter_name": "Chủ sở hữu",
                "invitee_id": str(current_user.id),
                "role": "editor",
                "status": "ACCEPTED",
                "created_at": datetime.now(timezone.utc),
                "responded_at": datetime.now(timezone.utc),
            }
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Tham gia qua mã",
            "Đã gia nhập nhóm cộng tác viên biên tập thông qua mã mời nhanh",
        )
        return {
            "message": "Đã tham gia nhóm cộng tác biên tập",
            "document_id": document_id,
        }

    @staticmethod
    async def create_task(
        document_id: str, task_desc: str, assigned_to: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {
                "_id": document_id,
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền truy cập",
            )
        task = {
            "_id": str(uuid7()),
            "document_id": document_id,
            "task_desc": task_desc,
            "is_done": False,
            "assigned_to": assigned_to or "Chưa giao",
            "created_by": current_user.full_name,
            "created_at": datetime.now(timezone.utc),
        }
        await db["collaboration_tasks"].insert_one(task)
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Tạo nhiệm vụ",
            f"Đã thêm nhiệm vụ cộng tác mới: {task_desc} (Giao cho: {assigned_to or 'Chưa giao'})",
        )
        return {"task": task}

    @staticmethod
    async def get_tasks(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {
                "_id": document_id,
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Tài liệu không tồn tại hoặc không có quyền truy cập",
            )
        tasks = (
            await db["collaboration_tasks"]
            .find({"document_id": document_id})
            .sort("created_at", -1)
            .to_list(length=100)
        )
        return [
            {
                "id": t["_id"],
                "task_desc": t["task_desc"],
                "is_done": t["is_done"],
                "assigned_to": t["assigned_to"],
                "created_by": t["created_by"],
                "created_at": (
                    t["created_at"].isoformat()
                    if isinstance(t.get("created_at"), datetime)
                    else t.get("created_at")
                ),
            }
            for t in tasks
        ]

    @staticmethod
    async def update_task(task_id: str, is_done: bool, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        task = await db["collaboration_tasks"].find_one({"_id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Nhiệm vụ không tồn tại")
        doc = await db["documents"].find_one(
            {
                "_id": task["document_id"],
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="Không có quyền chỉnh sửa nhiệm vụ này"
            )
        await db["collaboration_tasks"].update_one(
            {"_id": task_id}, {"$set": {"is_done": is_done}}
        )
        await CollaborationService.log_activity(
            task["document_id"],
            current_user.full_name,
            "Cập nhật nhiệm vụ",
            "Đã đánh dấu nhiệm vụ '{task['task_desc']}' thành {('Hoàn thành' if is_done else 'Chưa xong')}",
        )
        return {"message": "Đã cập nhật nhiệm vụ"}

    @staticmethod
    async def add_task_comment(
        task_id: str, comment_text: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        task = await db["collaboration_tasks"].find_one({"_id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Nhiệm vụ không tồn tại")
        doc = await db["documents"].find_one(
            {
                "_id": task["document_id"],
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="Không có quyền thảo luận trong nhiệm vụ này"
            )
        comment = {
            "_id": str(uuid7()),
            "task_id": task_id,
            "sender_name": current_user.full_name,
            "comment_text": comment_text,
            "timestamp": datetime.now(timezone.utc),
        }
        await db["collaboration_task_comments"].insert_one(comment)
        return {"comment": comment}

    @staticmethod
    async def get_task_comments(task_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        task = await db["collaboration_tasks"].find_one({"_id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Nhiệm vụ không tồn tại")
        doc = await db["documents"].find_one(
            {
                "_id": task["document_id"],
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="Không có quyền truy cập thảo luận nhiệm vụ này"
            )
        comments = (
            await db["collaboration_task_comments"]
            .find({"task_id": task_id})
            .sort("timestamp", 1)
            .to_list(length=100)
        )
        return [
            {
                "id": c["_id"],
                "sender_name": c["sender_name"],
                "comment_text": c["comment_text"],
                "timestamp": (
                    c["timestamp"].isoformat()
                    if isinstance(c.get("timestamp"), datetime)
                    else c.get("timestamp")
                ),
            }
            for c in comments
        ]
