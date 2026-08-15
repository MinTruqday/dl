from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from typing import Any
from src.core.response import APIResponse
from src.core.dependency import get_current_user, get_db, require_role, verify_internal_token, CurrentUser
from src.services.user import UserService
from src.schemas.user import Role, UpdateRoleRequest, UpdateStatusRequest, CreateUserRequest

router = APIRouter(prefix="/nguoi-dung")

@router.get("", response_model=APIResponse[Any], dependencies=[Depends(require_role([Role.ADMIN]))])
async def get_all_users(limit: int = 50, offset: int = 0, db=Depends(get_db)):
    return APIResponse(data=await UserService.get_all_users(limit, offset), message="Trích xuất danh sách người dùng hoàn tất")

@router.get("/tim-kiem", response_model=APIResponse[Any])
async def search_users(q: str = "", limit: int = Query(default=50, ge=1, le=100), current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await UserService.search_users(q, limit), message="Trích xuất kết quả tìm kiếm người dùng hoàn tất")

@router.put("/{user_id}/vai-tro", response_model=APIResponse[Any], dependencies=[Depends(require_role([Role.ADMIN]))])
async def update_user_role(user_id: str, req: UpdateRoleRequest, db=Depends(get_db)):
    return APIResponse(data=await UserService.update_user_role(user_id, req.role), message="Cập nhật quyền hạn hệ thống hoàn tất")

@router.put("/{user_id}/trang-thai", response_model=APIResponse[Any], dependencies=[Depends(require_role([Role.ADMIN]))])
async def update_user_status(user_id: str, req: UpdateStatusRequest, db=Depends(get_db)):
    return APIResponse(data=await UserService.update_user_status(user_id, req.is_active), message="Cập nhật trạng thái hoạt động hoàn tất")

@router.post("/", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED, include_in_schema=False, dependencies=[Depends(verify_internal_token)])
async def create_user(req: CreateUserRequest, db=Depends(get_db)):
    user_id = await UserService.create_user(req)
    return APIResponse(data={"user_id": user_id}, message="Khởi tạo dữ liệu người dùng hoàn tất", status=201)

@router.get("/email/{email}", response_model=APIResponse[Any], include_in_schema=False, dependencies=[Depends(verify_internal_token)])
async def get_user_by_email(email: str, db=Depends(get_db)):
    from src.repositories.user import UserRepository
    user = await UserRepository.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng tương ứng")
    user["_id"] = str(user["_id"])
    return APIResponse(data=user, message="Trích xuất thông tin người dùng hoàn tất")

@router.get("/{user_id}", response_model=APIResponse[Any], include_in_schema=False, dependencies=[Depends(verify_internal_token)])
async def get_user_by_id(user_id: str, db=Depends(get_db)):
    from src.repositories.user import UserRepository
    user = await UserRepository.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng tương ứng")
    user["_id"] = str(user["_id"])
    return APIResponse(data=user, message="Trích xuất thông tin người dùng hoàn tất")

@router.post("/hang-loat", response_model=APIResponse[Any], include_in_schema=False, dependencies=[Depends(verify_internal_token)])
async def get_users_by_ids(user_ids: list[str], db=Depends(get_db)):
    from src.repositories.user import UserRepository
    users = await UserRepository.get_users_by_ids(user_ids)
    for u in users:
        u["_id"] = str(u["_id"])
    return APIResponse(data=users, message="Trích xuất danh sách người dùng hoàn tất")

@router.post("/noi-bo/tim", include_in_schema=False, dependencies=[Depends(verify_internal_token)])
async def find_internal_user(req: dict, db=Depends(get_db)):
    from src.repositories.user import UserRepository
    value = str(req.get("identifier", "")).strip()
    user = await UserRepository.find_by_identifier(value)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng tương ứng")
    user["_id"] = str(user["_id"])
    return {"data": user}

@router.get("/noi-bo/danh-sach", include_in_schema=False, dependencies=[Depends(verify_internal_token)])
async def list_internal_users(limit: int = 100, offset: int = 0, db=Depends(get_db)):
    return {"data": await UserService.get_all_users(min(limit, 100), max(offset, 0))}

@router.get("/noi-bo/thong-ke", include_in_schema=False, dependencies=[Depends(verify_internal_token)])
async def get_internal_stats(db=Depends(get_db)):
    from src.repositories.user import UserRepository
    return {"data": await UserRepository.get_stats()}

@router.put("/{user_id}", response_model=APIResponse[Any], include_in_schema=False, dependencies=[Depends(verify_internal_token)])
async def update_user(user_id: str, request: Request, db=Depends(get_db)):
    data = await request.json()
    await UserService.update_internal_user(user_id, data)
    return APIResponse(data=None, message="Cập nhật thông tin hệ thống hoàn tất")

@router.get("/ten-mien/{slug}", response_model=APIResponse[Any], include_in_schema=False)
async def get_user_by_slug(slug: str, db=Depends(get_db)):
    from src.repositories.user import UserRepository
    user = await UserRepository.get_user_by_slug(slug)
    if user:
        user = UserService.to_public_user(user)
    return APIResponse(data=user, message="Trích xuất thông tin người dùng hoàn tất")

@router.delete("/internal/{user_id}", response_model=APIResponse[Any], include_in_schema=False, dependencies=[Depends(verify_internal_token)])
async def delete_internal_user(user_id: str, db=Depends(get_db)):
    return APIResponse(data=await UserService.delete_internal_user(user_id), message="Thu hồi hồ sơ nội bộ hoàn tất")
