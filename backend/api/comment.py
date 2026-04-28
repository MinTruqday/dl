from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, status
from typing import List, Optional, Any
from models.user import UserInDB
from models.comment import CommentCreate, CommentResponse
from api.dependencies import get_current_user, require_permissions, RateLimiter
from services.comment import CommentService
from pydantic import BaseModel

router = APIRouter()

class CommentRequest(BaseModel):
    item_id: str
    item_type: str
    content: str
    parent_id: Optional[str] = None

class CommentEditRequest(BaseModel):
    content: str

@router.post("/comments", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(calls=15, period=60))])
async def create_feed_comment(req: CommentRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await CommentService.create_feed_comment(req, current_user), message="Đăng bình luận thành công.", status=201)

@router.post("/items/{item_id}/comments", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED)
async def create_nested_comment(item_id: str, comment_in: CommentCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await CommentService.create_nested_comment(item_id, comment_in, current_user), message="Gửi bình luận thành công.", status=201)

@router.get("/items/{item_id}/comments", response_model=APIResponse[Any])
async def get_nested_comments(item_id: str, current_user: Optional[UserInDB] = Depends(get_current_user)):
    return APIResponse(data=await CommentService.get_nested_comments(item_id, current_user), message="Lấy danh sách bình luận thành công.", status=200)

@router.delete("/items/comments/{comment_id}", response_model=APIResponse[Any])
async def delete_comment_rbac(comment_id: str, current_user: UserInDB = Depends(require_permissions(["comments:delete_any"]))):
    await CommentService.delete_comment(comment_id)
    return APIResponse(data=None, message="Xóa bình luận thành công.", status=200)

@router.put("/comments/{comment_id}", response_model=APIResponse[Any])
async def edit_comment(comment_id: str, data: CommentEditRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await CommentService.edit_comment(comment_id, data.content, current_user), message="Chỉnh sửa bình luận thành công.", status=200)

@router.get("/posts/{post_id}/comments", response_model=APIResponse[Any])
async def get_post_comments(post_id: str, current_user: Optional[UserInDB] = Depends(get_current_user)):
    return APIResponse(data=await CommentService.get_nested_comments(post_id, current_user), message="Lấy danh sách bình luận bài viết thành công.", status=200)

