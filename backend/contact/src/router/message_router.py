import json
from typing import Any, List

from core.database import db_client
from core.dependency import AuthenticatedUser, Depends, Header, HTTPException, Query
from core.dependency import get_current_user_from_header as get_current_user
from core.repositories.base_repository import RepositoryFactory
from core.response import APIResponse
from fastapi import APIRouter
from src.schemas.message_schema import (
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from src.services.message_service import MessageService

router = APIRouter(prefix="/messages")


async def publish_personal_message(message: dict, receiver_id: str):
    import json

    from fastapi.encoders import jsonable_encoder

    payload = json.dumps(jsonable_encoder(message))
    db = db_client.mongodb.get_default_database()
    targets = [receiver_id]
    if receiver_id.startswith("group_"):
        group = await RepositoryFactory.get("message_groups").find_one(
            {"_id": receiver_id}
        )
        if group:
            targets = group.get("members", [])
    for target_id in targets:
        if db_client.redis:
            await db_client.redis.publish(f"message_delivery:{target_id}", payload)


@router.post("/", response_model=APIResponse[Any])
async def send_message(req: MessageCreate, current_user=Depends(get_current_user)):
    msg = await MessageService.send_message(
        req.receiver_id,
        req.content,
        current_user,
        req.image_url,
        req.reply_to_id,
        req.audio_url,
        req.client_msg_id,
    )
    await publish_personal_message(
        {"type": "new_message", "data": msg}, req.receiver_id
    )
    return APIResponse(data=msg, message="Message sent successfully", status=201)


@router.get("/{other_user_id}", response_model=APIResponse[Any])
async def get_messages(
    other_user_id: str,
    cursor: str = None,
    limit: int = Query(50),
    current_user=Depends(get_current_user),
):
    return APIResponse(
        data=await MessageService.get_messages(
            other_user_id, current_user, limit, cursor
        ),
        message="Message history retrieved successfully",
        status=200,
    )


@router.get("/conversations", response_model=APIResponse[Any])
async def get_conversations(current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.get_conversations(current_user),
        message="Conversation list retrieved successfully",
        status=200,
    )


@router.post("/{message_id}/pin", response_model=APIResponse[Any])
async def toggle_pin(message_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.toggle_pin(message_id, current_user)
    if result is None:
        return APIResponse(
            message="Message could not be found or access denied", status=404
        )
    if result == "limit_reached":
        return APIResponse(message="Maximum pinned messages limit (3) exceeded", status=400)
    other_id = (
        result["receiver_id"]
        if result["sender_id"] == current_user.id
        else result["sender_id"]
    )
    await publish_personal_message({"type": "message_pinned", "data": result}, other_id)
    return APIResponse(
        data=result["is_pinned"], message="Message pin status updated successfully", status=200
    )


@router.put("/{message_id}", response_model=APIResponse[Any])
async def edit_message(
    message_id: str, req: dict, current_user=Depends(get_current_user)
):
    content = req.get("content")
    if not content:
        return APIResponse(message="Content cannot be empty", status=400)
    result = await MessageService.edit_message(message_id, content, current_user)
    if not result:
        return APIResponse(
            message="Message cannot be edited at this time", status=403
        )
    other_id = (
        result["receiver_id"]
        if result["sender_id"] == current_user.id
        else result["sender_id"]
    )
    await publish_personal_message({"type": "message_edited", "data": result}, other_id)
    return APIResponse(data=result, message="Message edited successfully", status=200)


@router.delete("/{message_id}", response_model=APIResponse[Any])
async def recall_message(message_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.recall_message(message_id, current_user)
    if not result:
        return APIResponse(message="Action restricted. You do not have permission to recall this message", status=403)
    other_id = (
        result["receiver_id"]
        if result["sender_id"] == current_user.id
        else result["sender_id"]
    )
    await publish_personal_message(
        {"type": "message_recalled", "data": result}, other_id
    )
    return APIResponse(data=result, message="Message recalled successfully", status=200)


@router.get("/{other_user_id}/search", response_model=APIResponse[Any])
async def search_messages(
    other_user_id: str, q: str = Query(...), current_user=Depends(get_current_user)
):
    return APIResponse(
        data=await MessageService.search_messages(other_user_id, q, current_user),
        message="Message search completed successfully",
    )


@router.post("/{message_id}/reactions", response_model=APIResponse[Any])
async def add_reaction(
    message_id: str, req: dict, current_user=Depends(get_current_user)
):
    reaction = req.get("reaction")
    result = await MessageService.add_reaction(message_id, reaction, current_user)
    if not result:
        return APIResponse(
            message="Reaction operation is not available", status=400
        )
    other_id = (
        result["receiver_id"]
        if result["sender_id"] == current_user.id
        else result["sender_id"]
    )
    await publish_personal_message(
        {"type": "message_reaction", "data": result}, other_id
    )
    return APIResponse(data=result, message="Reaction updated successfully")


@router.post("/{other_user_id}/read", response_model=APIResponse[Any])
async def mark_as_read(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.mark_as_read(other_user_id, current_user)
    await publish_personal_message(
        {"type": "messages_read", "data": {"reader_id": current_user.id}}, other_user_id
    )
    return APIResponse(data=result, message="Marked as read successfully")


@router.post("/{receiver_id}/documents/share", response_model=APIResponse[Any])
async def share_document(
    receiver_id: str, req: dict, current_user=Depends(get_current_user)
):
    document_id = req.get("document_id")
    if not document_id:
        return APIResponse(message="Missing document identification", status=400)
    result = await MessageService.share_document(receiver_id, document_id, current_user)
    if not result:
        return APIResponse(message="The specified document could not be found", status=404)
    await publish_personal_message({"type": "new_message", "data": result}, receiver_id)
    return APIResponse(data=result, message="Document shared successfully", status=201)


@router.get("/{other_user_id}/documents/shared", response_model=APIResponse[Any])
async def get_shared_attachments(
    other_user_id: str, current_user=Depends(get_current_user)
):
    return APIResponse(
        data=await MessageService.get_shared_attachments(other_user_id, current_user),
        message="Shared documents retrieved successfully",
    )


@router.post("/{other_user_id}/block", response_model=APIResponse[Any])
async def block_user(other_user_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.block_user(other_user_id, current_user),
        message="User blocked successfully",
    )


@router.post("/{other_user_id}/unblock", response_model=APIResponse[Any])
async def unblock_user(other_user_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.unblock_user(other_user_id, current_user),
        message="User unblocked successfully",
    )


@router.get("/{other_user_id}/block-status", response_model=APIResponse[Any])
async def get_blocked_status(
    other_user_id: str, current_user=Depends(get_current_user)
):
    blocked = await MessageService.check_blocked_status(
        str(current_user.id), other_user_id
    )
    return APIResponse(
        data={"is_blocked": blocked}, message="Block status verified successfully"
    )


@router.post("/conversations/{other_user_id}/pin", response_model=APIResponse[Any])
async def toggle_pin_conversation(
    other_user_id: str, current_user=Depends(get_current_user)
):
    return APIResponse(
        data=await MessageService.toggle_pin_conversation(other_user_id, current_user),
        message="Conversation pin status updated successfully",
    )


@router.post("/{message_id}/translate", response_model=APIResponse[Any])
async def translate_message(
    message_id: str, req: dict, current_user=Depends(get_current_user)
):
    target_lang = req.get("target_lang", "vi")
    result = await MessageService.translate_message(
        message_id, target_lang, current_user
    )
    if not result:
        return APIResponse(message="The specified message could not be found", status=404)
    other_id = result.get("receiver_id")
    if other_id:
        await publish_personal_message(
            {
                "type": "message_translated",
                "data": {**result, "message_id": message_id},
            },
            other_id,
        )
    return APIResponse(data=result, message="Message translation completed")


@router.post("/groups", response_model=APIResponse[Any])
async def create_group(req: dict, current_user=Depends(get_current_user)):
    group_name = req.get("group_name")
    member_ids = req.get("member_ids", [])
    if not group_name:
        return APIResponse(message="Group name cannot be empty", status=400)
    result = await MessageService.create_group(group_name, member_ids, current_user)
    return APIResponse(data=result, message="Group created successfully", status=201)


@router.post("/{other_user_id}/drafts", response_model=APIResponse[Any])
async def save_draft(
    other_user_id: str, req: dict, current_user=Depends(get_current_user)
):
    content = req.get("content", "")
    result = await MessageService.save_draft(other_user_id, content, current_user)
    return APIResponse(data=result, message="Draft saved successfully")


@router.get("/{other_user_id}/drafts", response_model=APIResponse[Any])
async def get_draft(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.get_draft(other_user_id, current_user)
    return APIResponse(data=result, message="Draft retrieved successfully")


@router.post("/{other_user_id}/self-destruct", response_model=APIResponse[Any])
async def toggle_self_destruct(
    other_user_id: str, req: dict, current_user=Depends(get_current_user)
):
    seconds = req.get("seconds", 0)
    result = await MessageService.toggle_self_destruct(
        other_user_id, seconds, current_user
    )
    await publish_personal_message(
        {
            "type": "conversation_settings_updated",
            "data": {"self_destruct_seconds": seconds},
        },
        other_user_id,
    )
    return APIResponse(data=result, message="Self-destruct timer updated successfully")


@router.post("/{other_user_id}/mute", response_model=APIResponse[Any])
async def toggle_mute(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.toggle_mute(other_user_id, current_user)
    return APIResponse(data=result, message="Mute status updated successfully")


@router.get("/{other_user_id}/settings", response_model=APIResponse[Any])
async def get_conversation_settings(
    other_user_id: str, current_user=Depends(get_current_user)
):
    result = await MessageService.get_conversation_settings(other_user_id, current_user)
    is_online = False
    result["is_online"] = is_online
    return APIResponse(data=result, message="Settings retrieved successfully")


@router.delete("/conversations/{other_user_id}", response_model=APIResponse[Any])
async def delete_conversation(
    other_user_id: str, current_user=Depends(get_current_user)
):
    result = await MessageService.delete_conversation(other_user_id, current_user)
    return APIResponse(data=result, message="Conversation deleted successfully")
