import json
from typing import Any
from core.database import db_client
from fastapi import APIRouter, Depends, Query
from core.dependency import get_current_user_from_header as get_current_user
from core.repositories.base import RepositoryFactory
from core.response import APIResponse
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from src.schemas.messages import MessageCreate
from src.services.messages import MessageService

router = APIRouter(prefix="/tin-nhan")

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
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", 
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
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.get("/hoi-thoai", response_model=APIResponse[Any])
async def get_conversations(current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.get_conversations(current_user),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.post("/{message_id}/ghim-trang", response_model=APIResponse[Any])
async def toggle_pin(message_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.toggle_pin(message_id, current_user)
    if result is None:
        return APIResponse(
            message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", 
            status=404
        )
    if result == "limit_reached":
        return APIResponse(
            message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", 
            status=400
        )
        
    other_id = result["receiver_id"] if result["sender_id"] == str(current_user.get("id")) else result["sender_id"]
    await publish_personal_message({"type": "message_pinned", "data": result}, other_id)
    return APIResponse(
        data=result["is_pinned"], 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", 
        status=200
    )

@router.put("/{message_id}", response_model=APIResponse[Any])
async def edit_message(message_id: str, req: dict, current_user=Depends(get_current_user)):
    content = req.get("content")
    if not content:
        return APIResponse(
            message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", 
            status=400
        )
        
    result = await MessageService.edit_message(message_id, content, current_user)
    if not result:
        return APIResponse(
            message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", 
            status=403
        )
        
    other_id = result["receiver_id"] if result["sender_id"] == str(current_user.get("id")) else result["sender_id"]
    await publish_personal_message({"type": "message_edited", "data": result}, other_id)
    return APIResponse(
        data=result, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", 
        status=200
    )

@router.delete("/{message_id}", response_model=APIResponse[Any])
async def recall_message(message_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.recall_message(message_id, current_user)
    if not result:
        return APIResponse(
            message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", 
            status=403
        )
        
    other_id = result["receiver_id"] if result["sender_id"] == str(current_user.get("id")) else result["sender_id"]
    await publish_personal_message({"type": "message_recalled", "data": result}, other_id)
    return APIResponse(
        data=result, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", 
        status=200
    )

@router.get("/{other_user_id}/tim-kiem", response_model=APIResponse[Any])
async def search_messages(other_user_id: str, q: str = Query(...), current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.search_messages(other_user_id, q, current_user),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/{message_id}/phan-ung", response_model=APIResponse[Any])
async def add_reaction(message_id: str, req: dict, current_user=Depends(get_current_user)):
    reaction = req.get("reaction")
    result = await MessageService.add_reaction(message_id, reaction, current_user)
    if not result:
        return APIResponse(
            message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", 
            status=400
        )
        
    other_id = result["receiver_id"] if result["sender_id"] == str(current_user.get("id")) else result["sender_id"]
    await publish_personal_message({"type": "message_reaction", "data": result}, other_id)
    return APIResponse(
        data=result, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.post("/{other_user_id}/doc-hieu", response_model=APIResponse[Any])
async def mark_as_read(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.mark_as_read(other_user_id, current_user)
    await publish_personal_message(
        {"type": "messages_read", "data": {"viewer_id": str(current_user.get("id"))}}, 
        other_user_id
    )
    return APIResponse(
        data=result, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.post("/{receiver_id}/tai-lieu/chia-se", response_model=APIResponse[Any])
async def share_document(receiver_id: str, req: dict, current_user=Depends(get_current_user)):
    document_id = req.get("document_id")
    if not document_id:
        return APIResponse(
            message="Lỗi khi truy xuất tài liệu", 
            status=400
        )
        
    result = await MessageService.share_document(receiver_id, document_id, current_user)
    if not result:
        return APIResponse(
            message="Lỗi truy xuất cơ sở dữ liệu hệ thống", 
            status=404
        )
        
    await publish_personal_message({"type": "new_message", "data": result}, receiver_id)
    return APIResponse(
        data=result, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", 
        status=201
    )

@router.get("/{other_user_id}/tai-lieu/da-chia-se", response_model=APIResponse[Any])
async def get_shared_attachments(other_user_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.get_shared_attachments(other_user_id, current_user),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/{other_user_id}/block", response_model=APIResponse[Any])
async def block_user(other_user_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.block_user(other_user_id, current_user),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/{other_user_id}/bo-chan", response_model=APIResponse[Any])
async def unblock_user(other_user_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.unblock_user(other_user_id, current_user),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.get("/{other_user_id}/block-trang-thai", response_model=APIResponse[Any])
async def get_blocked_status(other_user_id: str, current_user=Depends(get_current_user)):
    blocked = await MessageService.check_blocked_status(str(current_user.get("id")), other_user_id)
    return APIResponse(
        data={"is_blocked": blocked}, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.post("/hoi-thoai/{other_user_id}/ghim-trang", response_model=APIResponse[Any])
async def toggle_pin_conversation(other_user_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await MessageService.toggle_pin_conversation(other_user_id, current_user),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/{message_id}/phien-dich", response_model=APIResponse[Any])
async def translate_message(message_id: str, req: dict, current_user=Depends(get_current_user)):
    target_lang = req.get("target_lang", "vi")
    result = await MessageService.translate_message(message_id, target_lang, current_user)
    if not result:
        return APIResponse(
            message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", 
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
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.post("/hoi-nhom", response_model=APIResponse[Any])
async def create_group(req: dict, current_user=Depends(get_current_user)):
    group_name = req.get("group_name")
    member_ids = req.get("member_ids", [])
    if not group_name:
        return APIResponse(
            message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn", 
            status=400
        )
        
    result = await MessageService.create_group(group_name, member_ids, current_user)
    return APIResponse(
        data=result, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", 
        status=201
    )

@router.post("/{other_user_id}/cam-quyen-nhap-lieu", response_model=APIResponse[Any])
async def save_draft(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    content = req.get("content", "")
    result = await MessageService.save_draft(other_user_id, content, current_user)
    return APIResponse(
        data=result, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.get("/{other_user_id}/cam-quyen-nhap-lieu", response_model=APIResponse[Any])
async def get_draft(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.get_draft(other_user_id, current_user)
    return APIResponse(
        data=result, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.post("/{other_user_id}/ca-nhan-huy-bo-diet", response_model=APIResponse[Any])
async def toggle_self_destruct(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    seconds = req.get("seconds", 0)
    result = await MessageService.toggle_self_destruct(other_user_id, seconds, current_user)
    await publish_personal_message(
        {"type": "conversation_settings_updated", "data": {"self_destruct_seconds": seconds}},
        other_user_id,
    )
    return APIResponse(
        data=result, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.post("/{other_user_id}/tat-am", response_model=APIResponse[Any])
async def toggle_mute(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.toggle_mute(other_user_id, current_user)
    return APIResponse(
        data=result, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.get("/{other_user_id}/cai-dat", response_model=APIResponse[Any])
async def get_conversation_settings(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.get_conversation_settings(other_user_id, current_user)
    result["is_online"] = False
    return APIResponse(
        data=result, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.delete("/hoi-thoai/{other_user_id}", response_model=APIResponse[Any])
async def delete_conversation(other_user_id: str, current_user=Depends(get_current_user)):
    result = await MessageService.delete_conversation(other_user_id, current_user)
    return APIResponse(
        data=result, 
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )