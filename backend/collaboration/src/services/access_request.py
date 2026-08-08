import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
from src.repositories.cooperation import CooperationRepository, DocumentRepository
from src.services.activity import ActivityService

class AccessRequestService:
    @staticmethod
    @log_logic_execution
    async def create_access_request(
        document_id: str, requested_role: str, message: str | None, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu yêu cầu")

        if str(doc.get("creator_id")) == str(current_user.id):
            raise HTTPException(
                status_code=400, detail="Bạn là chủ sở hữu của tài liệu này"
            )

        if str(current_user.id) in (doc.get("coauthors") or []):
            raise HTTPException(
                status_code=400, detail="Bạn đã là cộng tác viên của tài liệu này"
            )

        if requested_role not in ["editor", "commenter", "viewer"]:
            raise HTTPException(status_code=400, detail="Quyền yêu cầu không hợp lệ")

        existing = await CooperationRepository.find_access_request(
            {"document_id": document_id, "user_id": str(current_user.id), "status": "PENDING"}
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
            "user_id": str(current_user.id),
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
            "id": req_doc["_id"],
            "document_id": document_id,
            "status": "PENDING",
            "message": "Gửi yêu cầu xin cấp quyền truy cập hoàn tất",
        }

    @staticmethod
    @log_logic_execution
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
            .find("collaboration_access_requests", {"document_id": document_id})
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
    @log_logic_execution
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
    @log_logic_execution
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
        if status not in ["APPROVED", "REJECTED"]:
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
                    "granted_role": granted_role if status == "APPROVED" else None,
                    "reviewed_at": now,
                    "reviewed_by": str(current_user.id),
                }
            },
        )

        if status == "APPROVED":
            await DocumentRepository.update_one(
                {"_id": req["document_id"]},
                {
                    "$addToSet": {"coauthors": str(req["user_id"])},
                    "$set": {
                        f"coauthor_roles.{str(req['user_id'])}": granted_role,
                        "updated_at": now,
                    },
                },
            )

        await ActivityService.log_activity(
            req["document_id"],
            current_user.full_name,
            f"Review access request ({status})",
            f"Access request for user {req.get('user_name')} was {status} (Role: {granted_role})",
        )

        return {
            "id": request_id,
            "status": status,
            "granted_role": granted_role if status == "APPROVED" else None,
            "message": f"Xét duyệt yêu cầu thành công: {status}",
        }
