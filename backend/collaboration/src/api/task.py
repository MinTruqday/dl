from typing import Any
from fastapi import APIRouter, Depends
from src.core.logging_route import LoggingRoute
from src.api.dependency import get_db, require_role
from src.schemas.cooperation import (
    CollabTaskCreateRequest,
    TaskCommentCreateRequest,
    UpdateTaskStatusRequest,
)
from src.services.task import TaskService
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/cong-tac")

MEMBER_ROLES = [Role.AUTHOR, Role.READER, Role.ADMIN]

@router.post("/tai-lieu/{document_id}/cong-viec", response_model=APIResponse[Any], status_code=201)
async def create_task(
    document_id: str,
    data: CollabTaskCreateRequest,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await TaskService.create_task(
            document_id, data.task_desc, data.assigned_to, current_user
        ),
        message="Khởi tạo nhiệm vụ cộng tác mới hoàn tất",
        status=201,
    )

@router.get("/tai-lieu/{document_id}/cong-viec", response_model=APIResponse[Any])
async def get_tasks(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await TaskService.get_tasks(document_id, current_user),
        message="Trích xuất danh sách nhiệm vụ cộng tác hoàn tất",
    )

@router.patch("/nhiem-vu/{task_id}", response_model=APIResponse[Any])
async def update_task(
    task_id: str,
    data: UpdateTaskStatusRequest,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await TaskService.update_task(
            task_id, data.is_done, current_user
        ),
        message="Cập nhật trạng thái thực thi nhiệm vụ cộng tác hoàn tất",
    )

@router.post(
    "/nhiem-vu/{task_id}/binh-luan",
    response_model=APIResponse[Any],
    status_code=201,
)
async def add_task_comment(
    task_id: str,
    data: TaskCommentCreateRequest,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await TaskService.add_task_comment(
            task_id, data.comment_text, current_user
        ),
        message="Đăng tải bình luận thảo luận nhiệm vụ hoàn tất",
        status=201,
    )

@router.get("/nhiem-vu/{task_id}/binh-luan", response_model=APIResponse[Any])
async def get_task_comments(
    task_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await TaskService.get_task_comments(task_id, current_user),
        message="Trích xuất danh sách bình luận thảo luận nhiệm vụ hoàn tất",
    )
