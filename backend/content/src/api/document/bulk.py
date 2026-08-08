from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Response
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.api.dependency import get_current_user
from src.services.document import DocumentService

router = APIRouter(route_class=LoggingRoute)

@router.post("/thao-tac-hang-loat/xoa", response_model=APIResponse[Any])
async def bulk_delete_documents(req: dict, current_user=Depends(get_current_user)):
    document_ids = req.get("document_ids", [])
    return APIResponse(
        data=await DocumentService.bulk_delete_documents(document_ids, current_user),
        message="Xóa hàng loạt tài liệu hoàn tất",
    )

@router.post("/thao-tac-hang-loat/khoi-phuc", response_model=APIResponse[Any])
async def bulk_restore_documents(req: dict, current_user=Depends(get_current_user)):
    document_ids = req.get("document_ids", [])
    return APIResponse(
        data=await DocumentService.bulk_restore_documents(document_ids, current_user),
        message="Khôi phục hàng loạt tài liệu hoàn tất",
    )

@router.post("/thao-tac-hang-loat/di-chuyen", response_model=APIResponse[Any])
async def bulk_move_documents(req: dict, current_user=Depends(get_current_user)):
    document_ids = req.get("document_ids", [])
    folder_id = req.get("folder_id")
    return APIResponse(
        data=await DocumentService.bulk_move_documents(document_ids, folder_id, current_user),
        message="Di chuyển hàng loạt tài liệu hoàn tất",
    )

@router.post("/thao-tac-hang-loat/xuat")
async def bulk_export_documents(req: dict, current_user=Depends(get_current_user)):
    document_ids = req.get("document_ids", [])
    zip_bytes = await DocumentService.bulk_export_documents(document_ids, current_user)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="documents_export.zip"'},
    )
