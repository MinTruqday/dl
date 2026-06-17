import uuid
from datetime import datetime, timezone

from core.config import settings
from core.database import db_client
from core.repositories.base_repository import RepositoryFactory
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
        await RepositoryFactory.get("collaboration_activities").insert_one(
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
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        import httpx

        invitee = None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.PROVISION_URL}/users/by-email/{invitee_email}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    invitee = resp.json().get("data")
        except Exception:
            pass
        if not invitee:
            raise HTTPException(
                status_code=404, detail="The target user account specified for the collaboration invitation could not be located"
            )
        invitee_id = str(invitee["_id"])
        if invitee_id == str(current_user.id):
            raise HTTPException(
                status_code=400, detail="The system architecture restricts accounts from dispatching collaboration invitations to themselves"
            )
        existing_invite = await RepositoryFactory.get("collaboration_invites").find_one(
            {"document_id": document_id, "invitee_id": invitee_id, "status": "PENDING"}
        )
        if existing_invite:
            raise HTTPException(
                status_code=400, detail="An active collaboration invitation has already been dispatched to this account and is currently pending review"
            )
        coauthors = doc.get("coauthors", [])
        if invitee_id in coauthors:
            raise HTTPException(status_code=400, detail="The specified account is already registered as an active participant in this collaborative workspace")
        invite = {
            "_id": str(uuid7()),
            "document_id": document_id,
            "document_title": doc.get("title", "Untitled Document"),
            "inviter_id": str(current_user.id),
            "inviter_name": current_user.full_name,
            "invitee_id": invitee_id,
            "role": role,
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("collaboration_invites").insert_one(invite)
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Send invitation",
            "A new editorial collaboration invitation has been processed and dispatched via the internal notification system",
        )
        logger.info(
            "A new editorial collaboration invitation has been successfully dispatched to the designated participant"
        )
        return {"message": "The editorial collaboration invitation has been successfully processed and dispatched", "invite_id": invite["_id"]}

    @staticmethod
    async def get_my_collaboration_invites(current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        invites = (
            await RepositoryFactory.get("collaboration_invites")
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
        invite = await RepositoryFactory.get("collaboration_invites").find_one(
            {"_id": invite_id, "invitee_id": str(current_user.id), "status": "PENDING"}
        )
        if not invite:
            raise HTTPException(
                status_code=404, detail="The specified collaboration invitation is either invalid or has already been fully processed by the system"
            )
        if status not in ["ACCEPTED", "REJECTED"]:
            raise HTTPException(
                status_code=400, detail="The provided invitation response status is not recognized by the validation system"
            )
        await RepositoryFactory.get("collaboration_invites").update_one(
            {"_id": invite_id},
            {"$set": {"status": status, "responded_at": datetime.now(timezone.utc)}},
        )
        if status == "ACCEPTED":
            await RepositoryFactory.get("documents").update_one(
                {"_id": invite["document_id"]},
                {
                    "$push": {"coauthors": str(current_user.id)},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
            )
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Accepted" if status == "ACCEPTED" else "Declined",
            "The recipient has officially registered their response to the pending editorial collaboration invitation",
        )
        logger.info(
            "The pending collaboration invitation has been successfully processed according to the user response"
        )
        return {
            "message": "Your response to the collaboration invitation has been successfully recorded and applied"
        }

    @staticmethod
    async def get_collaborators(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        invites = (
            await RepositoryFactory.get("collaboration_invites")
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
                        f"{settings.PROVISION_URL}/users/{inv['invitee_id']}",
                        timeout=settings.DEFAULT_HTTP_TIMEOUT,
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
                        "full_name": user_info.get("full_name", "User"),
                        "role": inv.get("role", "editor"),
                    }
                )
        return collaborators

    @staticmethod
    async def remove_collaborator(collaboration_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        invite = await RepositoryFactory.get("collaboration_invites").find_one(
            {"_id": collaboration_id}
        )
        if not invite:
            raise HTTPException(
                status_code=404, detail="The detailed configuration for the specified collaboration environment could not be retrieved"
            )
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": invite["document_id"], "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=403,
                detail="The current account lacks the administrative privileges required to manage participants for this document",
            )
        await RepositoryFactory.get("documents").update_one(
            {"_id": invite["document_id"]},
            {"$pull": {"coauthors": invite["invitee_id"]}},
        )
        await RepositoryFactory.get("collaboration_invites").delete_one(
            {"_id": collaboration_id}
        )
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Collaborator removed",
            "The specified collaborator has been effectively removed from the authorized modification list",
        )
        logger.info(
            "The specified collaborator has been successfully removed from the active editorial environment"
        )
        return {"message": "The specified participant has been successfully removed from the active collaborative workspace"}

    @staticmethod
    async def get_activities(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        activities = (
            await RepositoryFactory.get("collaboration_activities")
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
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        import httpx

        target_user = None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.PROVISION_URL}/users/{target_user_id}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    target_user = resp.json().get("data")
        except Exception:
            pass
        if not target_user:
            raise HTTPException(
                status_code=404,
                detail="The target user account designated for the ownership transfer could not be located",
            )
        if target_user_id not in doc.get("coauthors", []):
            raise HTTPException(
                status_code=400,
                detail="The administrative ownership transfer is restricted exclusively to existing active collaborators",
            )
        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id},
            {
                "$set": {
                    "creator_id": target_user_id,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$pull": {"coauthors": target_user_id},
            },
        )
        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id}, {"$push": {"coauthors": str(current_user.id)}}
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Transfer ownership",
            "The primary administrative ownership rights of the document have been securely reassigned",
        )
        logger.info(
            "The primary administrative ownership of the collaborative document has been successfully transferred"
        )
        return {"message": "The administrative ownership rights of the specified document have been successfully transferred"}

    @staticmethod
    async def update_status(document_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await RepositoryFactory.get("collaboration_status").update_one(
            {"document_id": document_id, "user_id": str(current_user.id)},
            {
                "$set": {
                    "last_seen": datetime.now(timezone.utc),
                    "full_name": current_user.full_name,
                }
            },
            upsert=True,
        )
        return {"message": "Your active presence status within the collaborative environment has been successfully synchronized"}

    @staticmethod
    async def get_online_collaborators(document_id: str, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        online_users = (
            await RepositoryFactory.get("collaboration_status")
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
                    "full_name": u.get("full_name", "Collaborator"),
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
        invite = await RepositoryFactory.get("collaboration_invites").find_one(
            {"_id": collaboration_id}
        )
        if not invite:
            raise HTTPException(
                status_code=404, detail="The detailed configuration for the specified collaboration environment could not be retrieved"
            )
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": invite["document_id"], "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=403,
                detail="The current account lacks the administrative privileges required to manage participants for this document",
            )
        if role not in ["editor", "viewer"]:
            raise HTTPException(status_code=400, detail="The requested access role is not recognized by the collaboration permission architecture")
        await RepositoryFactory.get("collaboration_invites").update_one(
            {"_id": collaboration_id}, {"$set": {"role": role}}
        )
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Update role",
            "The specific access privileges and system roles for the collaborator have been modified",
        )
        return {"message": "The specific access privileges for the designated collaborator have been successfully updated"}

    @staticmethod
    async def send_memo(document_id: str, message: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        memo = {
            "_id": str(uuid7()),
            "document_id": document_id,
            "sender_name": current_user.full_name,
            "sender_id": str(current_user.id),
            "message": message,
            "timestamp": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("collaboration_memos").insert_one(memo)
        return {"message": "The internal collaborative communication message has been successfully transmitted", "memo": memo}

    @staticmethod
    async def get_memos(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        memos = (
            await RepositoryFactory.get("collaboration_memos")
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
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        if access_level not in ["invite_only", "anyone_with_link"]:
            raise HTTPException(
                status_code=400, detail="The provided document access level configuration is structurally invalid or unsupported"
            )
        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id}, {"$set": {"collab_access_level": access_level}}
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Permission settings",
            "The core collaborative access permissions for the environment have been successfully adjusted",
        )
        return {
            "message": "The global collaborative access permission configurations have been successfully updated",
            "collab_access_level": access_level,
        }

    @staticmethod
    async def get_sent_pending_invites(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        invites = (
            await RepositoryFactory.get("collaboration_invites")
            .find({"document_id": document_id, "status": "PENDING"})
            .sort("created_at", -1)
            .to_list(length=100)
        )
        return invites

    @staticmethod
    async def revoke_invite(invite_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        invite = await RepositoryFactory.get("collaboration_invites").find_one(
            {"_id": invite_id, "status": "PENDING"}
        )
        if not invite:
            raise HTTPException(
                status_code=404, detail="The specified collaboration invitation could not be located or has already been processed by the recipient"
            )
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": invite["document_id"], "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="The current account lacks the necessary authorization privileges to revoke this specific invitation"
            )
        await RepositoryFactory.get("collaboration_invites").delete_one(
            {"_id": invite_id}
        )
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Invitation revoked",
            "The active collaboration invitation token has been securely invalidated by the document owner",
        )
        return {"message": "The previously dispatched collaborative invitation has been successfully revoked and invalidated"}

    @staticmethod
    async def get_contribution_stats(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        pipeline = [
            {"$match": {"document_id": document_id}},
            {"$group": {"_id": "$user_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        stats = (
            await RepositoryFactory.get("collaboration_activities")
            .aggregate(pipeline)
            .to_list(length=100)
        )
        return [{"user_name": s["_id"], "count": s["count"]} for s in stats]

    @staticmethod
    async def create_snapshot(
        document_id: str, version_name: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        snapshot = {
            "_id": str(uuid7()),
            "document_id": document_id,
            "version_name": version_name,
            "content": doc.get("content", ""),
            "created_by": current_user.full_name,
            "timestamp": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("collaboration_drafts").insert_one(snapshot)
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Create draft",
            "A structural milestone snapshot has been permanently recorded in the version control history",
        )
        return {"message": "A new historical snapshot of the collaborative document has been successfully preserved", "snapshot": snapshot}

    @staticmethod
    async def get_snapshots(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        drafts = (
            await RepositoryFactory.get("collaboration_drafts")
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
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        existing = await RepositoryFactory.get("collaboration_locks").find_one(
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
                    detail="The specified document is currently locked for exclusive editorial modification by another active session",
                )
        await RepositoryFactory.get("collaboration_locks").update_one(
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
            "Document locked",
            "An exclusive access token has been acquired to prevent overlapping editorial modifications",
        )
        return {"message": "The exclusive editorial modification lock has been successfully acquired for the current session"}

    @staticmethod
    async def release_lock(document_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        existing = await RepositoryFactory.get("collaboration_locks").find_one(
            {"document_id": document_id}
        )
        if existing and existing.get("user_id") == str(current_user.id):
            await RepositoryFactory.get("collaboration_locks").delete_one(
                {"document_id": document_id}
            )
            await CollaborationService.log_activity(
                document_id,
                current_user.full_name,
                "Unlock document",
                "The previously acquired exclusive editorial lock has been safely released back into the available pool",
            )
        return {"message": "The exclusive editorial modification lock has been successfully released and the session has ended"}

    @staticmethod
    async def get_lock_status(document_id: str, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        existing = await RepositoryFactory.get("collaboration_locks").find_one(
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
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        invite_code = str(uuid7())[:8].upper()
        await RepositoryFactory.get("collaboration_invite_codes").update_one(
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
            "Generate collaboration code",
            "A secure time-limited invitation token has been successfully generated for immediate collaborative access",
        )
        return {"invite_code": invite_code}

    @staticmethod
    async def join_via_invite_code(invite_code: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        code_entry = await RepositoryFactory.get("collaboration_invite_codes").find_one(
            {"invite_code": invite_code.upper()}
        )
        if not code_entry:
            raise HTTPException(
                status_code=404, detail="The specified collaboration code could not be verified or has exceeded its expiration window"
            )
        document_id = code_entry["document_id"]
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="The requested digital document could not be located within the primary storage repository")
        if doc.get("creator_id") == str(current_user.id):
            raise HTTPException(status_code=400, detail="The authentication process has determined that you are already the primary administrative owner of this document")
        if str(current_user.id) in doc.get("coauthors", []):
            raise HTTPException(
                status_code=400, detail="The authentication process has determined that you are already an active participant in this collaborative workspace"
            )
        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id},
            {
                "$push": {"coauthors": str(current_user.id)},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        await RepositoryFactory.get("collaboration_invites").insert_one(
            {
                "_id": str(uuid7()),
                "document_id": document_id,
                "document_title": doc.get("title", "Untitled Document"),
                "inviter_id": doc["creator_id"],
                "inviter_name": "Owner",
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
            "Join via code",
            "The authenticated user has successfully claimed the invitation token and entered the editorial workspace",
        )
        return {
            "message": "You have successfully joined the collaborative editorial group using the provided access token",
            "document_id": document_id,
        }

    @staticmethod
    async def create_task(
        document_id: str, task_desc: str, assigned_to: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        task = {
            "_id": str(uuid7()),
            "document_id": document_id,
            "task_desc": task_desc,
            "is_done": False,
            "assigned_to": assigned_to or "Unassigned",
            "created_by": current_user.full_name,
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("collaboration_tasks").insert_one(task)
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Create task",
            "A structured operational assignment has been successfully integrated into the active workflow queue",
        )
        return {"task": task}

    @staticmethod
    async def get_tasks(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="The specified document could not be located or the current account lacks the required access permissions",
            )
        tasks = (
            await RepositoryFactory.get("collaboration_tasks")
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
        task = await RepositoryFactory.get("collaboration_tasks").find_one(
            {"_id": task_id}
        )
        if not task:
            raise HTTPException(status_code=404, detail="The requested collaborative editorial task could not be located within the active tracking system")
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": task["document_id"],
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="The current account lacks the required administrative privileges to modify the specified editorial task"
            )
        await RepositoryFactory.get("collaboration_tasks").update_one(
            {"_id": task_id}, {"$set": {"is_done": is_done}}
        )
        await CollaborationService.log_activity(
            task["document_id"],
            current_user.full_name,
            "Update task",
            "The execution status of the designated collaborative task has been formally modified",
        )
        return {"message": "The operational status of the specified editorial collaborative task has been successfully updated"}

    @staticmethod
    async def add_task_comment(
        task_id: str, comment_text: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        task = await RepositoryFactory.get("collaboration_tasks").find_one(
            {"_id": task_id}
        )
        if not task:
            raise HTTPException(status_code=404, detail="The requested collaborative editorial task could not be located within the active tracking system")
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": task["document_id"],
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="The current account lacks the necessary authorization privileges to participate in this task discussion thread"
            )
        comment = {
            "_id": str(uuid7()),
            "task_id": task_id,
            "sender_name": current_user.full_name,
            "comment_text": comment_text,
            "timestamp": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("collaboration_task_comments").insert_one(comment)
        return {"comment": comment}

    @staticmethod
    async def get_task_comments(task_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        task = await RepositoryFactory.get("collaboration_tasks").find_one(
            {"_id": task_id}
        )
        if not task:
            raise HTTPException(status_code=404, detail="The requested collaborative editorial task could not be located within the active tracking system")
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "_id": task["document_id"],
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="The current account lacks the necessary authorization privileges to participate in this task discussion thread"
            )
        comments = (
            await RepositoryFactory.get("collaboration_task_comments")
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