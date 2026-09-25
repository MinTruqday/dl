from fastapi import APIRouter, Depends, Header, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.contracts import (
    WebhookDeliveryRecordInput,
    WebhookReplayInput,
    WebhookSubscriptionCreate,
    WebhookSubscriptionPatch,
)
from src.services.webhook import WebhookService

router = APIRouter(prefix="/kiem-thu", tags=["Móc gọi dự án"])
internal_router = APIRouter(prefix="/noi-bo/kiem-thu/moc-goi", tags=["Móc gọi nội bộ"])


@router.get("/du-an/{project_id}/moc-goi")
async def list_webhook_subscriptions(
    project_id: str,
    include_disabled: bool = Query(default=True),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(
        await WebhookService.list_subscriptions(project_id, include_disabled, user)
    )


@router.post("/du-an/{project_id}/moc-goi", status_code=201)
async def create_webhook_subscription(
    project_id: str,
    payload: WebhookSubscriptionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await WebhookService.create_subscription(project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.patch("/du-an/{project_id}/moc-goi/{subscription_id}")
async def update_webhook_subscription(
    project_id: str,
    subscription_id: str,
    payload: WebhookSubscriptionPatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await WebhookService.update_subscription(
        project_id, subscription_id, payload, user
    )
    return envelope(value, revision=value["revision"])


@router.get("/du-an/{project_id}/moc-goi/giao-hang")
async def list_webhook_deliveries(
    project_id: str,
    status: str = Query(default="", max_length=30),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await WebhookService.list_deliveries(project_id, status, user))


@router.post("/du-an/{project_id}/moc-goi/giao-hang/{delivery_id}/phat-lai", status_code=202)
async def replay_webhook_delivery(
    project_id: str,
    delivery_id: str,
    payload: WebhookReplayInput,
    user: CurrentUser = Depends(get_current_user),
):
    value = await WebhookService.replay_delivery(project_id, delivery_id, payload, user)
    return envelope(value, operation_id=value["_id"])


@internal_router.post("/ket-qua", include_in_schema=False)
async def record_webhook_delivery(
    payload: WebhookDeliveryRecordInput, x_internal_token: str = Header(default="")
):
    return envelope(await WebhookService.record_delivery(payload, x_internal_token))
