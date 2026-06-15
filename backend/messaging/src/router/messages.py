import json
from typing import Any
from core.database import db_client
from core.dependency import Depends, Query
from core.dependency import get_current_user_from_header as get_current_user
from core.repositories.base_repository import RepositoryFactory
from core.response import APIResponse
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from src.schemas.messages import MessageCreate
from src.services.messages import MessageService

router = APIRouter(prefix="/messages")

async def publish_personal_message(message: dict, receiver_id: str):
    payload = json.dumps(jsonable_encoder(message))
    targets = [receiver_id]
    
    if receiver_id.startswith("group_"):
        group = await RepositoryFactory.get("message_groups").find_one({"_id": receiver_id})
        if group:
            targets = group.get("members", [])
            
    if db_client.redis:
        for target_id in targets:
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
    await publish_personal_message({"type": "new_message", "data": msg}, req.receiver_id)
    return APIResponse(
        data=msg, 
        message="Direct message has been successfully dispatched to intended recipient", 
        status=201
    )

@router.get("/{other_user_id}", response_model=APIResponse[Any])
async def get_messages(
    other_user_id: str,
    cursor: str = None,
    limit: int = Query(50),
    current_user=Depends(get_current_user),
):
    return APIResponse(
        data=await MessageService.get_messages(other_user_id, current_user, limit, cursor),
        message="Requested conversation history has been successfully retrieved from system database",
        status=200,
    )

@router.get("/conversations", response_model=APIResponse[Any])
async def get_conversations(current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.get_conversations(current_user),
        message="Active conversation list for current user has been successfully compiled",
        status=200,
    )

@router.post("/{message_id}/pin", response_model=APIResponse[Any])
async def toggle_pin(message_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.toggle_pin(message_id, current_user)
    if result is None:
        return APIResponse(
            message="System unable to locate specified message or permissions are insufficient", 
            status=404
        )
    if result == "limit_reached":
        return APIResponse(
            message="Operation rejected because maximum allowed limit of pinned messages exceeded", 
            status=400
        )
        
    other_id = result["receiver_id"] if result["sender_id"] == str(current_user.id) else result["sender_id"]
    await publish_personal_message({"type": "message_pinned", "data": result}, other_id)
    return APIResponse(
        data=result["is_pinned"], 
        message="Pinned status of specified message has been successfully updated", 
        status=200
    )

@router.put("/{message_id}", response_model=APIResponse[Any])
async def edit_message(message_id: str, req: dict, current_user=Depends(get_current_user)):
    content = req.get("content")
    if not content:
        return APIResponse(
            message="Modification request rejected because submitted message content cannot be empty", 
            status=400
        )
        
    result = await MessageService.edit_message(message_id, content, current_user)
    if not result:
        return APIResponse(
            message="Specified message cannot be modified due to strict security constraints", 
            status=403
        )
        
    other_id = result["receiver_id"] if result["sender_id"] == str(current_user.id) else result["sender_id"]
    await publish_personal_message({"type": "message_edited", "data": result}, other_id)
    return APIResponse(
        data=result, 
        message="Content of specified message has been successfully modified and updated", 
        status=200
    )

@router.delete("/{message_id}", response_model=APIResponse[Any])
async def recall_message(message_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.recall_message(message_id, current_user)
    if not result:
        return APIResponse(
            message="Operation restricted because you lack permissions to recall this message", 
            status=403
        )
        
    other_id = result["receiver_id"] if result["sender_id"] == str(current_user.id) else result["sender_id"]
    await publish_personal_message({"type": "message_recalled", "data": result}, other_id)
    return APIResponse(
        data=result, 
        message="Specified message successfully recalled and removed from active thread", 
        status=200
    )

@router.get("/{other_user_id}/search", response_model=APIResponse[Any])
async def search_messages(other_user_id: str, q: str = Query(...), current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.search_messages(other_user_id, q, current_user),
        message="Message search operation successfully executed across specified conversation history",
    )

@router.post("/{message_id}/reactions", response_model=APIResponse[Any])
async def add_reaction(message_id: str, req: dict, current_user=Depends(get_current_user)):
    reaction = req.get("reaction")
    result = await MessageService.add_reaction(message_id, reaction, current_user)
    if not result:
        return APIResponse(
            message="Requested reaction operation currently unavailable for this specific message", 
            status=400
        )
        
    other_id = result["receiver_id"] if result["sender_id"] == str(current_user.id) else result["sender_id"]
    await publish_personal_message({"type": "message_reaction", "data": result}, other_id)
    return APIResponse(
        data=result, 
        message="Interaction metric for specified message has been successfully recorded"
    )

@router.post("/{other_user_id}/read", response_model=APIResponse[Any])
async def mark_as_read(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.mark_as_read(other_user_id, current_user)
    await publish_personal_message(
        {"type": "messages_read", "data": {"viewer_id": str(current_user.id)}}, 
        other_user_id
    )
    return APIResponse(
        data=result, 
        message="Conversation thread successfully marked as read for current active user"
    )

@router.post("/{receiver_id}/documents/share", response_model=APIResponse[Any])
async def share_document(receiver_id: str, req: dict, current_user=Depends(get_current_user)):
    document_id = req.get("document_id")
    if not document_id:
        return APIResponse(
            message="Sharing operation aborted due to missing document identification parameters", 
            status=400
        )
        
    result = await MessageService.share_document(receiver_id, document_id, current_user)
    if not result:
        return APIResponse(
            message="System unable to locate specified document within core storage repository", 
            status=404
        )
        
    await publish_personal_message({"type": "new_message", "data": result}, receiver_id)
    return APIResponse(
        data=result, 
        message="Specified document successfully shared with designated external recipient profile", 
        status=201
    )

@router.get("/{other_user_id}/documents/shared", response_model=APIResponse[Any])
async def get_shared_attachments(other_user_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.get_shared_attachments(other_user_id, current_user),
        message="Shared multimedia and document attachments successfully retrieved from history",
    )

@router.post("/{other_user_id}/block", response_model=APIResponse[Any])
async def block_user(other_user_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.block_user(other_user_id, current_user),
        message="Specified user account successfully restricted from initiating further communications",
    )

@router.post("/{other_user_id}/unblock", response_model=APIResponse[Any])
async def unblock_user(other_user_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.unblock_user(other_user_id, current_user),
        message="Communication restrictions for specified user account have been successfully lifted",
    )

@router.get("/{other_user_id}/block-status", response_model=APIResponse[Any])
async def get_blocked_status(other_user_id: str, current_user=Depends(get_current_user)):
    blocked = await MessageService.check_blocked_status(str(current_user.id), other_user_id)
    return APIResponse(
        data={"is_blocked": blocked}, 
        message="Interaction restriction status between specified accounts successfully verified"
    )

@router.post("/conversations/{other_user_id}/pin", response_model=APIResponse[Any])
async def toggle_pin_conversation(other_user_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.toggle_pin_conversation(other_user_id, current_user),
        message="Prioritization status of selected conversation successfully updated in system",
    )

@router.post("/{message_id}/translate", response_model=APIResponse[Any])
async def translate_message(message_id: str, req: dict, current_user=Depends(get_current_user)):
    target_lang = req.get("target_lang", "vi")
    result = await MessageService.translate_message(message_id, target_lang, current_user)
    if not result:
        return APIResponse(
            message="System unable to locate specified message for requested translation process", 
            status=404
        )
        
    other_id = result.get("receiver_id")
    if other_id:
        await publish_personal_message(
            {"type": "message_translated", "data": {**result, "message_id": message_id}},
            other_id,
        )
    return APIResponse(
        data=result, 
        message="Specified message content successfully translated into requested target language"
    )

@router.post("/groups", response_model=APIResponse[Any])
async def create_group(req: dict, current_user=Depends(get_current_user)):
    group_name = req.get("group_name")
    member_ids = req.get("member_ids", [])
    if not group_name:
        return APIResponse(
            message="Group creation request rejected because valid group name is required", 
            status=400
        )
        
    result = await MessageService.create_group(group_name, member_ids, current_user)
    return APIResponse(
        data=result, 
        message="New communication group successfully provisioned and initialized within system", 
        status=201
    )

@router.post("/{other_user_id}/drafts", response_model=APIResponse[Any])
async def save_draft(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    content = req.get("content", "")
    result = await MessageService.save_draft(other_user_id, content, current_user)
    return APIResponse(
        data=result, 
        message="Message draft successfully preserved in system cache for future editing"
    )

@router.get("/{other_user_id}/drafts", response_model=APIResponse[Any])
async def get_draft(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.get_draft(other_user_id, current_user)
    return APIResponse(
        data=result, 
        message="Previously saved message draft successfully retrieved from local system cache"
    )

@router.post("/{other_user_id}/self-destruct", response_model=APIResponse[Any])
async def toggle_self_destruct(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    seconds = req.get("seconds", 0)
    result = await MessageService.toggle_self_destruct(other_user_id, seconds, current_user)
    await publish_personal_message(
        {"type": "conversation_settings_updated", "data": {"self_destruct_seconds": seconds}},
        other_user_id,
    )
    return APIResponse(
        data=result, 
        message="Automated self destruction timer for conversation successfully configured and applied"
    )

@router.post("/{other_user_id}/mute", response_model=APIResponse[Any])
async def toggle_mute(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.toggle_mute(other_user_id, current_user)
    return APIResponse(
        data=result, 
        message="Notification suppression settings for specified conversation successfully updated internally"
    )

@router.get("/{other_user_id}/settings", response_model=APIResponse[Any])
async def get_conversation_settings(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.get_conversation_settings(other_user_id, current_user)
    result["is_online"] = False
    return APIResponse(
        data=result, 
        message="Personalized configuration settings for specified conversation successfully retrieved from database"
    )

@router.delete("/conversations/{other_user_id}", response_model=APIResponse[Any])
async def delete_conversation(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.delete_conversation(other_user_id, current_user)
    return APIResponse(
        data=result, 
        message="Specified conversation history successfully cleared and removed from active inbox"
    )