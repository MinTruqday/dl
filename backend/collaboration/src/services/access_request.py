import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from src.core.infrastructure.mongo import mongo
from src.repositories.cooperation import CooperationRepository, DocumentRepository
from src.services.activity import ActivityService
from src.services.presence import PresenceService

class AccessRequestService:
    @staticmethod
    async def create_access_request(
        document_id: str, requested_role: str, message: str | None, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu yêu cầu")

        user_id = str(current_user.id)
        status_info = PresenceService.get_effective_collaboration_status(
            doc,
            user_id=user_id,
            is_admin=str(getattr(current_user, "role", "")).lower().endswith("admin"),
        )
        if status_info["is_effective_closed"]:
            raise HTTPException(
                status_code=403,
                detail="Tài liệu đã đóng hoàn toàn và không tiếp nhận yêu cầu xin quyền",
            )

        if str(doc.get("creator_id")) == user_id:
            raise HTTPException(
                status_code=400, detail="Bạn là chủ sở hữu của tài liệu này"
            )

        if user_id in (doc.get("coauthors") or []):
            raise HTTPException(
                status_code=400, detail="Bạn đã là cộng tác viên của tài liệu này"
            )

        if requested_role not in ["editor", "commenter", "viewer"]:
            raise HTTPException(status_code=400, detail="Quyền yêu cầu không hợp lệ")

        existing = await CooperationRepository.find_access_request(
            {"document_id": document_id, "user_id": user_id, "status": "PENDING"}
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Bạn đã gửi yêu cầu quyền truy cập cho tài liệu này và đang chờ duyệt",
            )

        req_doc = {
            "_id": str(uuid.uuid4()),
            "document_id": document_id,
            "document_title": doc.get("title", "Untitled Document"),
            "creator_id": str(doc.get("creator_id")),
            "user_id": user_id,
            "user_name": current_user.full_name or "Người dùng",
            "user_email": getattr(current_user, "email", ""),
            "requested_role": requested_role,
            "message": message or "",
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc),
            "reviewed_at": None,
        }

        await CooperationRepository.insert_access_request(req_doc)

        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            "Request access",
            f"User requested {requested_role} access to document",
        )

        return {
            "message": "Gửi yêu cầu xin cấp quyền truy cập hoàn tất",
            "request_id": req_doc["_id"],
        }

    @staticmethod
    async def get_document_access_requests(document_id: str, current_user) -> list:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc bạn không phải là chủ sở hữu",
            )

        requests = (
            await mongo
            .find(
                "collaboration_access_requests",
                {"document_id": document_id, "status": "PENDING"},
            )
            .sort("created_at", -1)
            .to_list(length=100)
        )
        return [
            {
                "id": r["_id"],
                "document_id": r["document_id"],
                "document_title": r.get("document_title"),
                "user_id": r["user_id"],
                "user_name": r.get("user_name"),
                "user_email": r.get("user_email"),
                "requested_role": r.get("requested_role"),
                "message": r.get("message"),
                "status": r.get("status"),
                "created_at": (
                    r["created_at"].isoformat()
                    if isinstance(r.get("created_at"), datetime)
                    else r.get("created_at")
                ),
            }
            for r in requests
        ]

    @staticmethod
    async def get_my_incoming_access_requests(current_user) -> list:
        requests = (
            await mongo
            .find("collaboration_access_requests", {"creator_id": str(current_user.id), "status": "PENDING"})
            .sort("created_at", -1)
            .to_list(length=100)
        )
        return [
            {
                "id": r["_id"],
                "document_id": r["document_id"],
                "document_title": r.get("document_title"),
                "user_id": r["user_id"],
                "user_name": r.get("user_name"),
                "user_email": r.get("user_email"),
                "requested_role": r.get("requested_role"),
                "message": r.get("message"),
                "status": r.get("status"),
                "created_at": (
                    r["created_at"].isoformat()
                    if isinstance(r.get("created_at"), datetime)
                    else r.get("created_at")
                ),
            }
            for r in requests
        ]

    @staticmethod
    async def review_access_request(
        request_id: str, status: str, role: str | None, current_user
    ) -> dict:
        req = await CooperationRepository.find_access_request({"_id": request_id})
        if not req:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy yêu cầu cấp quyền")

        if str(req.get("creator_id")) != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="Chỉ chủ sở hữu tài liệu mới có quyền xét duyệt yêu cầu",
            )

        if req.get("status") != "PENDING":
            raise HTTPException(
                status_code=400, detail="Yêu cầu này đã được xét duyệt trước đó"
            )

        status = status.upper()
        if status not in ["ACCEPTED", "REJECTED"]:
            raise HTTPException(status_code=400, detail="Trạng thái duyệt không hợp lệ")

        granted_role = role or req.get("requested_role", "editor")
        if granted_role not in ["editor", "commenter", "viewer"]:
            raise HTTPException(status_code=400, detail="Quyền hạn cấp không hợp lệ")

        now = datetime.now(timezone.utc)
        await CooperationRepository.update_access_request(
            {"_id": request_id},
            {
                "$set": {
                    "status": status,
                    "granted_role": granted_role if status == "ACCEPTED" else None,
                    "reviewed_at": now,
                    "reviewed_by": str(current_user.id),
                }
            },
        )

        if status == "ACCEPTED":
            user_id = str(req["user_id"])
            document_id = req["document_id"]
            await DocumentRepository.update_one(
                {"_id": document_id},
                {
                    "$addToSet": {"coauthors": user_id},
                    "$set": {"updated_at": now},
                },
            )
            await CooperationRepository.update_invite(
                {"document_id": document_id, "invitee_id": user_id},
                {
                    "$set": {
                        "document_id": document_id,
                        "document_title": req.get("document_title", ""),
                        "inviter_id": req["creator_id"],
                        "inviter_name": current_user.full_name,
                        "invitee_id": user_id,
                        "role": granted_role,
                        "status": "ACCEPTED",
                        "responded_at": now,
                    },
                    "$setOnInsert": {
                        "_id": str(uuid.uuid4()),
                        "created_at": now,
                    },
                },
                upsert=True,
            )

        await ActivityService.log_activity(
            req["document_id"],
            current_user.full_name,
            f"Review access request ({status})",
            f"Access request for user {req.get('user_name')} was {status} (Role: {granted_role})",
        )

        return {
            "status": status,
            "role": granted_role if status == "ACCEPTED" else None,
            "message": (
                "Phê duyệt yêu cầu tham gia cộng tác hoàn tất"
                if status == "ACCEPTED"
                else "Từ chối yêu cầu tham gia cộng tác hoàn tất"
            ),
        }
