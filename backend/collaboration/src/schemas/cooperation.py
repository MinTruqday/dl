from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class CoauthorInviteRequest(BaseModel):
    document_id: Optional[str] = None
    email: str
    role: str = "editor"

class CollaborationResponse(BaseModel):
    status: str

class TransferOwnershipRequest(BaseModel):
    user_id: str

class UpdateCollaboratorRoleRequest(BaseModel):
    role: str

class UpdateCollabAccessRequest(BaseModel):
    access_level: str

class CreateDraftSnapshotRequest(BaseModel):
    version_name: str

class CollabTaskCreateRequest(BaseModel):
    task_desc: str
    assigned_to: Optional[str] = None

class UpdateTaskStatusRequest(BaseModel):
    is_done: bool

class TaskCommentCreateRequest(BaseModel):
    comment_text: str

class CollaborationShareLinkConfig(BaseModel):
    is_active: bool = True
    password: Optional[str] = None
    default_role: str = "editor"
    expires_in_hours: Optional[int] = None

class CollaborationShareLinkJoin(BaseModel):
    password: Optional[str] = None

class CollaborationAccessRequestCreate(BaseModel):
    requested_role: str = "editor"
    message: Optional[str] = None

class CollaborationAccessRequestReview(BaseModel):
    status: str
    role: Optional[str] = None

class CollaborationScheduleRule(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: datetime
    mode: str = "EDIT"
    fallback_mode: str = "READ_ONLY"
    is_active: bool = True

class CollaborationModeUpdate(BaseModel):
    collaboration_mode: str

class CollaborationScheduleUpdate(BaseModel):
    schedules: List[CollaborationScheduleRule]
