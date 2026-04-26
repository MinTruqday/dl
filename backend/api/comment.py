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

@router.post("/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(calls=15, period=60))])
async def create_feed_comment(req: CommentRequest, current_user: UserInDB = Depends(get_current_user)):
    return await CommentService.create_feed_comment(req, current_user)

@router.post("/items/{item_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_nested_comment(item_id: str, comment_in: CommentCreate, current_user: UserInDB = Depends(get_current_user)):
    return await CommentService.create_nested_comment(item_id, comment_in, current_user)

@router.get("/items/{item_id}/comments", response_model=List[CommentResponse])
async def get_nested_comments(item_id: str, current_user: Optional[UserInDB] = Depends(get_current_user)):
    return await CommentService.get_nested_comments(item_id, current_user)

@router.delete("/items/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_rbac(comment_id: str, current_user: UserInDB = Depends(require_permissions(["comments:delete_any"]))):
    await CommentService.delete_comment(comment_id)
    return status.HTTP_204_NO_CONTENT

class CommentEditRequest(BaseModel):
    content: str

@router.put("/comments/{comment_id}")
async def edit_comment(comment_id: str, data: CommentEditRequest, current_user: UserInDB = Depends(get_current_user)):
    return await CommentService.edit_comment(comment_id, data.content, current_user)

@router.get("/posts/{post_id}/comments")
async def get_post_comments(post_id: str, current_user: Optional[UserInDB] = Depends(get_current_user)):
    return await CommentService.get_nested_comments(post_id, current_user)

