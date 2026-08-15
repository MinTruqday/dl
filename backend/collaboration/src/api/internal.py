from fastapi import APIRouter, Depends

from src.core.dependency import verify_internal_token
from src.repositories.cooperation import CooperationRepository

router = APIRouter(prefix="/cong-tac/noi-bo")


@router.post("/quyen", dependencies=[Depends(verify_internal_token)], include_in_schema=False)
async def resolve_collaboration_permission(request: dict):
    document_id = str(request.get("document_id") or "")
    user_id = str(request.get("user_id") or "")
    invitation = await CooperationRepository.find_invite(
        {
            "document_id": document_id,
            "invitee_id": user_id,
            "status": "ACCEPTED",
        }
    )
    role = str((invitation or {}).get("role") or "")
    return {
        "data": {
            "role": role or None,
            "can_edit": role == "editor",
            "can_comment": role in {"editor", "commenter"},
            "can_view": bool(invitation),
        }
    }
