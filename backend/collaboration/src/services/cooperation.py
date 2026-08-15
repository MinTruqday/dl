from src.services.activity import ActivityService
from src.services.presence import PresenceService
from src.services.invite import InviteService
from src.services.member import MemberService
from src.services.link import LinkService
from src.services.access_request import AccessRequestService
from src.services.task import TaskService
from src.services.lock import LockService
from src.services.snapshot import SnapshotService
from src.repositories.cooperation import DocumentRepository
from fastapi import HTTPException

class CooperationService:
    log_activity = ActivityService.log_activity
    get_activities = ActivityService.get_activities
    get_contribution_stats = ActivityService.get_contribution_stats

    get_effective_collaboration_status = PresenceService.get_effective_collaboration_status
    update_status = PresenceService.update_status
    get_online_collaborators = PresenceService.get_online_collaborators
    update_collaboration_mode = PresenceService.update_collaboration_mode
    get_collaboration_mode = PresenceService.get_collaboration_mode
    update_collaboration_schedules = PresenceService.update_collaboration_schedules
    get_collaboration_schedules = PresenceService.get_collaboration_schedules

    send_collaboration_invite = InviteService.send_collaboration_invite
    get_my_collaboration_invites = InviteService.get_my_collaboration_invites
    respond_to_collaboration_invite = InviteService.respond_to_collaboration_invite
    get_sent_pending_invites = InviteService.get_sent_pending_invites
    revoke_invite = InviteService.revoke_invite

    get_collaborators = MemberService.get_collaborators
    remove_collaborator = MemberService.remove_collaborator
    update_collaborator_role = MemberService.update_collaborator_role
    transfer_ownership = MemberService.transfer_ownership

    generate_invite_code = LinkService.generate_invite_code
    join_via_invite_code = LinkService.join_via_invite_code
    configure_share_link = LinkService.configure_share_link
    get_share_link_config = LinkService.get_share_link_config
    get_public_share_link_info = LinkService.get_public_share_link_info
    join_via_share_link = LinkService.join_via_share_link

    create_access_request = AccessRequestService.create_access_request
    get_document_access_requests = AccessRequestService.get_document_access_requests
    get_my_incoming_access_requests = AccessRequestService.get_my_incoming_access_requests
    review_access_request = AccessRequestService.review_access_request

    create_task = TaskService.create_task
    get_tasks = TaskService.get_tasks
    update_task = TaskService.update_task
    add_task_comment = TaskService.add_task_comment
    get_task_comments = TaskService.get_task_comments

    acquire_lock = LockService.acquire_lock
    release_lock = LockService.release_lock
    get_lock_status = LockService.get_lock_status

    create_draft_snapshot = SnapshotService.create_draft_snapshot
    get_draft_snapshots = SnapshotService.get_draft_snapshots
    create_snapshot = SnapshotService.create_draft_snapshot
    get_snapshots = SnapshotService.get_draft_snapshots

    @staticmethod
    async def update_collab_access(
        document_id: str, access_level: str, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        if access_level not in ["invite_only", "anyone_with_link"]:
            raise HTTPException(
                status_code=400, detail="Cấu hình mức độ truy cập cộng tác không hợp lệ"
            )
        await DocumentRepository.update_one(
            {"_id": document_id}, {"$set": {"collab_access_level": access_level}}
        )
        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            "Permission settings",
            "The core collaborative access permissions for the environment have been successfully adjusted",
        )
        return {
            "message": "Cập nhật cấu hình mức độ quyền truy cập cộng tác hoàn tất",
            "collab_access_level": access_level,
        }
