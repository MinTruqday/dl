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
            {"_id": document_id, "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document could not be found or access denied",
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
                status_code=404, detail="The specified user could not be found"
            )
        invitee_id = str(invitee["_id"])
        if invitee_id == str(current_user.id):
            raise HTTPException(
                status_code=400, detail="Action restricted. You cannot invite yourself as a collaborator"
            )
        existing_invite = await RepositoryFactory.get("collaboration_invites").find_one(
            {"document_id": document_id, "invitee_id": invitee_id, "status": "PENDING"}
        )
        if existing_invite:
            raise HTTPException(
                status_code=400, detail="A pending invitation is awaiting confirmation from this user"
            )
        coauthors = doc.get("coauthors", [])
        if invitee_id in coauthors:
            raise HTTPException(status_code=400, detail="This user is already a collaborator")
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
            f"Collaboration invitation sent to {invitee_email} with role {role}",
        )
        logger.info(
            f"User {current_user.id} invited {invitee_id} to edit document {document_id}"
        )
        return {"message": "Collaboration invitation sent successfully", "invite_id": invite["_id"]}

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
                status_code=404, detail="The invitation could not be found or has already been processed"
            )
        if status not in ["ACCEPTED", "REJECTED"]:
            raise HTTPException(
                status_code=400, detail="Invalid response status"
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
            (
                "Collaboration invitation accepted successfully"
                if status == "ACCEPTED"
                else "Collaboration invitation declined successfully"
            ),
        )
        logger.info(
            f"User {current_user.id} {status} collaboration invitation {invite_id}"
        )
        return {
            "message": f"Collaboration invitation {('accepted' if status == 'ACCEPTED' else 'declined')} successfully"
        }

    @staticmethod
    async def get_collaborators(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
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
                detail="Document could not be found or access denied",
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
                status_code=404, detail="Collaboration details could not be found"
            )
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": invite["document_id"], "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=403,
                detail="Action restricted. Permission denied to manage collaborators for this document",
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
            f"Collaborator {invite['invitee_id']} removed successfully",
        )
        logger.info(
            f"Owner {current_user.id} removed collaborator {invite['invitee_id']} from document {invite['document_id']}"
        )
        return {"message": "User removed from collaboration list successfully"}

    @staticmethod
    async def get_activities(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
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
                detail="Document could not be found or access denied",
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
            {"_id": document_id, "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document could not be found or ownership transfer access denied",
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
                detail="Transferee information could not be found",
            )
        if target_user_id not in doc.get("coauthors", []):
            raise HTTPException(
                status_code=400,
                detail="Only collaborators are eligible to receive document ownership transfer",
            )
        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id},
            {
                "$set": {
                    "author_id": target_user_id,
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
            f"Ownership transferred successfully document cho {target_user.get('full_name')}",
        )
        logger.info(
            f"Transferred ownership of document {document_id} from {current_user.id} to {target_user_id}"
        )
        return {"message": "Document ownership transferred successfully"}

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
        return {"message": "Online status updated successfully"}

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
                status_code=404, detail="Collaboration details could not be found"
            )
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": invite["document_id"], "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=403,
                detail="Action restricted. Permission denied to manage collaborators for this document",
            )
        if role not in ["editor", "viewer"]:
            raise HTTPException(status_code=400, detail="Invalid collaboration role specified")
        await RepositoryFactory.get("collaboration_invites").update_one(
            {"_id": collaboration_id}, {"$set": {"role": role}}
        )
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Update role",
            f"Changed role of collaborator {invite['invitee_id']} to {role}",
        )
        return {"message": "Collaborator role updated successfully"}

    @staticmethod
    async def send_memo(document_id: str, message: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
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
                detail="Document could not be found or access denied",
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
        return {"message": "Message exchanged successfully", "memo": memo}

    @staticmethod
    async def get_memos(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
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
                detail="Document could not be found or access denied",
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
            {"_id": document_id, "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document could not be found or access denied to update settings",
            )
        if access_level not in ["invite_only", "anyone_with_link"]:
            raise HTTPException(
                status_code=400, detail="Invalid access level specified"
            )
        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id}, {"$set": {"collab_access_level": access_level}}
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Permission settings",
            f"Document access level updated to: {access_level}",
        )
        return {
            "message": "Default access permissions updated successfully",
            "collab_access_level": access_level,
        }

    @staticmethod
    async def get_sent_pending_invites(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": document_id, "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document could not be found or access denied",
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
                status_code=404, detail="The invitation could not be found or has already been accepted"
            )
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": invite["document_id"], "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="Action restricted. Permission denied to revoke this invitation"
            )
        await RepositoryFactory.get("collaboration_invites").delete_one(
            {"_id": invite_id}
        )
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Invitation revoked",
            "Pending collaboration invitation revoked successfully",
        )
        return {"message": "Collaboration invitation revoked successfully"}

    @staticmethod
    async def get_contribution_stats(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
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
                detail="Document could not be found or access to statistics denied",
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
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document could not be found or access denied",
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
            f"Collaboration draft version stored: {version_name}",
        )
        return {"message": "Collaboration draft created successfully", "snapshot": snapshot}

    @staticmethod
    async def get_snapshots(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
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
                detail="Document could not be found or access denied",
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
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document could not be found or access denied",
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
                    detail=f"Document is currently exclusively locked by {existing.get('user_name')}",
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
            "Exclusive edit lock enabled successfully",
        )
        return {"message": "Document locked for editing successfully"}

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
                "Exclusive edit lock disabled successfully",
            )
        return {"message": "Editing session ended and document unlocked successfully"}

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
            {"_id": document_id, "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document could not be found or ownership access denied",
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
            f"Activated quick invite code: {invite_code}",
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
                status_code=404, detail="Collaboration code could not be found or has expired"
            )
        document_id = code_entry["document_id"]
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document could not be found")
        if doc.get("author_id") == str(current_user.id):
            raise HTTPException(status_code=400, detail="User is already the owner of this document")
        if str(current_user.id) in doc.get("coauthors", []):
            raise HTTPException(
                status_code=400, detail="User is already a collaborator on this document"
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
                "inviter_id": doc["author_id"],
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
            "Joined editorial collaboration group via quick invite code successfully",
        )
        return {
            "message": "Joined editorial collaboration group successfully",
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
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document could not be found or access denied",
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
            f"New collaboration task added: {task_desc} (Assigned to: {assigned_to or 'Unassigned'})",
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
                    {"author_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document could not be found or access denied",
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
            raise HTTPException(status_code=404, detail="The specified task could not be found")
        doc = await RepositoryFactory.get("documents").find_one(
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
                status_code=403, detail="Action restricted. Permission denied to edit this task"
            )
        await RepositoryFactory.get("collaboration_tasks").update_one(
            {"_id": task_id}, {"$set": {"is_done": is_done}}
        )
        await CollaborationService.log_activity(
            task["document_id"],
            current_user.full_name,
            "Update task",
            "Marked task '{task['task_desc']}' as {('Completed' if is_done else 'Pending')}",
        )
        return {"message": "Task updated successfully"}

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
            raise HTTPException(status_code=404, detail="The specified task could not be found")
        doc = await RepositoryFactory.get("documents").find_one(
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
                status_code=403, detail="Action restricted. Access to task discussion denied"
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
            raise HTTPException(status_code=404, detail="The specified task could not be found")
        doc = await RepositoryFactory.get("documents").find_one(
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
                status_code=403, detail="Action restricted. Access to task discussion denied"
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
