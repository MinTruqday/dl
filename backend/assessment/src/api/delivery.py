from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
from math import log
import json

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.api.common import audit, new_id, now, require_owned
from src.core.auth import CurrentUser, get_current_user, require_author, require_internal_token
from src.core.configuration import settings
from src.core.database import database
from src.core.metrics import metrics as service_metrics
from src.domain.models import (
    AssessmentArchiveInput,
    AssessmentCloneInput,
    AssessmentCreate,
    AssessmentUnpublishInput,
    AssignmentInput,
    AttemptCreate,
    CalibrationJobInput,
    CalibrationRunInput,
    PublishInput,
    ResponseInput,
)
from src.psychometrics.ctt import ctt_snapshot, group_by_question
from src.psychometrics.evidence_filter import classify_evidence, eligible_responses
from src.psychometrics.rasch import estimate_item_parameter
from src.services.blueprint import validate_blueprint
from src.services.delivery_policy import (
    assignment_access,
    attempt_deadline,
    attempt_expired,
    ensure_aware,
    normalize_delivery_policy,
)
from src.services.privacy import participant_id
from src.services.scoring import score_response
from src.services.telemetry import derive_assigned_telemetry
from src.services.validation import validate_question


router = APIRouter(tags=["delivery"])


def stable_order(values: list[dict], seed: str, key: str):
    return sorted(
        [deepcopy(value) for value in values],
        key=lambda value: sha256(f"{seed}:{value.get(key, '')}".encode()).hexdigest(),
    )


def public_question(question: dict, seed: str | None = None):
    projected = {
        key: deepcopy(value)
        for key, value in question.items()
        if key not in {"answer_key", "solution_doc", "plain_text_projection", "owner_id"}
    }
    if seed and isinstance(projected.get("options"), list):
        projected["options"] = stable_order(projected["options"], f"{seed}:{question['_id']}", "id")
    return projected


def ordered_assessment_items(version: dict, assignment: dict | None):
    items = [deepcopy(item) for item in version.get("items", [])]
    if assignment and version.get("delivery_policy", {}).get("shuffle_questions"):
        items = stable_order(items, assignment["_id"], "question_version_id")
    return items


async def activate_scheduled_assessment(assessment: dict):
    if assessment.get("status") != "scheduled":
        return assessment
    version = await database.value.assessment_versions.find_one(
        {"_id": assessment.get("current_version_id")}
    )
    scheduled_for = ensure_aware(version.get("scheduled_for")) if version else None
    if not scheduled_for or scheduled_for > now():
        return assessment
    activated = await database.value.assessments.find_one_and_update(
        {
            "_id": assessment["_id"],
            "status": "scheduled",
            "current_version_id": assessment.get("current_version_id"),
        },
        {"$set": {"status": "published", "updated_at": now()}},
        return_document=ReturnDocument.AFTER,
    )
    if activated:
        await database.value.assessment_versions.update_one(
            {"_id": assessment.get("current_version_id"), "published_at": None},
            {"$set": {"published_at": now()}},
        )
        await audit(
            assessment["owner_id"], "assessment_schedule_activated", "Assessment", assessment["_id"]
        )
    return activated or assessment


async def finalize_attempt_record(attempt: dict, user_id: str, timed_out: bool = False):
    responses = await database.value.responses.find({"attempt_id": attempt["_id"]}).to_list(500)
    total_score = sum(float(response.get("score", 0)) for response in responses)
    pending = sum(1 for response in responses if response.get("score_status") != "final")
    final_status = "timed_out" if timed_out else "completed" if not pending else "submitted"
    completed = await database.value.attempts.find_one_and_update(
        {"_id": attempt["_id"], "student_id": user_id, "status": {"$in": ["active", "paused"]}},
        {
            "$set": {
                "status": final_status,
                "submitted_at": now(),
                "total_score": total_score,
                "pending_scores": pending,
                "updated_at": now(),
            },
            "$unset": {"active_slot": ""},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not completed:
        return await database.value.attempts.find_one({"_id": attempt["_id"]}) or attempt
    await database.value.assignments.update_one(
        {"_id": attempt.get("assignment_id"), "student_id": user_id},
        {
            "$set": {
                "status": "scored" if not pending else "pending_manual_scoring",
                "updated_at": now(),
            }
        },
    )
    await audit(
        user_id,
        "attempt_timed_out" if timed_out else "attempt_submitted",
        "Attempt",
        attempt["_id"],
        {"response_count": len(responses)},
    )
    return completed


@router.post("/assessments", status_code=201)
async def create_assessment(payload: AssessmentCreate, user: CurrentUser = Depends(require_author)):
    draft = await require_owned("assessment_drafts", payload.assessment_draft_id, user)
    try:
        delivery_policy = normalize_delivery_policy(payload.delivery_policy)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    existing = await database.value.assessments.find_one(
        {"owner_id": user.id, "assessment_draft_id": draft["_id"], "status": {"$ne": "archived"}}
    )
    if existing:
        return await database.value.assessments.find_one_and_update(
            {"_id": existing["_id"], "owner_id": user.id},
            {
                "$set": {
                    "delivery_policy": delivery_policy,
                    "title": draft["title"],
                    "updated_at": now(),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
    assessment = {
        "_id": new_id("ASM"),
        "owner_id": user.id,
        "assessment_draft_id": draft["_id"],
        "title": draft["title"],
        "blueprint_id": draft.get("blueprint_id"),
        "status": "draft",
        "current_version_id": None,
        "target_context": draft.get("context", {}),
        "delivery_policy": delivery_policy,
        "created_at": now(),
        "updated_at": now(),
    }
    await database.value.assessments.insert_one(assessment)
    await audit(user.id, "assessment_created", "Assessment", assessment["_id"])
    return assessment


@router.get("/assessments")
async def list_assessments(user: CurrentUser = Depends(require_author)):
    assessments = (
        await database.value.assessments.find({"owner_id": user.id})
        .sort("updated_at", -1)
        .to_list(500)
    )
    return [await activate_scheduled_assessment(assessment) for assessment in assessments]


@router.get("/assessments/{assessment_id}/versions")
async def list_assessment_versions(assessment_id: str, user: CurrentUser = Depends(require_author)):
    await require_owned("assessments", assessment_id, user)
    return (
        await database.value.assessment_versions.find({"assessment_id": assessment_id})
        .sort("version", -1)
        .to_list(100)
    )


@router.get("/assessment-versions/{version_id}")
async def get_assessment_version(version_id: str, user: CurrentUser = Depends(require_author)):
    version = await database.value.assessment_versions.find_one({"_id": version_id})
    if not version:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên bản bài đánh giá")
    if version.get("owner_id") != user.id and not user.is_admin:
        raise HTTPException(
            status_code=403, detail="Không có quyền truy cập phiên bản bài đánh giá"
        )
    return version


@router.get(
    "/assessment-versions/{version_id}/internal/export-snapshot",
    dependencies=[Depends(require_internal_token)],
    include_in_schema=False,
)
async def get_internal_export_snapshot(
    version_id: str, x_actor_id: str = Header(), x_actor_role: str = Header(default="reader")
):
    version = await database.value.assessment_versions.find_one({"_id": version_id})
    if not version:
        raise HTTPException(status_code=404, detail="Không tìm thấy AssessmentVersion")
    if version.get("owner_id") != x_actor_id and x_actor_role.casefold() != "admin":
        raise HTTPException(status_code=403, detail="Không có quyền xuất bài đánh giá")
    question_ids = [item["question_version_id"] for item in version.get("items", [])]
    questions = await database.value.question_versions.find({"_id": {"$in": question_ids}}).to_list(
        1000
    )
    if len(questions) != len(set(question_ids)):
        raise HTTPException(status_code=409, detail={"code": "assessment_snapshot_incomplete"})
    return {"version": version, "questions": questions}


@router.patch("/assessment-versions/{version_id}")
async def reject_assessment_version_mutation(
    version_id: str, payload: dict, user: CurrentUser = Depends(require_author)
):
    await require_owned("assessment_versions", version_id, user)
    await audit(
        user.id,
        "published_assessment_mutation_denied",
        "AssessmentVersion",
        version_id,
        {"fields": sorted(payload)},
    )
    raise HTTPException(status_code=409, detail={"code": "immutable_assessment_version"})


@router.post("/assessments/{assessment_id}/clone", status_code=201)
async def clone_assessment(
    assessment_id: str, payload: AssessmentCloneInput, user: CurrentUser = Depends(require_author)
):
    assessment = await require_owned("assessments", assessment_id, user)
    source_draft = await require_owned("assessment_drafts", assessment["assessment_draft_id"], user)
    source_questions = await database.value.question_drafts.find(
        {"assessment_draft_id": source_draft["_id"], "owner_id": user.id}
    ).to_list(500)
    cloned_draft_id = new_id("ASD")
    question_id_map = {question["_id"]: new_id("QDR") for question in source_questions}
    cloned_draft = deepcopy(source_draft)
    cloned_draft.update(
        {
            "_id": cloned_draft_id,
            "title": payload.title or f"Bản sao {source_draft['title']}",
            "status": "draft",
            "revision": 1,
            "question_order": [
                question_id_map[item]
                for item in source_draft.get("question_order", [])
                if item in question_id_map
            ],
            "blueprint_id": None,
            "published_version_id": None,
            "created_at": now(),
            "updated_at": now(),
        }
    )
    cloned_questions = []
    for source_question in source_questions:
        cloned_question = deepcopy(source_question)
        cloned_question.update(
            {
                "_id": question_id_map[source_question["_id"]],
                "assessment_draft_id": cloned_draft_id,
                "question_id": None,
                "frozen_version_id": None,
                "frozen_revision": None,
                "validity_review": {"status": "pending", "risk_flags": []},
                "cloned_from_question_draft_id": source_question["_id"],
                "status": "draft",
                "revision": 1,
                "created_at": now(),
                "updated_at": now(),
            }
        )
        for key in [
            "validation",
            "reviewed_at",
            "reviewer_note",
            "import_job_id",
            "import_candidate_id",
        ]:
            cloned_question.pop(key, None)
        cloned_questions.append(cloned_question)
    await database.value.assessment_drafts.insert_one(cloned_draft)
    if cloned_questions:
        await database.value.question_drafts.insert_many(cloned_questions)
    await audit(
        user.id,
        "assessment_cloned",
        "AssessmentDraft",
        cloned_draft_id,
        {"source_assessment_id": assessment_id},
    )
    return {**cloned_draft, "questions": cloned_questions}


@router.post("/assessments/{assessment_id}/archive")
async def archive_assessment(
    assessment_id: str, payload: AssessmentArchiveInput, user: CurrentUser = Depends(require_author)
):
    await require_owned("assessments", assessment_id, user)
    updated = await database.value.assessments.find_one_and_update(
        {"_id": assessment_id, "owner_id": user.id},
        {"$set": {"status": "archived", "archived_at": now(), "updated_at": now()}},
        return_document=ReturnDocument.AFTER,
    )
    await audit(
        user.id, "assessment_archived", "Assessment", assessment_id, {"reason": payload.reason}
    )
    return updated


@router.post("/assessments/{assessment_id}/unpublish")
async def unpublish_assessment(
    assessment_id: str,
    payload: AssessmentUnpublishInput,
    user: CurrentUser = Depends(require_author),
):
    assessment = await require_owned("assessments", assessment_id, user)
    if assessment.get("status") not in {"published", "scheduled"}:
        raise HTTPException(
            status_code=409, detail="Bài đánh giá không ở trạng thái có thể hủy xuất bản"
        )
    attempt_ids = await database.value.attempts.distinct(
        "_id", {"assessment_version_id": assessment.get("current_version_id")}
    )
    response_count = (
        await database.value.responses.count_documents({"attempt_id": {"$in": attempt_ids}})
        if attempt_ids
        else 0
    )
    if attempt_ids or response_count:
        raise HTTPException(
            status_code=409, detail={"code": "assessment_has_responses_create_new_version"}
        )
    updated = await database.value.assessments.find_one_and_update(
        {
            "_id": assessment_id,
            "owner_id": user.id,
            "current_version_id": assessment.get("current_version_id"),
        },
        {"$set": {"status": "draft", "updated_at": now()}},
        return_document=ReturnDocument.AFTER,
    )
    await audit(
        user.id, "assessment_unpublished", "Assessment", assessment_id, {"reason": payload.reason}
    )
    return updated


@router.post("/assessments/{assessment_id}/assignments", status_code=201)
async def assign_assessment(
    assessment_id: str, payload: AssignmentInput, user: CurrentUser = Depends(require_author)
):
    assessment = await require_owned("assessments", assessment_id, user)
    assessment = await activate_scheduled_assessment(assessment)
    if assessment.get("status") not in {"published", "scheduled"}:
        raise HTTPException(status_code=409, detail="Chỉ giao bài đã xuất bản")
    version = await database.value.assessment_versions.find_one(
        {"_id": assessment["current_version_id"]}
    )
    scheduled_for = ensure_aware(version.get("scheduled_for")) if version else None
    existing = await database.value.assignment_batches.find_one(
        {"owner_id": user.id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        existing_assignments = await database.value.assignments.find(
            {"_id": {"$in": existing.get("assignment_ids", [])}}
        ).to_list(1000)
        return {**existing, "assignments": existing_assignments}
    assignments = []
    for student_id in sorted(set(payload.student_ids)):
        assignment = {
            "_id": new_id("ASN"),
            "assessment_id": assessment_id,
            "assessment_version_id": assessment["current_version_id"],
            "owner_id": user.id,
            "student_id": student_id,
            "status": "available",
            "available_from": max(
                [value for value in [payload.available_from, scheduled_for] if value is not None],
                default=None,
            ),
            "due_at": payload.due_at,
            "created_at": now(),
        }
        assignment = await database.value.assignments.find_one_and_update(
            {"assessment_version_id": assessment["current_version_id"], "student_id": student_id},
            {"$setOnInsert": assignment},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        assignments.append(assignment)
    batch = {
        "_id": new_id("ASB"),
        "owner_id": user.id,
        "assessment_id": assessment_id,
        "idempotency_key": payload.idempotency_key,
        "assignment_ids": [assignment["_id"] for assignment in assignments],
        "created_at": now(),
    }
    persisted_batch = await database.value.assignment_batches.find_one_and_update(
        {"owner_id": user.id, "idempotency_key": payload.idempotency_key},
        {"$setOnInsert": batch},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    if persisted_batch["_id"] != batch["_id"]:
        persisted_assignments = await database.value.assignments.find(
            {"_id": {"$in": persisted_batch.get("assignment_ids", [])}}
        ).to_list(1000)
        return {**persisted_batch, "assignments": persisted_assignments}
    await audit(
        user.id,
        "assessment_assigned",
        "AssignmentBatch",
        batch["_id"],
        {"student_count": len(assignments)},
    )
    return {**batch, "assignments": assignments}


@router.get("/students/me/assessments")
async def list_student_assessments(user: CurrentUser = Depends(get_current_user)):
    assignments = (
        await database.value.assignments.find({"student_id": user.id})
        .sort("created_at", -1)
        .to_list(1000)
    )
    assessment_ids = list({assignment["assessment_id"] for assignment in assignments})
    assessments = await database.value.assessments.find({"_id": {"$in": assessment_ids}}).to_list(
        1000
    )
    by_id = {assessment["_id"]: assessment for assessment in assessments}
    attempts = (
        await database.value.attempts.find({"student_id": user.id})
        .sort("updated_at", -1)
        .to_list(1000)
    )
    latest_attempt = {}
    for attempt in attempts:
        latest_attempt.setdefault(
            attempt.get("assignment_id") or attempt["assessment_version_id"], attempt
        )
    current_time = now()
    return [
        {
            **assignment,
            "availability_status": assignment_access(assignment, current_time),
            "assessment": by_id.get(assignment["assessment_id"]),
            "attempt": latest_attempt.get(assignment["_id"])
            or latest_attempt.get(assignment["assessment_version_id"]),
        }
        for assignment in assignments
    ]


@router.post("/assessments/{assessment_id}/publish", status_code=201)
async def publish_assessment(
    assessment_id: str, payload: PublishInput, user: CurrentUser = Depends(require_author)
):
    assessment = await require_owned("assessments", assessment_id, user)
    existing = await database.value.assessment_versions.find_one(
        {"assessment_id": assessment_id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        return existing
    draft = await require_owned("assessment_drafts", payload.assessment_draft_id, user)
    if draft["revision"] != payload.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={"code": "revision_conflict", "current_revision": draft["revision"]},
        )
    from src.api.authoring import validate_assessment_draft

    draft_validation = await validate_assessment_draft(draft["_id"], user)
    if not draft_validation["valid"]:
        raise HTTPException(
            status_code=422,
            detail={"code": "assessment_validation_failed", "validation": draft_validation},
        )
    if draft.get("blueprint_id"):
        blueprint = await require_owned("blueprints", draft["blueprint_id"], user)
        result = validate_blueprint(blueprint)
        if not result["valid"]:
            raise HTTPException(
                status_code=422, detail={"code": "blueprint_invalid", "validation": result}
            )
    draft_questions = await database.value.question_drafts.find(
        {"assessment_draft_id": draft["_id"]}
    ).to_list(500)
    questions_by_id = {question["_id"]: question for question in draft_questions}
    if not draft.get("question_order"):
        raise HTTPException(status_code=422, detail="Bài đánh giá chưa có câu hỏi")
    frozen_versions = []
    for position, question_draft_id in enumerate(draft["question_order"], start=1):
        question = questions_by_id.get(question_draft_id)
        if not question:
            raise HTTPException(
                status_code=422,
                detail={"code": "question_order_invalid", "question_draft_id": question_draft_id},
            )
        if validate_question(question)["blockers"]:
            raise HTTPException(
                status_code=422,
                detail={"code": "question_has_blockers", "question_draft_id": question_draft_id},
            )
        if question.get("frozen_revision") != question.get("revision"):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "question_current_revision_not_frozen",
                    "question_draft_id": question_draft_id,
                },
            )
        version_id = question.get("frozen_version_id")
        if not version_id:
            raise HTTPException(
                status_code=422,
                detail={"code": "question_not_frozen", "question_draft_id": question_draft_id},
            )
        version = await database.value.question_versions.find_one(
            {"_id": version_id, "owner_id": user.id}
        )
        if not version:
            raise HTTPException(
                status_code=422,
                detail={"code": "question_version_missing", "question_version_id": version_id},
            )
        if version.get("source_draft_revision") != question.get("revision"):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "question_frozen_revision_mismatch",
                    "question_draft_id": question_draft_id,
                },
            )
        frozen_versions.append(
            {
                "question_version_id": version_id,
                "position": position,
                "points": float(version.get("scoring_rule", {}).get("points", 1)),
            }
        )
    latest = await database.value.assessment_versions.find_one(
        {"assessment_id": assessment_id}, sort=[("version", -1)]
    )
    version_number = 1 if not latest else latest["version"] + 1
    scheduled_for = (
        payload.scheduled_for if payload.scheduled_for and payload.scheduled_for > now() else None
    )
    version = {
        "_id": f"{assessment_id}-v{version_number}",
        "assessment_id": assessment_id,
        "version": version_number,
        "owner_id": user.id,
        "title": draft["title"],
        "context": deepcopy(draft.get("context", {})),
        "layout_doc": deepcopy(draft.get("layout_doc", {})),
        "items": frozen_versions,
        "blueprint_snapshot": deepcopy(blueprint) if draft.get("blueprint_id") else {},
        "delivery_policy": deepcopy(assessment.get("delivery_policy", {})),
        "idempotency_key": payload.idempotency_key,
        "scheduled_for": scheduled_for,
        "published_at": None if scheduled_for else now(),
    }
    try:
        await database.value.assessment_versions.insert_one(version)
    except DuplicateKeyError:
        duplicate = await database.value.assessment_versions.find_one(
            {"assessment_id": assessment_id, "idempotency_key": payload.idempotency_key}
        )
        if duplicate:
            await database.value.assessments.update_one(
                {"_id": assessment_id, "owner_id": user.id},
                {
                    "$set": {
                        "current_version_id": duplicate["_id"],
                        "status": "scheduled" if duplicate.get("scheduled_for") else "published",
                        "updated_at": now(),
                    }
                },
            )
            await database.value.assessment_drafts.update_one(
                {"_id": draft["_id"], "owner_id": user.id},
                {
                    "$set": {
                        "status": "ready",
                        "published_version_id": duplicate["_id"],
                        "updated_at": now(),
                    }
                },
            )
            return duplicate
        raise HTTPException(status_code=409, detail={"code": "assessment_publish_conflict"})
    await database.value.assessments.update_one(
        {"_id": assessment_id, "owner_id": user.id},
        {
            "$set": {
                "current_version_id": version["_id"],
                "status": "scheduled" if scheduled_for else "published",
                "updated_at": now(),
            }
        },
    )
    await database.value.assessment_drafts.update_one(
        {"_id": draft["_id"]},
        {"$set": {"status": "ready", "published_version_id": version["_id"], "updated_at": now()}},
    )
    await audit(user.id, "assessment_published", "AssessmentVersion", version["_id"])
    return version


@router.get("/assessments/{assessment_id}/player")
async def get_assessment_player(
    assessment_id: str,
    assignment_id: str | None = None,
    user: CurrentUser = Depends(get_current_user),
):
    assessment = await database.value.assessments.find_one({"_id": assessment_id})
    if assessment:
        assessment = await activate_scheduled_assessment(assessment)
    if not assessment or assessment.get("status") != "published":
        raise HTTPException(status_code=404, detail="Không tìm thấy bài đánh giá đã xuất bản")
    assignment = None
    version_id = assessment["current_version_id"]
    if assessment.get("owner_id") != user.id and not user.is_admin:
        assignment_query = {"assessment_id": assessment_id, "student_id": user.id}
        if assignment_id:
            assignment_query["_id"] = assignment_id
        assignment = await database.value.assignments.find_one(
            assignment_query, sort=[("created_at", -1)]
        )
        if not assignment:
            raise HTTPException(status_code=403, detail="Bài đánh giá chưa được giao cho người học")
        access = assignment_access(assignment, now())
        if access == "upcoming":
            raise HTTPException(status_code=403, detail={"code": "assessment_not_available_yet"})
        if access == "expired":
            raise HTTPException(status_code=410, detail={"code": "assessment_assignment_expired"})
        version_id = assignment["assessment_version_id"]
    version = await database.value.assessment_versions.find_one({"_id": version_id})
    items = ordered_assessment_items(version, assignment)
    version_ids = [item["question_version_id"] for item in items]
    questions = await database.value.question_versions.find({"_id": {"$in": version_ids}}).to_list(
        500
    )
    by_id = {question["_id"]: question for question in questions}
    return {
        "assessment_id": assessment_id,
        "assessment_version_id": version["_id"],
        "assignment_id": assignment.get("_id") if assignment else None,
        "title": version["title"],
        "layout_doc": version["layout_doc"],
        "delivery_policy": version["delivery_policy"],
        "items": [
            {
                **item,
                "question": public_question(
                    by_id[item["question_version_id"]],
                    assignment["_id"]
                    if assignment and version.get("delivery_policy", {}).get("shuffle_options")
                    else None,
                ),
            }
            for item in items
        ],
    }


@router.post("/assessments/{assessment_id}/attempts", status_code=201)
async def create_attempt(
    assessment_id: str, payload: AttemptCreate, user: CurrentUser = Depends(get_current_user)
):
    assessment = await database.value.assessments.find_one({"_id": assessment_id})
    if assessment:
        assessment = await activate_scheduled_assessment(assessment)
    if not assessment or assessment.get("status") != "published":
        raise HTTPException(status_code=404, detail="Không tìm thấy bài đánh giá đã xuất bản")
    assignment_query = {"assessment_id": assessment_id, "student_id": user.id}
    if payload.assignment_id:
        assignment_query["_id"] = payload.assignment_id
    assignment = await database.value.assignments.find_one(
        assignment_query, sort=[("created_at", -1)]
    )
    if not assignment:
        raise HTTPException(status_code=403, detail="Bài đánh giá chưa được giao cho người học")
    existing = await database.value.attempts.find_one(
        {
            "assignment_id": assignment["_id"],
            "student_id": user.id,
            "idempotency_key": payload.idempotency_key,
        }
    )
    if existing:
        return existing
    version = await database.value.assessment_versions.find_one(
        {"_id": assignment["assessment_version_id"]}
    )
    access = assignment_access(assignment, now())
    if access == "upcoming":
        raise HTTPException(status_code=403, detail={"code": "assessment_not_available_yet"})
    if access == "expired":
        raise HTTPException(status_code=410, detail={"code": "assessment_assignment_expired"})
    active = await database.value.attempts.find_one(
        {
            "assessment_version_id": version["_id"],
            "student_id": user.id,
            "status": {"$in": ["active", "paused"]},
        },
        sort=[("updated_at", -1)],
    )
    if active and not attempt_expired(active, now()):
        return active
    if active:
        await finalize_attempt_record(active, user.id, timed_out=True)
    policy = version.get("delivery_policy", {})
    attempt_limit = int(policy.get("attempt_limit", 1))
    attempt_count = await database.value.attempts.count_documents(
        {"assessment_version_id": version["_id"], "student_id": user.id}
    )
    if attempt_count >= attempt_limit:
        raise HTTPException(status_code=409, detail={"code": "attempt_limit_reached"})
    started_at = now()
    expires_at = attempt_deadline(started_at, policy, assignment)
    attempt = {
        "_id": new_id("ATT"),
        "attempt_id": None,
        "assessment_id": assessment_id,
        "assessment_version_id": version["_id"],
        "assignment_id": assignment["_id"],
        "student_id": user.id,
        "active_slot": f"{assignment['_id']}:{user.id}",
        "attempt_number": attempt_count + 1,
        "delivery_mode": "fixed",
        "status": "active",
        "policy_snapshot": deepcopy(policy),
        "integrity_flags": [],
        "technical_flags": [],
        "item_order": [
            item["question_version_id"] for item in ordered_assessment_items(version, assignment)
        ],
        "option_order": {
            question["_id"]: [
                option["id"]
                for option in stable_order(
                    question.get("options", []), f"{assignment['_id']}:{question['_id']}", "id"
                )
            ]
            for question in await database.value.question_versions.find(
                {"_id": {"$in": [item["question_version_id"] for item in version["items"]]}}
            ).to_list(500)
        }
        if policy.get("shuffle_options")
        else {},
        "idempotency_key": payload.idempotency_key,
        "started_at": started_at,
        "expires_at": expires_at,
        "updated_at": now(),
    }
    attempt["attempt_id"] = attempt["_id"]
    try:
        await database.value.attempts.insert_one(attempt)
    except DuplicateKeyError:
        duplicate = await database.value.attempts.find_one(
            {"active_slot": f"{assignment['_id']}:{user.id}"}
        )
        if not duplicate:
            duplicate = await database.value.attempts.find_one(
                {
                    "assignment_id": assignment["_id"],
                    "student_id": user.id,
                    "idempotency_key": payload.idempotency_key,
                }
            )
        if duplicate:
            return duplicate
        raise HTTPException(status_code=409, detail={"code": "attempt_create_conflict"})
    await database.value.assignments.update_one(
        {"_id": assignment["_id"]},
        {"$set": {"status": "in_progress", "attempt_id": attempt["_id"], "updated_at": now()}},
    )
    await audit(user.id, "attempt_started", "Attempt", attempt["_id"])
    return attempt


@router.get("/attempts/{attempt_id}")
async def get_attempt(attempt_id: str, user: CurrentUser = Depends(get_current_user)):
    attempt = await require_owned("attempts", attempt_id, user)
    responses = (
        await database.value.responses.find({"attempt_id": attempt_id})
        .sort("response_sequence", 1)
        .to_list(500)
    )
    return {**attempt, "responses": responses}


@router.post("/attempts/{attempt_id}/responses")
async def save_response(
    attempt_id: str, payload: ResponseInput, user: CurrentUser = Depends(get_current_user)
):
    attempt = await require_owned("attempts", attempt_id, user)
    if attempt["status"] not in {"active", "paused"}:
        raise HTTPException(status_code=409, detail="Phiên làm bài không còn nhận câu trả lời")
    if attempt_expired(attempt, now()):
        await finalize_attempt_record(attempt, user.id, timed_out=True)
        raise HTTPException(status_code=409, detail={"code": "attempt_time_expired"})
    version = await database.value.assessment_versions.find_one(
        {"_id": attempt["assessment_version_id"]}
    )
    eligible_item_ids = {item["question_version_id"] for item in version["items"]}
    if payload.question_version_id not in eligible_item_ids:
        raise HTTPException(status_code=422, detail="Câu hỏi không thuộc phiên bản bài đánh giá")
    existing = await database.value.responses.find_one(
        {"attempt_id": attempt_id, "question_version_id": payload.question_version_id}
    )
    if existing and existing.get("idempotency_key") == payload.idempotency_key:
        if existing.get("answer") != payload.answer:
            raise HTTPException(
                status_code=409, detail={"code": "response_idempotency_payload_conflict"}
            )
        return existing
    if existing and int(existing.get("client_revision", 1)) >= payload.client_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "stale_response_revision",
                "current_revision": existing.get("client_revision", 1),
            },
        )
    question = await database.value.question_versions.find_one({"_id": payload.question_version_id})
    is_correct, score, score_status = score_response(question, payload.answer)
    response_participant_id = participant_id(user.id)
    prior_attempt_ids = await database.value.responses.distinct(
        "attempt_id",
        {
            "participant_id": response_participant_id,
            "question_version_id": payload.question_version_id,
            "attempt_id": {"$ne": attempt_id},
        },
    )
    exposure_index = (
        int(existing.get("exposure_index", 1)) if existing else len(prior_attempt_ids) + 1
    )
    item_order = attempt.get("item_order") or [
        item["question_version_id"] for item in version["items"]
    ]
    if payload.question_version_id not in item_order:
        item_order = [item["question_version_id"] for item in version["items"]]
    response_sequence = item_order.index(payload.question_version_id) + 1
    captured_at = now()
    telemetry = derive_assigned_telemetry(payload.model_dump(), attempt["started_at"], captured_at)
    response_data = payload.model_dump()
    response_data.update(
        {
            "participant_id": response_participant_id,
            "assessment_version_id": attempt["assessment_version_id"],
            "delivery_context": "assigned",
            "response_sequence": response_sequence,
            "client_revision": payload.client_revision,
            "is_first_exposure": exposure_index == 1,
            "exposure_index": exposure_index,
            "hint_used": False,
            "explanation_seen_before_answer": False,
            **telemetry,
            "is_correct": is_correct,
            "score": score,
            "max_score": float(question.get("scoring_rule", {}).get("points", 1)),
            "score_status": score_status,
            "submitted_at": captured_at,
            "updated_at": captured_at,
        }
    )
    response_data.pop("answer_change_count", None)
    response_data["evidence_eligibility"] = classify_evidence(response_data)
    response_id = existing.get("_id") if existing else new_id("RSP")
    persisted_at = now()
    update_fields = {
        "_id": {"$ifNull": ["$_id", {"$literal": response_id}]},
        "response_id": {"$ifNull": ["$response_id", {"$literal": response_id}]},
        "attempt_id": {"$literal": attempt_id},
        "created_at": {"$ifNull": ["$created_at", {"$literal": persisted_at}]},
        "answer_change_count": {
            "$cond": [
                {
                    "$and": [
                        {"$ne": [{"$type": "$created_at"}, "missing"]},
                        {"$ne": ["$idempotency_key", {"$literal": payload.idempotency_key}]},
                        {"$ne": ["$answer", {"$literal": payload.answer}]},
                    ]
                },
                {"$add": [{"$ifNull": ["$answer_change_count", 0]}, 1]},
                {"$ifNull": ["$answer_change_count", 0]},
            ]
        },
        **{key: {"$literal": value} for key, value in response_data.items()},
    }
    try:
        response = await database.value.responses.find_one_and_update(
            {
                "attempt_id": attempt_id,
                "question_version_id": payload.question_version_id,
                "$or": [
                    {"client_revision": {"$exists": False}},
                    {"client_revision": {"$lt": payload.client_revision}},
                ],
            },
            [{"$set": update_fields}],
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        current = await database.value.responses.find_one(
            {"attempt_id": attempt_id, "question_version_id": payload.question_version_id}
        )
        if (
            current
            and current.get("idempotency_key") == payload.idempotency_key
            and current.get("answer") == payload.answer
        ):
            return current
        raise HTTPException(
            status_code=409,
            detail={
                "code": "stale_response_revision",
                "current_revision": current.get("client_revision", 1) if current else None,
            },
        )
    action = "response_autosaved" if existing else "response_recorded"
    await database.value.attempts.update_one({"_id": attempt_id}, {"$set": {"updated_at": now()}})
    await audit(user.id, action, "Response", response["_id"], {"attempt_id": attempt_id})
    return response


@router.post("/attempts/{attempt_id}/submit")
async def submit_attempt(attempt_id: str, user: CurrentUser = Depends(get_current_user)):
    attempt = await require_owned("attempts", attempt_id, user)
    if attempt["status"] in {"submitted", "completed", "timed_out"}:
        return attempt
    if attempt["status"] not in {"active", "paused"}:
        raise HTTPException(status_code=409, detail="Trạng thái phiên làm bài không hợp lệ")
    return await finalize_attempt_record(
        attempt, user.id, timed_out=attempt_expired(attempt, now())
    )


@router.get("/attempts/{attempt_id}/result")
async def get_attempt_result(attempt_id: str, user: CurrentUser = Depends(get_current_user)):
    attempt = await require_owned("attempts", attempt_id, user)
    if attempt["status"] not in {"submitted", "completed", "timed_out"}:
        raise HTTPException(status_code=409, detail="Phiên làm bài chưa hoàn tất")
    responses = (
        await database.value.responses.find({"attempt_id": attempt_id})
        .sort("response_sequence", 1)
        .to_list(500)
    )
    version = await database.value.assessment_versions.find_one(
        {"_id": attempt["assessment_version_id"]}
    )
    review_answers = bool(version.get("delivery_policy", {}).get("review_answers", False))
    question_ids = [response["question_version_id"] for response in responses]
    questions = (
        await database.value.question_versions.find({"_id": {"$in": question_ids}}).to_list(500)
        if review_answers
        else []
    )
    questions_by_id = {question["_id"]: question for question in questions}
    return {
        "attempt_id": attempt_id,
        "status": attempt["status"],
        "total_score": attempt.get("total_score", 0),
        "total_possible_score": sum(
            float(item.get("points", 1)) for item in version.get("items", [])
        ),
        "pending_scores": attempt.get("pending_scores", 0),
        "review_answers": review_answers,
        "responses": [
            {
                "question_version_id": response["question_version_id"],
                "is_correct": response.get("is_correct") if review_answers else None,
                "score": response.get("score") if review_answers else None,
                "score_status": response.get("score_status"),
                "evidence_eligibility": response.get("evidence_eligibility"),
                "submitted_answer": response.get("answer") if review_answers else None,
                "answer_key": questions_by_id.get(response["question_version_id"], {}).get(
                    "answer_key"
                )
                if review_answers
                else None,
                "stem_doc": questions_by_id.get(response["question_version_id"], {}).get(
                    "stem_doc"
                )
                if review_answers
                else None,
                "solution_doc": questions_by_id.get(response["question_version_id"], {}).get(
                    "solution_doc"
                )
                if review_answers
                else None,
            }
            for response in responses
        ],
    }


@router.post("/calibration/run", status_code=201)
async def run_calibration(
    payload: CalibrationRunInput, user: CurrentUser = Depends(require_author)
):
    if payload.idempotency_key:
        existing = await database.value.calibration_runs.find_one(
            {"owner_id": user.id, "idempotency_key": payload.idempotency_key}
        )
        if existing:
            snapshots = await database.value.calibrations.find({"run_id": existing["_id"]}).to_list(
                1000
            )
            return {**existing, "snapshots": snapshots}
    version_query = {"owner_id": user.id}
    if payload.question_version_ids:
        version_query["_id"] = {"$in": payload.question_version_ids}
    versions = await database.value.question_versions.find(version_query).to_list(1000)
    version_ids = [version["_id"] for version in versions]
    responses = await database.value.responses.find(
        {"question_version_id": {"$in": version_ids}}
    ).to_list(100000)
    clean = eligible_responses(responses)
    all_grouped = group_by_question(responses)
    totals = defaultdict(float)
    all_totals = defaultdict(float)
    for response in clean:
        totals[response["attempt_id"]] += float(response.get("score", 0))
    for response in responses:
        all_totals[response["attempt_id"]] += float(response.get("score", 0))
    grouped = group_by_question(clean)
    attempt_correct = defaultdict(int)
    attempt_total = defaultdict(int)
    binary_clean = [
        response
        for response in clean
        if float(response.get("score", 0)) in {0.0, float(response.get("max_score", 1))}
    ]
    for response in binary_clean:
        attempt_total[response["attempt_id"]] += 1
        attempt_correct[response["attempt_id"]] += int(bool(response.get("is_correct")))
    versions_by_id = {version["_id"]: version for version in versions}
    run = {
        "_id": new_id("CRN"),
        "owner_id": user.id,
        "method": payload.method,
        "idempotency_key": payload.idempotency_key,
        "population_context": payload.population_context,
        "evidence_policy_version": payload.evidence_policy_version,
        "eligible_response_count": len(clean),
        "total_response_count": len(responses),
        "created_at": now(),
    }
    try:
        await database.value.calibration_runs.insert_one(run)
    except DuplicateKeyError:
        if not payload.idempotency_key:
            raise
        duplicate = await database.value.calibration_runs.find_one(
            {"owner_id": user.id, "idempotency_key": payload.idempotency_key}
        )
        snapshots = await database.value.calibrations.find({"run_id": duplicate["_id"]}).to_list(
            1000
        )
        return {**duplicate, "snapshots": snapshots}
    snapshots = []
    for version_id in version_ids:
        item_responses = grouped.get(version_id, [])
        if len(item_responses) < settings.CALIBRATION_MIN_SAMPLE_SIZE:
            snapshot = {
                "_id": new_id("CAL"),
                "question_version_id": version_id,
                "run_id": run["_id"],
                "owner_id": user.id,
                "method": payload.method,
                "status": "insufficient_evidence",
                "sample_size": len(item_responses),
                "total_response_count": len(all_grouped.get(version_id, [])),
                "excluded_response_count": len(all_grouped.get(version_id, []))
                - len(item_responses),
                "minimum_sample_size": settings.CALIBRATION_MIN_SAMPLE_SIZE,
                "population_context": payload.population_context,
                "evidence_policy_version": payload.evidence_policy_version,
                "created_at": now(),
            }
            await database.value.calibrations.insert_one(snapshot)
            snapshots.append(snapshot)
            await audit(
                user.id,
                "item_calibration_insufficient",
                "ItemCalibration",
                snapshot["_id"],
                {"question_version_id": version_id},
            )
            continue
        if payload.method == "Rasch":
            partial_responses = [
                response
                for response in item_responses
                if float(response.get("score", 0)) not in {0.0, float(response.get("max_score", 1))}
            ]
            if partial_responses:
                snapshot = {
                    "_id": new_id("CAL"),
                    "question_version_id": version_id,
                    "run_id": run["_id"],
                    "owner_id": user.id,
                    "method": "Rasch",
                    "status": "unsupported_response_scale",
                    "sample_size": len(item_responses),
                    "total_response_count": len(all_grouped.get(version_id, [])),
                    "excluded_response_count": len(all_grouped.get(version_id, []))
                    - len(item_responses),
                    "population_context": payload.population_context,
                    "evidence_policy_version": payload.evidence_policy_version,
                    "created_at": now(),
                }
                await database.value.calibrations.insert_one(snapshot)
                snapshots.append(snapshot)
                await audit(
                    user.id,
                    "item_calibration_unsupported",
                    "ItemCalibration",
                    snapshot["_id"],
                    {"question_version_id": version_id},
                )
                continue
            ordered_responses = sorted(
                item_responses, key=lambda response: str(response["attempt_id"])
            )
            metrics = estimate_item_parameter(
                sum(1 for response in ordered_responses if response.get("is_correct")),
                len(ordered_responses),
                [
                    log(
                        (
                            attempt_correct[response["attempt_id"]]
                            - int(bool(response.get("is_correct")))
                            + 0.5
                        )
                        / (
                            attempt_total[response["attempt_id"]]
                            - 1
                            - attempt_correct[response["attempt_id"]]
                            + int(bool(response.get("is_correct")))
                            + 0.5
                        )
                    )
                    for response in ordered_responses
                ],
                [1.0 if response.get("is_correct") else 0.0 for response in ordered_responses],
            )
        else:
            version = versions_by_id[version_id]
            answer_key = version.get("answer_key", {})
            correct_option_ids = (
                [answer_key["option_id"]]
                if answer_key.get("option_id")
                else answer_key.get("option_ids", [])
            )
            metrics = ctt_snapshot(
                item_responses,
                totals,
                [option.get("id") for option in version.get("options", [])],
                correct_option_ids,
            )
        snapshot = {
            "_id": new_id("CAL"),
            "question_version_id": version_id,
            "run_id": run["_id"],
            "owner_id": user.id,
            "method": payload.method,
            **metrics,
            "population_context": payload.population_context,
            "evidence_policy_version": payload.evidence_policy_version,
            "total_response_count": len(all_grouped.get(version_id, [])),
            "excluded_response_count": len(all_grouped.get(version_id, [])) - len(item_responses),
            "status": "calibrated",
            "created_at": now(),
        }
        if payload.method == "CTT" and all_grouped.get(version_id):
            version = versions_by_id[version_id]
            answer_key = version.get("answer_key", {})
            all_correct_option_ids = (
                [answer_key["option_id"]]
                if answer_key.get("option_id")
                else answer_key.get("option_ids", [])
            )
            unfiltered = ctt_snapshot(
                all_grouped[version_id],
                all_totals,
                [option.get("id") for option in version.get("options", [])],
                all_correct_option_ids,
            )
            snapshot["unfiltered_difficulty"] = unfiltered.get("difficulty")
            snapshot["contamination_filter_difficulty_delta"] = (
                abs(float(unfiltered["difficulty"]) - float(snapshot["difficulty"]))
                if unfiltered.get("difficulty") is not None
                and snapshot.get("difficulty") is not None
                else None
            )
        previous = await database.value.calibrations.find_one(
            {"question_version_id": version_id, "status": "calibrated"}, sort=[("created_at", -1)]
        )
        snapshot["drift_from_snapshot_id"] = previous.get("_id") if previous else None
        snapshot["drift_delta"] = (
            abs(float(previous["difficulty"]) - float(snapshot["difficulty"]))
            if previous
            and previous.get("difficulty") is not None
            and snapshot.get("difficulty") is not None
            else None
        )
        snapshot["drift_flag"] = bool(
            snapshot["drift_delta"] is not None and snapshot["drift_delta"] >= 0.75
        )
        await database.value.calibrations.insert_one(snapshot)
        snapshots.append(snapshot)
        await audit(
            user.id,
            "item_calibrated",
            "ItemCalibration",
            snapshot["_id"],
            {"question_version_id": version_id},
        )
    calibrated_snapshots = [
        snapshot for snapshot in snapshots if snapshot.get("status") == "calibrated"
    ]
    service_metrics.set(
        "calibration_valid_n",
        sum(int(snapshot.get("sample_size", 0)) for snapshot in calibrated_snapshots),
    )
    service_metrics.set(
        "calibration_failure_rate",
        (len(snapshots) - len(calibrated_snapshots)) / len(snapshots) if snapshots else 0,
    )
    rasch_snapshots = [snapshot for snapshot in snapshots if snapshot.get("method") == "Rasch"]
    service_metrics.set(
        "irt_fit_failure_rate",
        sum(1 for snapshot in rasch_snapshots if snapshot.get("status") != "calibrated")
        / len(rasch_snapshots)
        if rasch_snapshots
        else 0,
    )
    prediction_errors = []
    for snapshot in calibrated_snapshots:
        estimate = await database.value.difficulty_estimates.find_one(
            {"question_version_id": snapshot["question_version_id"]}, sort=[("created_at", -1)]
        )
        if (
            estimate
            and estimate.get("predicted_difficulty") is not None
            and snapshot.get("difficulty") is not None
        ):
            prediction_errors.append(
                abs(float(estimate["predicted_difficulty"]) - float(snapshot["difficulty"]))
            )
    if prediction_errors:
        service_metrics.set(
            "difficulty_prediction_mae", sum(prediction_errors) / len(prediction_errors)
        )
    return {**run, "snapshots": snapshots}


@router.post("/calibration/jobs", status_code=202)
async def enqueue_calibration(
    payload: CalibrationJobInput, user: CurrentUser = Depends(require_author)
):
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            f"{settings.WORKER_URL}/worker/internal/assessment/calibration",
            headers={"X-Internal-Token": settings.SECRET_KEY},
            json={
                "owner_id": user.id,
                "owner_email": user.email,
                "payload": payload.model_dump(mode="json"),
            },
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=503, detail="Không thể đưa hiệu chỉnh vào hàng đợi")
    return response.json()


@router.get("/calibration/jobs/{job_id}")
async def get_calibration_job(job_id: str, user: CurrentUser = Depends(require_author)):
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            f"{settings.WORKER_URL}/worker/internal/jobs/{job_id}",
            headers={"X-Internal-Token": settings.SECRET_KEY},
        )
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Không tìm thấy calibration job")
    if response.status_code >= 400:
        raise HTTPException(status_code=503, detail="Không thể đọc calibration job")
    job = response.json()
    if job.get("owner_id") != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Không có quyền đọc calibration job")
    return job


@router.post(
    "/internal/calibration/run",
    dependencies=[Depends(require_internal_token)],
    include_in_schema=False,
)
async def run_internal_calibration(
    payload: CalibrationRunInput, x_owner_id: str = Header(), x_owner_email: str = Header()
):
    return await run_calibration(
        payload, CurrentUser(_id=x_owner_id, email=x_owner_email, role="author")
    )


@router.get("/questions/{version_id}/calibration")
async def get_calibration(version_id: str, user: CurrentUser = Depends(require_author)):
    version = await require_owned("question_versions", version_id, user)
    return (
        await database.value.calibrations.find({"question_version_id": version["_id"]})
        .sort("created_at", -1)
        .to_list(100)
    )


@router.get("/questions/{version_id}/difficulty-signals")
async def get_difficulty_signals(version_id: str, user: CurrentUser = Depends(require_author)):
    version = await require_owned("question_versions", version_id, user)
    target = await database.value.difficulty_targets.find_one(
        {"question_version_id": version_id}, sort=[("created_at", -1)]
    )
    judgment = await database.value.teacher_judgments.find_one(
        {"question_version_id": version_id}, sort=[("created_at", -1)]
    )
    prediction = await database.value.difficulty_estimates.find_one(
        {
            "question_version_id": version_id,
            "$or": [{"predictor_kind": "structured"}, {"predictor_kind": {"$exists": False}}],
        },
        sort=[("created_at", -1)],
    )
    direct_prediction = await database.value.difficulty_estimates.find_one(
        {"question_version_id": version_id, "predictor_kind": "llm_direct"},
        sort=[("created_at", -1)],
    )
    calibration = await database.value.calibrations.find_one(
        {"question_version_id": version_id}, sort=[("created_at", -1)]
    )
    return {
        "question_id": version.get("question_id"),
        "version": version.get("version"),
        "target": target.get("target_difficulty") if target else None,
        "teacher_estimate": judgment.get("estimated_difficulty") if judgment else None,
        "teacher_estimate_research_eligible": judgment.get("research_eligible")
        if judgment
        else None,
        "ai_prediction": prediction.get("predicted_difficulty") if prediction else None,
        "ai_confidence": prediction.get("confidence") if prediction else None,
        "llm_direct_prediction": direct_prediction.get("predicted_difficulty")
        if direct_prediction
        else None,
        "llm_direct_confidence": direct_prediction.get("confidence") if direct_prediction else None,
        "empirical": calibration.get("difficulty") if calibration else None,
        "sample_size": calibration.get("sample_size") if calibration else 0,
        "calibration_context": calibration.get("population_context") if calibration else None,
        "calibration_standard_error": calibration.get("standard_error") if calibration else None,
        "prediction_empirical_gap": abs(
            prediction["predicted_difficulty"] - calibration["difficulty"]
        )
        if prediction
        and calibration
        and prediction.get("predicted_difficulty") is not None
        and calibration.get("difficulty") is not None
        else None,
        "drift_flag": calibration.get("drift_flag") if calibration else None,
        "drift_delta": calibration.get("drift_delta") if calibration else None,
        "item_fit_status": calibration.get("item_fit_status") if calibration else None,
    }


@router.get("/assessments/{assessment_id}/difficulty-comparison")
async def get_difficulty_comparison(
    assessment_id: str, user: CurrentUser = Depends(require_author)
):
    assessment = await require_owned("assessments", assessment_id, user)
    versions = (
        await database.value.assessment_versions.find({"assessment_id": assessment["_id"]})
        .sort("version", 1)
        .to_list(100)
    )
    question_version_ids = [
        item["question_version_id"] for version in versions for item in version["items"]
    ]
    rows = []
    for version_id in question_version_ids:
        rows.append(
            {"question_version_id": version_id, **await get_difficulty_signals(version_id, user)}
        )
    return {
        "assessment_id": assessment_id,
        "assessment_versions": [version["_id"] for version in versions],
        "items": rows,
    }


@router.get("/questions/{question_id}/research-metrics")
async def get_research_metrics(question_id: str, user: CurrentUser = Depends(require_author)):
    question = await require_owned("questions", question_id, user)
    versions = (
        await database.value.question_versions.find({"question_id": question["_id"]})
        .sort("version", 1)
        .to_list(100)
    )
    rows = []
    for version in versions:
        prediction = await database.value.difficulty_estimates.find_one(
            {
                "question_version_id": version["_id"],
                "$or": [{"predictor_kind": "structured"}, {"predictor_kind": {"$exists": False}}],
            },
            sort=[("created_at", -1)],
        )
        teacher = await database.value.teacher_judgments.find_one(
            {"question_version_id": version["_id"]}, sort=[("created_at", -1)]
        )
        empirical = await database.value.calibrations.find_one(
            {"question_version_id": version["_id"], "status": "calibrated"},
            sort=[("created_at", -1)],
        )
        empirical_value = empirical.get("difficulty") if empirical else None
        ai_value = prediction.get("predicted_difficulty") if prediction else None
        teacher_value = teacher.get("estimated_difficulty") if teacher else None
        rows.append(
            {
                "question_version_id": version["_id"],
                "version": version["version"],
                "ai_error": abs(ai_value - empirical_value)
                if ai_value is not None and empirical_value is not None
                else None,
                "teacher_error": abs(teacher_value - empirical_value)
                if teacher_value is not None and empirical_value is not None
                else None,
                "sample_size": empirical.get("sample_size", 0) if empirical else 0,
                "population_context": empirical.get("population_context") if empirical else None,
            }
        )
    first = rows[0] if rows else None
    latest = rows[-1] if rows else None
    return {
        "question_id": question_id,
        "versions": rows,
        "error_v1": first.get("ai_error") if first else None,
        "error_v2": latest.get("ai_error") if latest and latest.get("version", 0) >= 2 else None,
        "error_reduction": first["ai_error"] - latest["ai_error"]
        if first
        and latest
        and first.get("ai_error") is not None
        and latest.get("ai_error") is not None
        else None,
    }


@router.get("/assessments/{assessment_id}/analytics")
async def get_assessment_analytics(assessment_id: str, user: CurrentUser = Depends(require_author)):
    assessment = await require_owned("assessments", assessment_id, user)
    version_ids = await database.value.assessment_versions.distinct(
        "_id", {"assessment_id": assessment_id}
    )
    attempts = await database.value.attempts.find(
        {"assessment_version_id": {"$in": version_ids}}
    ).to_list(100000)
    responses = await database.value.responses.find(
        {"attempt_id": {"$in": [attempt["_id"] for attempt in attempts]}}
    ).to_list(100000)
    completed = [attempt for attempt in attempts if attempt["status"] == "completed"]
    score_values = [float(attempt.get("total_score", 0)) for attempt in completed]
    question_ids = list({response["question_version_id"] for response in responses})
    question_versions = await database.value.question_versions.find(
        {"_id": {"$in": question_ids}, "owner_id": user.id}
    ).to_list(1000)
    versions_by_id = {version["_id"]: version for version in question_versions}
    responses_by_question = defaultdict(list)
    for response in responses:
        responses_by_question[response["question_version_id"]].append(response)
    completion_seconds = []
    for attempt in completed:
        started_at = attempt.get("started_at")
        submitted_at = attempt.get("submitted_at")
        if started_at and submitted_at:
            completion_seconds.append(max(0, (submitted_at - started_at).total_seconds()))
    score_distribution = defaultdict(int)
    for value in score_values:
        score_distribution[str(round(value, 3))] += 1
    topic_totals = defaultdict(
        lambda: {"responses": 0, "correct": 0, "score": 0.0, "max_score": 0.0}
    )
    rows = []
    for question_id in question_ids:
        question_version = versions_by_id.get(question_id, {})
        item_responses = responses_by_question[question_id]
        target = await database.value.difficulty_targets.find_one(
            {"question_version_id": question_id}, sort=[("created_at", -1)]
        )
        teacher = await database.value.teacher_judgments.find_one(
            {"question_version_id": question_id}, sort=[("created_at", -1)]
        )
        prediction = await database.value.difficulty_estimates.find_one(
            {
                "question_version_id": question_id,
                "$or": [{"predictor_kind": "structured"}, {"predictor_kind": {"$exists": False}}],
            },
            sort=[("created_at", -1)],
        )
        direct_prediction = await database.value.difficulty_estimates.find_one(
            {"question_version_id": question_id, "predictor_kind": "llm_direct"},
            sort=[("created_at", -1)],
        )
        empirical = await database.value.calibrations.find_one(
            {"question_version_id": question_id}, sort=[("created_at", -1)]
        )
        answer_distribution = defaultdict(int)
        response_times = []
        answer_changes = []
        for response in item_responses:
            answer_distribution[
                json.dumps(response.get("answer"), ensure_ascii=False, sort_keys=True)
            ] += 1
            if isinstance(response.get("response_time_ms"), (int, float)):
                response_times.append(float(response["response_time_ms"]))
            answer_changes.append(int(response.get("answer_change_count", 0)))
            curriculum = (question_version.get("curriculum_links") or [{}])[0]
            topic = str(
                curriculum.get("topic")
                or curriculum.get("lesson")
                or curriculum.get("chapter")
                or curriculum.get("subject")
                or "unmapped"
            )
            topic_totals[topic]["responses"] += 1
            topic_totals[topic]["correct"] += int(bool(response.get("is_correct")))
            topic_totals[topic]["score"] += float(response.get("score", 0))
            topic_totals[topic]["max_score"] += float(response.get("max_score", 1))
        prediction_error = (
            abs(float(prediction["predicted_difficulty"]) - float(empirical["difficulty"]))
            if prediction
            and empirical
            and prediction.get("predicted_difficulty") is not None
            and empirical.get("difficulty") is not None
            else None
        )
        anomaly_flags = []
        if empirical and empirical.get("drift_flag"):
            anomaly_flags.append("difficulty_drift")
        if empirical and empirical.get("status") == "insufficient_evidence":
            anomaly_flags.append("insufficient_evidence")
        if (
            empirical
            and isinstance(empirical.get("discrimination"), (int, float))
            and empirical["discrimination"] < 0
        ):
            anomaly_flags.append("negative_discrimination")
        if prediction_error is not None and prediction_error >= 1:
            anomaly_flags.append("large_prediction_error")
        rows.append(
            {
                "question_version_id": question_id,
                "question_id": question_version.get("question_id"),
                "version": question_version.get("version"),
                "target": target.get("target_difficulty") if target else None,
                "teacher_estimate": teacher.get("estimated_difficulty") if teacher else None,
                "ai_prediction": prediction.get("predicted_difficulty") if prediction else None,
                "llm_direct_prediction": direct_prediction.get("predicted_difficulty")
                if direct_prediction
                else None,
                "empirical": empirical.get("difficulty") if empirical else None,
                "sample_size": empirical.get("sample_size") if empirical else 0,
                "discrimination": empirical.get("discrimination") if empirical else None,
                "distractor_distribution": dict(answer_distribution),
                "omission_count": max(0, len(completed) - len(item_responses)),
                "average_response_time_ms": round(sum(response_times) / len(response_times), 3)
                if response_times
                else None,
                "average_answer_changes": round(sum(answer_changes) / len(answer_changes), 3)
                if answer_changes
                else 0,
                "item_fit_status": empirical.get("item_fit_status") if empirical else None,
                "exposure_count": len(item_responses),
                "anomaly_flags": anomaly_flags,
                "prediction_error": round(prediction_error, 3)
                if prediction_error is not None
                else None,
            }
        )
    return {
        "assessment_id": assessment_id,
        "attempts": len(attempts),
        "completed": len(completed),
        "completion_rate": len(completed) / len(attempts) if attempts else 0,
        "average_score": sum(score_values) / len(score_values) if score_values else None,
        "score_distribution": dict(
            sorted(score_distribution.items(), key=lambda item: float(item[0]))
        ),
        "average_completion_seconds": round(sum(completion_seconds) / len(completion_seconds), 3)
        if completion_seconds
        else None,
        "topic_performance": [
            {
                "topic": topic,
                **values,
                "accuracy": round(values["correct"] / values["responses"], 4)
                if values["responses"]
                else None,
                "score_rate": round(values["score"] / values["max_score"], 4)
                if values["max_score"]
                else None,
            }
            for topic, values in sorted(topic_totals.items())
        ],
        "difficulty_comparison": rows,
        "item_analysis": rows,
    }
