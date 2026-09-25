from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.clients.authentication import get_project_creation_policy
from src.core.auth import PROJECT_PERMISSIONS, permissions_for_role
from src.core.common import (
    audit,
    get_project,
    load_user_identities,
    new_id,
    now,
    optimistic_patch,
    resolve_user_reference,
)
from src.repositories import project_repository
from src.services.domain_policy import domain_policy


PROJECT_POLICY = domain_policy("project_service")


def project_access(project, membership, grant):
    policy = PROJECT_POLICY
    role_permissions = (
        permissions_for_role(membership["project_role"], project.get("settings"))
        if membership
        else set()
    )
    grant_permissions = set(grant.get("permissions", [])) & PROJECT_PERMISSIONS if grant else set()
    return {
        **project,
        "current_membership": membership,
        "current_permissions": sorted(role_permissions | grant_permissions),
        "access_context": (
            {
                "mode": policy["break_glass_mode"],
                "grant_id": grant["_id"],
                "permissions": sorted(grant_permissions),
                "expires_at": grant["expires_at"],
                "reason": grant.get("reason"),
            }
            if grant and not grant_permissions.issubset(role_permissions)
            else None
        ),
    }


def project_settings(project):
    return {
        "project_id": project["_id"],
        "name": project.get("name"),
        "description": project.get("description", ""),
        "project_type": project.get("project_type"),
        "locale": project.get("locale"),
        "timezone": project.get("timezone"),
        "settings": project.get("settings", {}),
    }


class ProjectService:
    @staticmethod
    async def create(payload, user):
        service_policy = PROJECT_POLICY
        membership_statuses = service_policy["membership_statuses"]
        policy = await get_project_creation_policy()
        if policy == service_policy["creation_admin_only_policy"] and not user.is_system_admin:
            raise HTTPException(
                status_code=403,
                detail={"code": service_policy["error_codes"]["system_permission_denied"]},
            )
        timestamp = now()
        project = {
            "_id": new_id(service_policy["project_id_prefix"]),
            **payload.model_dump(),
            "created_by": user.id,
            "status": service_policy["project_statuses"]["active"],
            "revision": service_policy["initial_revision"],
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        membership = {
            "_id": new_id(service_policy["membership_id_prefix"]),
            "project_id": project["_id"],
            "user_id": user.id,
            "project_role": service_policy["creator_role"],
            "status": membership_statuses["active"],
            "membership_revision": service_policy["initial_revision"],
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await project_repository.create_with_creator(project, membership)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=409, detail={"code": service_policy["error_codes"]["key_exists"]}
            )
        await audit(
            user.id,
            service_policy["events"]["created"],
            service_policy["entity_types"]["project"],
            project["_id"],
            project["_id"],
            {"creator_membership_id": membership["_id"]},
        )
        return {
            **project,
            "current_membership": membership,
            "current_permissions": sorted(
                permissions_for_role(service_policy["creator_role"], project["settings"])
            ),
        }

    @staticmethod
    async def list(query_text, status, limit, user):
        policy = PROJECT_POLICY
        active_status = policy["membership_statuses"]["active"]
        memberships = await project_repository.list_active_memberships(
            user.id, active_status
        )
        by_project = {item["project_id"]: item for item in memberships}
        grants = await project_repository.list_active_grants(
            user.id, active_status, now()
        )
        by_grant = {item["project_id"]: item for item in grants}
        query = {"_id": {"$in": list(set(by_project) | set(by_grant))}}
        if status and status != policy["all_status_filter"]:
            query["status"] = status
        if query_text:
            query["$or"] = [
                {"name": {"$regex": query_text, "$options": "i"}},
                {"key": {"$regex": query_text, "$options": "i"}},
            ]
        projects = await project_repository.list_projects(query, limit)
        return [
            project_access(project, by_project.get(project["_id"]), by_grant.get(project["_id"]))
            for project in projects
        ]

    @staticmethod
    async def list_invitations(user):
        invitations = await project_repository.list_invitations(
            user.id, PROJECT_POLICY["membership_statuses"]["invited"]
        )
        project_ids = {item["project_id"] for item in invitations}
        projects = await project_repository.list_project_summaries(project_ids)
        projects_by_id = {item["_id"]: item for item in projects}
        return [
            {**invitation, "project": projects_by_id.get(invitation["project_id"])}
            for invitation in invitations
            if invitation["project_id"] in projects_by_id
        ]

    @staticmethod
    async def get(project_id, user):
        policy = PROJECT_POLICY
        project = await get_project(project_id, user, policy["permissions"]["read"])
        membership = await project_repository.find_member(
            project_id, user.id, status=policy["membership_statuses"]["active"]
        )
        grant = await project_repository.find_active_grant(
            project_id, user.id, policy["membership_statuses"]["active"], now()
        )
        return project_access(project, membership, grant)

    @staticmethod
    async def update(project_id, payload, user):
        policy = PROJECT_POLICY
        await get_project(project_id, user, policy["permissions"]["update"])
        if payload.settings is not None:
            await get_project(project_id, user, policy["permissions"]["settings_manage"])
        updated = await optimistic_patch(
            "projects", project_id, project_id, payload.expected_revision, payload.model_dump()
        )
        await audit(
            user.id,
            policy["events"]["updated"],
            policy["entity_types"]["project"],
            project_id,
            project_id,
        )
        return updated

    @staticmethod
    async def get_settings(project_id, user):
        policy = PROJECT_POLICY
        project = await get_project(
            project_id, user, policy["permissions"]["settings_manage"]
        )
        return project_settings(project), project.get("revision", policy["initial_revision"])

    @staticmethod
    async def update_settings(project_id, payload, user):
        policy = PROJECT_POLICY
        await get_project(project_id, user, policy["permissions"]["settings_manage"])
        changes = payload.model_dump(exclude_none=True)
        changes.pop("expected_revision", None)
        if not changes:
            raise HTTPException(
                status_code=422, detail={"code": policy["error_codes"]["settings_empty"]}
            )
        updated = await optimistic_patch(
            "projects", project_id, project_id, payload.expected_revision, changes
        )
        await audit(
            user.id,
            policy["events"]["settings_updated"],
            policy["entity_types"]["settings"],
            project_id,
            project_id,
        )
        return project_settings(updated), updated["revision"]

    @staticmethod
    async def archive(project_id, payload, user):
        policy = PROJECT_POLICY
        await get_project(project_id, user, policy["permissions"]["archive"])
        updated = await optimistic_patch(
            "projects",
            project_id,
            project_id,
            payload.expected_revision,
            {
                "status": policy["project_statuses"]["archived"],
                "archived_by": user.id,
                "archived_at": now(),
                "archive_reason": payload.reason,
            },
        )
        await audit(
            user.id,
            policy["events"]["archived"],
            policy["entity_types"]["project"],
            project_id,
            project_id,
            {"reason": payload.reason},
        )
        return updated

    @staticmethod
    async def restore(project_id, payload, user):
        policy = PROJECT_POLICY
        project = await get_project(project_id, user, policy["permissions"]["restore"])
        if project.get("status") == policy["project_statuses"]["active"]:
            return project
        updated = await optimistic_patch(
            "projects",
            project_id,
            project_id,
            payload.expected_revision,
            {
                "status": policy["project_statuses"]["active"],
                "restored_by": user.id,
                "restored_at": now(),
                "restore_reason": payload.reason,
            },
        )
        await audit(
            user.id,
            policy["events"]["restored"],
            policy["entity_types"]["project"],
            project_id,
            project_id,
            {"reason": payload.reason},
        )
        return updated

    @staticmethod
    async def list_members(project_id, user):
        await get_project(
            project_id, user, PROJECT_POLICY["permissions"]["members_read"]
        )
        members = await project_repository.list_members(project_id)
        identities = await load_user_identities(item.get("user_id") for item in members)
        return [
            {
                **member,
                "user": identities.get(member.get("user_id")),
                "user_label": (identities.get(member.get("user_id")) or {}).get("label") or member.get("user_id"),
            }
            for member in members
        ]

    @staticmethod
    async def add_member(project_id, payload, user, invited=False):
        policy = PROJECT_POLICY
        statuses = policy["membership_statuses"]
        await get_project(project_id, user, policy["permissions"]["members_manage"])
        member_user_id = await resolve_user_reference(payload.user_id)
        timestamp = now()
        membership = {
            "_id": new_id(policy["membership_id_prefix"]),
            "project_id": project_id,
            "user_id": member_user_id,
            "project_role": payload.project_role,
            "status": statuses["invited"] if invited else statuses["active"],
            "membership_revision": policy["initial_revision"],
            **({"invited_by": user.id, "invited_at": timestamp} if invited else {}),
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await project_repository.add_member(membership)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["error_codes"]["membership_exists"]},
            )
        await audit(
            user.id,
            policy["events"]["member_invited"]
            if invited
            else policy["events"]["member_added"],
            policy["entity_types"]["member"],
            membership["_id"],
            project_id,
            {"user_id": member_user_id, "project_role": payload.project_role},
        )
        return membership

    @staticmethod
    async def accept_invitation(invitation_id, user):
        policy = PROJECT_POLICY
        statuses = policy["membership_statuses"]
        timestamp = now()
        membership = await project_repository.transition_invitation(
            invitation_id,
            user.id,
            statuses["invited"],
            {"status": statuses["active"], "accepted_at": timestamp, "updated_at": timestamp},
        )
        if not membership:
            raise HTTPException(
                status_code=404,
                detail={"code": policy["error_codes"]["invitation_not_found"]},
            )
        await audit(
            user.id,
            policy["events"]["invitation_accepted"],
            policy["entity_types"]["member"],
            membership["_id"],
            membership["project_id"],
        )
        return membership

    @classmethod
    async def accept_project_invitation(cls, project_id, member_user_id, user):
        policy = PROJECT_POLICY
        if user.id != member_user_id:
            raise HTTPException(
                status_code=403,
                detail={"code": policy["error_codes"]["invitation_owner_required"]},
            )
        membership = await project_repository.find_member(
            project_id,
            user.id,
            status=policy["membership_statuses"]["invited"],
            projection={"_id": 1},
        )
        if not membership:
            raise HTTPException(
                status_code=404,
                detail={"code": policy["error_codes"]["invitation_not_found"]},
            )
        return await cls.accept_invitation(membership["_id"], user)

    @staticmethod
    async def decline_invitation(invitation_id, user):
        policy = PROJECT_POLICY
        statuses = policy["membership_statuses"]
        timestamp = now()
        membership = await project_repository.transition_invitation(
            invitation_id,
            user.id,
            statuses["invited"],
            {"status": statuses["declined"], "declined_at": timestamp, "updated_at": timestamp},
        )
        if not membership:
            raise HTTPException(
                status_code=404,
                detail={"code": policy["error_codes"]["invitation_not_found"]},
            )
        await audit(
            user.id,
            policy["events"]["invitation_declined"],
            policy["entity_types"]["member"],
            membership["_id"],
            membership["project_id"],
        )
        return membership

    @staticmethod
    async def leave(project_id, user):
        policy = PROJECT_POLICY
        statuses = policy["membership_statuses"]
        timestamp = now()
        membership = await project_repository.transition_membership(
            project_id,
            user.id,
            statuses["active"],
            {"status": statuses["left"], "left_at": timestamp, "updated_at": timestamp},
        )
        if not membership:
            raise HTTPException(
                status_code=404,
                detail={"code": policy["error_codes"]["membership_not_found"]},
            )
        await audit(
            user.id,
            policy["events"]["member_left"],
            policy["entity_types"]["member"],
            membership["_id"],
            project_id,
        )
        return membership

    @staticmethod
    async def resend_invitation(project_id, member_user_id, user):
        policy = PROJECT_POLICY
        await get_project(project_id, user, policy["permissions"]["members_manage"])
        timestamp = now()
        membership = await project_repository.update_invitation(
            project_id,
            member_user_id,
            policy["membership_statuses"]["invited"],
            {"invited_by": user.id, "invited_at": timestamp, "updated_at": timestamp},
            {"invite_send_count": 1},
        )
        if not membership:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["error_codes"]["invitation_not_pending"]},
            )
        await audit(
            user.id,
            policy["events"]["invitation_resent"],
            policy["entity_types"]["member"],
            membership["_id"],
            project_id,
        )
        return membership

    @staticmethod
    async def cancel_invitation(project_id, member_user_id, user):
        policy = PROJECT_POLICY
        await get_project(project_id, user, policy["permissions"]["members_manage"])
        timestamp = now()
        membership = await project_repository.update_invitation(
            project_id,
            member_user_id,
            policy["membership_statuses"]["invited"],
            {
                "status": policy["membership_statuses"]["cancelled"],
                "cancelled_by": user.id,
                "cancelled_at": timestamp,
                "updated_at": timestamp,
            },
        )
        if not membership:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["error_codes"]["invitation_not_pending"]},
            )
        await audit(
            user.id,
            policy["events"]["invitation_cancelled"],
            policy["entity_types"]["member"],
            membership["_id"],
            project_id,
        )
        return membership

    @staticmethod
    async def update_member(project_id, member_user_id, payload, user):
        policy = PROJECT_POLICY
        statuses = policy["membership_statuses"]
        qa_role = policy["creator_role"]
        await get_project(project_id, user, policy["permissions"]["members_manage"])
        previous = await project_repository.find_member(project_id, member_user_id)
        if not previous:
            raise HTTPException(
                status_code=404, detail={"code": policy["error_codes"]["entity_not_found"]}
            )
        if previous.get("membership_revision") != payload.expected_revision:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": policy["error_codes"]["revision_conflict"],
                    "current_revision": previous.get("membership_revision"),
                },
            )
        changes = {key: value for key, value in payload.model_dump().items() if value is not None and key != "expected_revision"}
        desired_role = changes.get("project_role", previous.get("project_role"))
        desired_status = changes.get("status", previous.get("status"))
        was_active_qa = (
            previous.get("project_role") == qa_role
            and previous.get("status") == statuses["active"]
        )
        remains_active_qa = desired_role == qa_role and desired_status == statuses["active"]
        if was_active_qa and not remains_active_qa:
            qa_count = await project_repository.count_members_by_role_status(
                project_id, qa_role, statuses["active"]
            )
            if qa_count <= policy["minimum_creator_count"]:
                raise HTTPException(
                    status_code=422,
                    detail={"code": policy["error_codes"]["last_qa_required"]},
                )
        changes["updated_at"] = now()
        membership = await project_repository.update_member(
            project_id, member_user_id, payload.expected_revision, changes
        )
        if not membership:
            existing = await project_repository.find_member(project_id, member_user_id)
            if not existing:
                raise HTTPException(
                    status_code=404,
                    detail={"code": policy["error_codes"]["entity_not_found"]},
                )
            raise HTTPException(
                status_code=409,
                detail={
                    "code": policy["error_codes"]["revision_conflict"],
                    "current_revision": existing["membership_revision"],
                },
            )
        remains_active_qa = (
            membership.get("project_role") == qa_role
            and membership.get("status") == statuses["active"]
        )
        if was_active_qa and not remains_active_qa:
            qa_count = await project_repository.count_members_by_role_status(
                project_id, qa_role, statuses["active"]
            )
            if qa_count == 0:
                await project_repository.restore_member(membership, previous, now())
                raise HTTPException(
                    status_code=422,
                    detail={"code": policy["error_codes"]["last_qa_required"]},
                )
        await audit(
            user.id,
            policy["events"]["member_updated"],
            policy["entity_types"]["member"],
            membership["_id"],
            project_id,
            {"user_id": member_user_id, **changes},
        )
        return membership

    @staticmethod
    async def remove_member(project_id, member_user_id, user):
        policy = PROJECT_POLICY
        statuses = policy["membership_statuses"]
        qa_role = policy["creator_role"]
        await get_project(project_id, user, policy["permissions"]["members_manage"])
        membership = await project_repository.find_member(project_id, member_user_id)
        if not membership:
            raise HTTPException(
                status_code=404, detail={"code": policy["error_codes"]["entity_not_found"]}
            )
        if (
            membership.get("project_role") == qa_role
            and membership.get("status") == statuses["active"]
        ):
            qa_count = await project_repository.count_members_by_role_status(
                project_id, qa_role, statuses["active"]
            )
            if qa_count <= policy["minimum_creator_count"]:
                raise HTTPException(
                    status_code=422,
                    detail={"code": policy["error_codes"]["last_qa_required"]},
                )
        await project_repository.remove_member(project_id, member_user_id)
        await audit(
            user.id,
            policy["events"]["member_removed"],
            policy["entity_types"]["member"],
            membership["_id"],
            project_id,
            {"user_id": member_user_id},
        )
        return {"removed": True, "user_id": member_user_id}
