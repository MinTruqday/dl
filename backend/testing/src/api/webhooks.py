import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now, optimistic_patch
from src.core.configuration import settings
from src.core.database import database
from src.domain.schemas import (
    WebhookDeliveryRecordInput,
    WebhookReplayInput,
    WebhookSubscriptionCreate,
    WebhookSubscriptionPatch,
)


router = APIRouter(prefix="/kiem-thu", tags=["Móc gọi dự án"])
internal_router = APIRouter(prefix="/noi-bo/kiem-thu/moc-goi", tags=["Móc gọi nội bộ"])


def public_subscription(value):
    result = dict(value)
    result["endpoint_reference"] = "Đã cấu hình" if value.get("endpoint_reference") else None
    result["secret_reference"] = "Đã cấu hình" if value.get("secret_reference") else None
    return result


def public_delivery(value):
    allowed = {
        "_id",
        "project_id",
        "subscription_id",
        "event_type",
        "status",
        "attempt",
        "response_status",
        "error_code",
        "payload_hash",
        "duration_ms",
        "operation_id",
        "created_at",
        "updated_at",
        "completed_at",
    }
    return {key: item for key, item in value.items() if key in allowed}


def public_replay_job(value):
    return {
        key: item
        for key, item in value.items()
        if key not in {"endpoint_reference", "secret_reference"}
    }


@router.get("/du-an/{project_id}/moc-goi")
async def list_webhook_subscriptions(
    project_id: str,
    include_disabled: bool = Query(default=True),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "webhook.project.read")
    query = {"project_id": project_id}
    if not include_disabled:
        query["enabled"] = True
    items = await database.value.webhook_subscriptions.find(query).sort(
        "updated_at", -1
    ).to_list(500)
    return envelope([public_subscription(item) for item in items])


@router.post("/du-an/{project_id}/moc-goi", status_code=201)
async def create_webhook_subscription(
    project_id: str,
    payload: WebhookSubscriptionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "webhook.project.manage")
    timestamp = now()
    value = {
        "_id": new_id("WHSUB"),
        "project_id": project_id,
        **payload.model_dump(),
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.webhook_subscriptions.insert_one(value)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "WEBHOOK_NAME_EXISTS"})
    await audit(
        user.id,
        "webhook_subscription_created",
        "WebhookSubscription",
        value["_id"],
        project_id,
        {"events": value["events"]},
    )
    return envelope(public_subscription(value), revision=1)


@router.patch("/du-an/{project_id}/moc-goi/{subscription_id}")
async def update_webhook_subscription(
    project_id: str,
    subscription_id: str,
    payload: WebhookSubscriptionPatch,
    user: CurrentUser = Depends(get_current_user),
):
    subscription = await get_project_entity(
        "webhook_subscriptions", subscription_id, user, "webhook.project.manage"
    )
    if subscription["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    try:
        updated = await optimistic_patch(
            "webhook_subscriptions",
            subscription_id,
            project_id,
            payload.expected_revision,
            payload.model_dump(exclude_unset=True),
        )
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "WEBHOOK_NAME_EXISTS"})
    await audit(
        user.id,
        "webhook_subscription_updated",
        "WebhookSubscription",
        subscription_id,
        project_id,
        {"enabled": updated.get("enabled")},
    )
    return envelope(public_subscription(updated), revision=updated["revision"])


@router.get("/du-an/{project_id}/moc-goi/giao-hang")
async def list_webhook_deliveries(
    project_id: str,
    status: str = Query(default="", max_length=30),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "webhook.project.read")
    query = {"project_id": project_id}
    if status:
        if status not in {"QUEUED", "DELIVERED", "FAILED"}:
            raise HTTPException(status_code=422, detail={"code": "WEBHOOK_STATUS_INVALID"})
        query["status"] = status
    items = await database.value.webhook_deliveries.find(query).sort(
        "created_at", -1
    ).to_list(1000)
    return envelope([public_delivery(item) for item in items])


@router.post("/du-an/{project_id}/moc-goi/giao-hang/{delivery_id}/phat-lai", status_code=202)
async def replay_webhook_delivery(
    project_id: str,
    delivery_id: str,
    payload: WebhookReplayInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "webhook.project.replay")
    existing_job = await database.value.webhook_replay_jobs.find_one(
        {"project_id": project_id, "idempotency_key": payload.idempotency_key}
    )
    if existing_job:
        if existing_job.get("delivery_id") != delivery_id:
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
        return envelope(public_replay_job(existing_job), operation_id=existing_job["_id"])
    delivery = await database.value.webhook_deliveries.find_one(
        {"_id": delivery_id, "project_id": project_id}
    )
    if not delivery:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    if delivery.get("status") != "FAILED":
        raise HTTPException(status_code=409, detail={"code": "WEBHOOK_DELIVERY_NOT_REPLAYABLE"})
    subscription = await database.value.webhook_subscriptions.find_one(
        {
            "_id": delivery["subscription_id"],
            "project_id": project_id,
            "enabled": True,
        }
    )
    if not subscription:
        raise HTTPException(status_code=409, detail={"code": "WEBHOOK_SUBSCRIPTION_INACTIVE"})
    timestamp = now()
    job = {
        "_id": new_id("WHOP"),
        "project_id": project_id,
        "delivery_id": delivery_id,
        "subscription_id": delivery["subscription_id"],
        "endpoint_reference": subscription["endpoint_reference"],
        "secret_reference": subscription["secret_reference"],
        "event_type": delivery["event_type"],
        "payload_hash": delivery["payload_hash"],
        "status": "QUEUED",
        "reason": payload.reason,
        "idempotency_key": payload.idempotency_key,
        "requested_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.webhook_replay_jobs.insert_one(job)
    except DuplicateKeyError:
        existing_job = await database.value.webhook_replay_jobs.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if existing_job:
            return envelope(public_replay_job(existing_job), operation_id=existing_job["_id"])
        raise
    await database.value.webhook_deliveries.update_one(
        {"_id": delivery_id, "project_id": project_id, "status": "FAILED"},
        {
            "$set": {
                "status": "QUEUED",
                "operation_id": job["_id"],
                "updated_at": timestamp,
            },
            "$inc": {"attempt": 1},
        },
    )
    await audit(
        user.id,
        "webhook_delivery_replay_queued",
        "WebhookDelivery",
        delivery_id,
        project_id,
        {"operation_id": job["_id"], "reason": payload.reason},
    )
    public_job = public_replay_job(job)
    return envelope(public_job, operation_id=job["_id"])


@internal_router.post("/ket-qua", include_in_schema=False)
async def record_webhook_delivery(
    payload: WebhookDeliveryRecordInput,
    x_internal_token: str = Header(default=""),
):
    if not hmac.compare_digest(x_internal_token, settings.SECRET_KEY):
        raise HTTPException(status_code=403, detail={"code": "INVALID_INTERNAL_TOKEN"})
    subscription = await database.value.webhook_subscriptions.find_one(
        {"_id": payload.subscription_id, "project_id": payload.project_id}
    )
    if not subscription:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    timestamp = now()
    value = {
        "_id": payload.delivery_id,
        **payload.model_dump(exclude={"delivery_id"}),
        "completed_at": timestamp,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await database.value.webhook_deliveries.update_one(
        {"_id": payload.delivery_id, "project_id": payload.project_id},
        {"$set": value},
        upsert=True,
    )
    return envelope(public_delivery(value))
