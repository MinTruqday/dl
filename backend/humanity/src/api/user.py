from fastapi import APIRouter, Depends, Query, Request
from typing import Any
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.core.dependency import get_current_user, get_db, require_role, CurrentUser
from src.services.user import UserService
from src.schemas.user import Role, UpdateRoleRequest, UpdateStatusRequest, CreateUserRequest

router = APIRouter(route_class=LoggingRoute, prefix="/nguoi-dung")

@router.get("", response_model=APIResponse[Any], dependencies=[Depends(require_role([Role.ADMIN]))])
async def get_all_users(limit: int = 50, offset: int = 0, db=Depends(get_db)):
    return APIResponse(data=await UserService.get_all_users(limit, offset), message="Truy xuất danh sách người dùng thành công")

@router.get("/tim-kiem", response_model=APIResponse[Any])
async def search_users(q: str = "", limit: int = 50, db=Depends(get_db)):
    return APIResponse(data=await UserService.search_users(q, limit), message="Truy xuất kết quả tìm kiếm người dùng thành công")

@router.put("/{user_id}/vai-tro", response_model=APIResponse[Any], dependencies=[Depends(require_role([Role.ADMIN]))])
async def update_user_role(user_id: str, req: UpdateRoleRequest, db=Depends(get_db)):
    return APIResponse(data=await UserService.update_user_role(user_id, req.role), message="Cập nhật quyền hạn hệ thống thành công")

@router.put("/{user_id}/trang-thai", response_model=APIResponse[Any], dependencies=[Depends(require_role([Role.ADMIN]))])
async def update_user_status(user_id: str, req: UpdateStatusRequest, db=Depends(get_db)):
    return APIResponse(data=await UserService.update_user_status(user_id, req.is_active), message="Cập nhật trạng thái hoạt động thành công")

@router.post("/", response_model=APIResponse[Any], include_in_schema=False)
async def create_user(req: CreateUserRequest, db=Depends(get_db)):
    user_id = await UserService.create_user(req)
    return APIResponse(data={"user_id": user_id}, message="Khởi tạo dữ liệu người dùng thành công", status=201)

@router.get("/email/{email}", response_model=APIResponse[Any], include_in_schema=False)
async def get_user_by_email(email: str, db=Depends(get_db)):
    from src.repositories.user import UserRepository
    user = await UserRepository.get_user_by_email(email)
    if user: user["_id"] = str(user["_id"])
    return APIResponse(data=user, message="Truy xuất thông tin người dùng thành công")

@router.get("/{user_id}", response_model=APIResponse[Any], include_in_schema=False)
async def get_user_by_id(user_id: str, db=Depends(get_db)):
    from src.repositories.user import UserRepository
    user = await UserRepository.get_user_by_id(user_id)
    if user: user["_id"] = str(user["_id"])
    return APIResponse(data=user, message="Truy xuất thông tin người dùng thành công")

@router.post("/hang-loat", response_model=APIResponse[Any], include_in_schema=False)
async def get_users_by_ids(user_ids: list[str], db=Depends(get_db)):
    from src.repositories.user import UserRepository
    users = await UserRepository.get_users_by_ids(user_ids)
    for u in users:
        u["_id"] = str(u["_id"])
    return APIResponse(data=users, message="Truy xuất danh sách người dùng thành công")

@router.put("/{user_id}", response_model=APIResponse[Any], include_in_schema=False)
async def update_user(user_id: str, request: Request, db=Depends(get_db)):
    from src.repositories.user import UserRepository
    data = await request.json()
    await UserRepository.update_user(user_id, data)
    return APIResponse(data=None, message="Cập nhật thông tin hệ thống thành công")

@router.get("/ten-mien/{slug}", response_model=APIResponse[Any], include_in_schema=False)
async def get_user_by_slug(slug: str, db=Depends(get_db)):
    from src.repositories.user import UserRepository
    user = await UserRepository.get_user_by_slug(slug)
    if user: user["_id"] = str(user["_id"])
    return APIResponse(data=user, message="Truy xuất thông tin người dùng thành công")
