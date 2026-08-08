import asyncio
import os
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.services.collaboration import CollaborationService
from src.services.document import DocumentService
from src.repositories.document import DocumentRepository
from src.repositories.collaboration import CollaborationRepository
from src.schemas.document import DocumentContentUpdate


class MockUser:
    def __init__(self, user_id, email, full_name, role="author"):
        self.id = user_id
        self.email = email
        self.full_name = full_name
        self.role = role


async def run_e2e_tests():
    database.mongodb = AsyncIOMotorClient(settings.MONGODB_URI)
    owner = MockUser(str(uuid.uuid4()), "owner@doclib.vn", "Doc Owner")
    editor = MockUser(str(uuid.uuid4()), "editor@doclib.vn", "Doc Editor")
    doc_id = str(uuid.uuid4())
    humanity = database.mongodb[os.environ["HUMANITY_DB_NAME"]]
    content = database.mongodb[settings.CONTENT_DB_NAME]
    await humanity.users.insert_many(
        [
            {
                "_id": owner.id,
                "email": owner.email,
                "full_name": owner.full_name,
                "role": owner.role,
                "is_active": True,
            },
            {
                "_id": editor.id,
                "email": editor.email,
                "full_name": editor.full_name,
                "role": editor.role,
                "is_active": True,
            },
        ]
    )

    await DocumentRepository.insert_one(
        {
            "_id": doc_id,
            "title": "Tai lieu hen gio dong mo",
            "slug": f"tai-lieu-hen-gio-{doc_id}",
            "creator_id": owner.id,
            "coauthors": [editor.id],
            "content": "Noi dung goc",
            "status": "PUBLISHED",
            "collaboration_mode": "OPEN",
            "collaboration_schedules": [],
        }
    )
    await CollaborationRepository.insert_invite(
        {
            "_id": str(uuid.uuid4()),
            "document_id": doc_id,
            "invitee_id": editor.id,
            "role": "editor",
            "status": "ACCEPTED",
        }
    )

    res = await CollaborationService.update_collaboration_mode(
        doc_id, "READ_ONLY", owner
    )
    assert res["collaboration_mode"] == "READ_ONLY"

    mode_info = await CollaborationService.get_collaboration_mode(
        doc_id, editor
    )
    assert mode_info["collaboration_mode"] == "READ_ONLY"
    assert mode_info["effective_status"]["can_edit"] is False
    assert mode_info["effective_status"]["can_view"] is True

    try:
        await DocumentService.update_document_content(
            doc_id,
            DocumentContentUpdate(
                content="Sua lenh", content_format="markdown"
            ),
            editor,
        )
        assert False, "Expected 403 Forbidden"
    except HTTPException as e:
        assert e.status_code == 403

    await DocumentService.update_document_content(
        doc_id,
        DocumentContentUpdate(
            content="Chu so huu sua", content_format="markdown"
        ),
        owner,
    )

    await CollaborationService.update_collaboration_mode(
        doc_id, "CLOSED", owner
    )
    closed_info = await CollaborationService.get_collaboration_mode(
        doc_id, editor
    )
    assert closed_info["effective_status"]["is_effective_closed"] is True
    assert closed_info["effective_status"]["can_view"] is False

    try:
        await DocumentService.get_document_by_id(doc_id, current_user=editor)
        assert False, "Expected 403 Forbidden"
    except HTTPException as e:
        assert e.status_code == 403

    now = datetime.now(timezone.utc)
    schedules = [
        {
            "title": "Khung gio dac biet",
            "start_at": (now - timedelta(minutes=10)).isoformat(),
            "end_at": (now + timedelta(minutes=50)).isoformat(),
            "mode": "EDIT",
            "fallback_mode": "READ_ONLY",
            "is_active": True,
        }
    ]
    await CollaborationService.update_collaboration_schedules(
        doc_id, schedules, owner
    )
    sched_info = await CollaborationService.get_collaboration_schedules(
        doc_id, editor
    )
    assert len(sched_info["schedules"]) == 1
    assert sched_info["effective_status"]["can_edit"] is True

    await DocumentService.update_document_content(
        doc_id,
        DocumentContentUpdate(
            content="Sua trong khung gio", content_format="markdown"
        ),
        editor,
    )

    await content.documents.delete_one({"_id": doc_id})
    await content.collaboration_invites.delete_many({"document_id": doc_id})
    await content.collaboration_activities.delete_many({"document_id": doc_id})
    await content.collaboration_locks.delete_many({"document_id": doc_id})
    await humanity.users.delete_many({"_id": {"$in": [owner.id, editor.id]}})

    print("ALL E2E INTEGRATION TESTS PASSED PERFECTLY")


if __name__ == "__main__":
    asyncio.run(run_e2e_tests())
