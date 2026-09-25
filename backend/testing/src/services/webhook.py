import hmac

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, get_project_entity, new_id, now, optimistic_patch
from src.core.configuration import settings
from src.repositories import webhook_repository
from src.services.domain_policy import domain_policy


def public_subscription(value):
    result = dict(value)
    result["endpoint_reference"] = "Đã cấu hình" if value.get("endpoint_reference") else None
    result["secret_reference"] = "Đã cấu hình" if value.get("secret_reference") else None
    return result


def public_delivery(value):
    allowed = set(domain_policy("webhook")["delivery_public_fields"])
    return {key: item for key, item in value.items() if key in allowed}


def public_replay_job(value):
    private_fields = set(domain_policy("webhook")["replay_private_fields"])
    return {
        key: item
        for key, item in value.items()
        if key not in private_fields
    }


class WebhookService:
    @staticmethod
    async def list_subscriptions(project_id, include_disabled, user):
        policy = domain_policy("webhook")
        await get_project(project_id, user, "webhook.project.read")
        query = {"project_id": project_id}
        if not include_disabled:
            query["enabled"] = True
        items = await webhook_repository.list_subscriptions(
            query, policy["subscription_limit"]
        )
        return [public_subscription(item) for item in items]

    @staticmethod
    async def create_subscription(project_id, payload, user):
        policy = domain_policy("webhook")
        await get_project(project_id, user, "webhook.project.manage")
        timestamp = now()
        value = {
            "_id": new_id(policy["subscription_id_prefix"]),
            "project_id": project_id,
            **payload.model_dump(),
            "revision": 1,
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await webhook_repository.insert_subscription(value)
        except DuplicateKeyError:
            raise HTTPException(status_code=409, detail={"code": policy["name_exists_code"]})
        await audit(
            user.id,
            "webhook_subscription_created",
            "WebhookSubscription",
            value["_id"],
            project_id,
            {"events": value["events"]},
        )
        return public_subscription(value)

    @staticmethod
    async def update_subscription(project_id, subscription_id, payload, user):
        policy = domain_policy("webhook")
        subscription = await get_project_entity(
            "webhook_subscriptions", subscription_id, user, "webhook.project.manage"
        )
        if subscription["project_id"] != project_id:
            raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
        try:
            updated = await optimistic_patch(
                "webhook_subscriptions",
                subscription_id,
                project_id,
                payload.expected_revision,
                payload.model_dump(exclude_unset=True),
            )
        except DuplicateKeyError:
            raise HTTPException(status_code=409, detail={"code": policy["name_exists_code"]})
        await audit(
            user.id,
            "webhook_subscription_updated",
            "WebhookSubscription",
            subscription_id,
            project_id,
            {"enabled": updated.get("enabled")},
        )
        return public_subscription(updated)

    @staticmethod
    async def list_deliveries(project_id, status, user):
        policy = domain_policy("webhook")
        await get_project(project_id, user, "webhook.project.read")
        query = {"project_id": project_id}
        if status:
            if status not in policy["delivery_statuses"]:
                raise HTTPException(
                    status_code=422, detail={"code": policy["status_invalid_code"]}
                )
            query["status"] = status
        items = await webhook_repository.list_deliveries(
            query, policy["delivery_limit"]
        )
        return [public_delivery(item) for item in items]

    @staticmethod
    async def replay_delivery(project_id, delivery_id, payload, user):
        policy = domain_policy("webhook")
        await get_project(project_id, user, "webhook.project.replay")
        existing_job = await webhook_repository.find_replay_job(
            project_id, payload.idempotency_key
        )
        if existing_job:
            if existing_job.get("delivery_id") != delivery_id:
                raise HTTPException(
                    status_code=409, detail={"code": policy["idempotency_reused_code"]}
                )
            return public_replay_job(existing_job)
        delivery = await webhook_repository.find_delivery(delivery_id, project_id)
        if not delivery:
            raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
        if delivery.get("status") != policy["failed_status"]:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["delivery_not_replayable_code"]},
            )
        subscription = await webhook_repository.find_subscription(
            delivery["subscription_id"], project_id, True
        )
        if not subscription:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["subscription_inactive_code"]},
            )
        timestamp = now()
        job = {
            "_id": new_id(policy["replay_id_prefix"]),
            "project_id": project_id,
            "delivery_id": delivery_id,
            "subscription_id": delivery["subscription_id"],
            "endpoint_reference": subscription["endpoint_reference"],
            "secret_reference": subscription["secret_reference"],
            "event_type": delivery["event_type"],
            "payload_hash": delivery["payload_hash"],
            "status": policy["queued_status"],
            "reason": payload.reason,
            "idempotency_key": payload.idempotency_key,
            "requested_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await webhook_repository.insert_replay_job(job)
        except DuplicateKeyError:
            existing_job = await webhook_repository.find_replay_job(
                project_id, payload.idempotency_key
            )
            if existing_job:
                return public_replay_job(existing_job)
            raise
        await webhook_repository.queue_replay(
            delivery_id,
            project_id,
            policy["failed_status"],
            policy["queued_status"],
            job["_id"],
            timestamp,
        )
        await audit(
            user.id,
            "webhook_delivery_replay_queued",
            "WebhookDelivery",
            delivery_id,
            project_id,
            {"operation_id": job["_id"], "reason": payload.reason},
        )
        return public_replay_job(job)

    @staticmethod
    async def record_delivery(payload, internal_token):
        policy = domain_policy("webhook")
        if not hmac.compare_digest(internal_token, settings.SECRET_KEY):
            raise HTTPException(
                status_code=403, detail={"code": policy["invalid_internal_token_code"]}
            )
        subscription = await webhook_repository.find_subscription(
            payload.subscription_id, payload.project_id
        )
        if not subscription:
            raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
        timestamp = now()
        value = {
            "_id": payload.delivery_id,
            **payload.model_dump(exclude={"delivery_id"}),
            "completed_at": timestamp,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        await webhook_repository.upsert_delivery(
            payload.delivery_id, payload.project_id, value
        )
        return public_delivery(value)
