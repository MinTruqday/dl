from functools import lru_cache

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from pymongo import MongoClient

from src.core.common import audit, get_project, new_id, now, optimistic_patch
from src.core.configuration import settings
from src.repositories.project_notification import project_notification_repository


@lru_cache(maxsize=1)
def notification_policy():
    client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        document = client[settings.TESTING_DB_NAME].runtime_policies.find_one(
            {"_id": "project_notification"}, {"_id": 0, "values": 1}
        )
    finally:
        client.close()
    values = document.get("values") if isinstance(document, dict) else None
    if not isinstance(values, dict) or not isinstance(values.get("artifact_collections"), dict):
        raise RuntimeError("Thiếu chính sách thông báo dự án")
    return values




def artifact_label(artifact):
    return (
        artifact.get("requirement_key")
        or artifact.get("test_case_key")
        or artifact.get("name")
        or artifact.get("defect_key")
        or artifact.get("title")
    )


def default_rules(project_id):
    policy = notification_policy()
    return {
        "_id": f"{policy['rule_id_prefix']}{project_id}",
        "project_id": project_id,
        "enabled_events": [],
        "channels": policy["default_channels"],
        "target_roles": policy["default_target_roles"],
        "escalation_minutes": None,
        "revision": policy["initial_revision"],
    }


def default_preferences(project_id, user_id):
    policy = notification_policy()
    return {
        "_id": f"{policy['preference_id_prefix']}{project_id}:{user_id}",
        "project_id": project_id,
        "user_id": user_id,
        "digest_frequency": policy["default_digest_frequency"],
        "channels": policy["default_channels"],
        "muted_events": [],
        "quiet_hours_start": None,
        "quiet_hours_end": None,
        "timezone": policy["default_timezone"],
        "revision": policy["initial_revision"],
    }


class ProjectNotificationService:
    @staticmethod
    async def require_artifact(project_id, artifact_type, artifact_id):
        policy = notification_policy()
        collection = policy["artifact_collections"].get(artifact_type)
        if not collection:
            raise HTTPException(
                status_code=422,
                detail={"code": policy["invalid_artifact_type_code"]},
            )
        if not await project_notification_repository.artifact_exists(
            collection, project_id, artifact_id
        ):
            raise HTTPException(
                status_code=404,
                detail={"code": policy["entity_not_found_code"]},
            )

    @staticmethod
    async def list_watches(project_id, artifact_type, user):
        await get_project(project_id, user, "notification.watch.manage")
        policy = notification_policy()
        collections = policy["artifact_collections"]
        query = {"project_id": project_id, "user_id": user.id}
        if artifact_type:
            if artifact_type not in collections:
                raise HTTPException(
                    status_code=422,
                    detail={"code": policy["invalid_artifact_type_code"]},
                )
            query["artifact_type"] = artifact_type
        items = await project_notification_repository.list_subscriptions(query)
        for artifact_type_value, collection_name in collections.items():
            matching = [
                item for item in items if item.get("artifact_type") == artifact_type_value
            ]
            identifiers = [item.get("artifact_id") for item in matching if item.get("artifact_id")]
            if not identifiers:
                continue
            artifacts = await project_notification_repository.list_artifact_labels(
                collection_name, project_id, identifiers
            )
            labels = {item["_id"]: artifact_label(item) for item in artifacts}
            for item in matching:
                item["artifact_label"] = labels.get(item.get("artifact_id")) or item.get(
                    "artifact_id"
                )
        return items

    @classmethod
    async def set_watch(cls, project_id, artifact_type, artifact_id, payload, user):
        await get_project(project_id, user, "notification.watch.manage")
        await cls.require_artifact(project_id, artifact_type, artifact_id)
        scope = {
            "project_id": project_id,
            "user_id": user.id,
            "artifact_type": artifact_type,
            "artifact_id": artifact_id,
        }
        if not payload.watching:
            await project_notification_repository.remove_subscription(scope)
            await audit(user.id, "notification_watch_removed", artifact_type, artifact_id, project_id)
            return {**scope, "watching": False}
        timestamp = now()
        subscription = await project_notification_repository.set_subscription(
            scope,
            new_id('NSUB'),
            timestamp,
        )
        await audit(user.id, "notification_watch_added", artifact_type, artifact_id, project_id)
        return {**subscription, "watching": True}

    @staticmethod
    async def get_rules(project_id, user):
        await get_project(project_id, user, "notification.project_rule.manage")
        value = await project_notification_repository.find_rules(project_id)
        return value or default_rules(project_id)

    @staticmethod
    async def update_rules(project_id, payload, user):
        await get_project(project_id, user, "notification.project_rule.manage")
        current = await project_notification_repository.find_rules(project_id)
        changes = payload.model_dump(exclude={"expected_revision"})
        if current:
            updated = await optimistic_patch(
                "project_notification_rules",
                current["_id"],
                project_id,
                payload.expected_revision,
                changes,
            )
        else:
            if payload.expected_revision != notification_policy()["initial_revision"]:
                raise HTTPException(
                    status_code=409,
                    detail={"code": notification_policy()["revision_conflict_code"]},
                )
            timestamp = now()
            updated = {
                **default_rules(project_id),
                **changes,
                "revision": notification_policy()["created_revision"],
                "created_by": user.id,
                "created_at": timestamp,
                "updated_at": timestamp,
            }
            try:
                await project_notification_repository.insert_rules(updated)
            except DuplicateKeyError:
                raise HTTPException(
                    status_code=409,
                    detail={"code": notification_policy()["revision_conflict_code"]},
                )
        await audit(
            user.id,
            "project_notification_rules_updated",
            "ProjectNotificationRule",
            updated["_id"],
            project_id,
        )
        return updated

    @staticmethod
    async def get_preferences(project_id, user):
        await get_project(project_id, user, "notification.preferences.manage")
        value = await project_notification_repository.find_preferences(project_id, user.id)
        return value or default_preferences(project_id, user.id)

    @staticmethod
    async def update_preferences(project_id, payload, user):
        await get_project(project_id, user, "notification.preferences.manage")
        current = await project_notification_repository.find_preferences(project_id, user.id)
        changes = payload.model_dump(exclude={"expected_revision"})
        if current:
            updated = await optimistic_patch(
                "project_notification_preferences",
                current["_id"],
                project_id,
                payload.expected_revision,
                changes,
            )
        else:
            if payload.expected_revision != notification_policy()["initial_revision"]:
                raise HTTPException(
                    status_code=409,
                    detail={"code": notification_policy()["revision_conflict_code"]},
                )
            timestamp = now()
            updated = {
                **default_preferences(project_id, user.id),
                **changes,
                "revision": notification_policy()["created_revision"],
                "created_at": timestamp,
                "updated_at": timestamp,
            }
            try:
                await project_notification_repository.insert_preferences(updated)
            except DuplicateKeyError:
                raise HTTPException(
                    status_code=409,
                    detail={"code": notification_policy()["revision_conflict_code"]},
                )
        await audit(
            user.id,
            "project_notification_preferences_updated",
            "ProjectNotificationPreference",
            updated["_id"],
            project_id,
        )
        return updated
