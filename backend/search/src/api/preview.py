from fastapi import APIRouter, Depends
from src.core.response import APIResponse
from src.api.dependency import get_current_user, CurrentUser
from src.services.preview import PreviewService

router = APIRouter()

@router.get("/xem-truoc/{item_id}", response_model=APIResponse[dict])
async def preview_item_endpoint(
    item_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await PreviewService.get_preview_payload(
        item_id=item_id,
        owner_id=str(current_user.id),
    )
    return APIResponse(data=result, message="Lấy dữ liệu xem trước thành công")
