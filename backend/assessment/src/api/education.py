import hashlib
import json

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.api.common import audit, new_id, now
from src.core.auth import CurrentUser, Role, get_current_user, require_admin, require_author, require_internal_token
from src.core.database import database
from src.core.metrics import metrics
from src.core.configuration import settings
from src.domain.models import CurriculumMergeInput, CurriculumNodeInput, CurriculumNodePatch, CurriculumSplitInput, EducationProfileInput, SourceMappingInput, SourceMappingReviewInput, SourceObsoleteInput, TeacherProfileEventInput, TeacherProfileInput, UserSettingsInput
from src.services.teacher_profile import persist_teacher_profile_event


router = APIRouter(prefix="/education", tags=["education"])


async def require_owned_teacher_material(document_id: str, user: CurrentUser):
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{settings.CONTENT_URL}/tai-lieu/noi-bo/truy-cap",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                json={
                    "document_id": document_id,
                    "user_id": user.id,
                    "edit": True,
                    "is_admin": user.is_admin,
                },
            )
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail={"code": "content_service_unavailable"})
    if response.status_code == 404:
        raise HTTPException(status_code=403, detail={"code": "teacher_material_document_forbidden"})
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail={"code": "content_service_unavailable"})
    document = response.json().get("data", {})
    metadata = document.get("education_metadata") or {}
    if metadata.get("source_type") != "teacher_material":
        raise HTTPException(status_code=422, detail={"code": "document_is_not_teacher_material"})
    return document


@router.put("/profiles/me")
async def update_profile(payload: EducationProfileInput, user: CurrentUser = Depends(get_current_user)):
    profile = await database.value.education_profiles.find_one_and_update(
        {"user_id": user.id},
        {
            "$set": {"personas": sorted(persona.value for persona in payload.personas), "updated_at": now()},
            "$setOnInsert": {"_id": new_id("EP"), "user_id": user.id, "created_at": now()},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    await audit(user.id, "education_profile_updated", "EducationProfile", profile["_id"])
    return profile


@router.get("/profiles/me")
async def get_profile(user: CurrentUser = Depends(get_current_user)):
    profile = await database.value.education_profiles.find_one({"user_id": user.id})
    return profile or {"user_id": user.id, "personas": []}


@router.get("/profiles/me/settings")
async def get_user_settings(user: CurrentUser = Depends(get_current_user)):
    profile = await database.value.education_profiles.find_one({"user_id": user.id})
    return (profile or {}).get(
        "settings",
        {
            "ui_language": "vi",
            "theme": "system",
            "notifications_enabled": True,
            "accessibility_preferences": {},
            "default_subject": None,
            "privacy_mode": False,
            "data_export_format": "json",
        },
    )


@router.put("/profiles/me/settings")
async def update_user_settings(payload: UserSettingsInput, user: CurrentUser = Depends(get_current_user)):
    profile = await database.value.education_profiles.find_one_and_update(
        {"user_id": user.id},
        {
            "$set": {"settings": payload.model_dump(), "updated_at": now()},
            "$setOnInsert": {"_id": new_id("EP"), "user_id": user.id, "personas": [], "created_at": now()},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    await audit(user.id, "user_settings_updated", "EducationProfile", profile["_id"])
    return profile["settings"]


@router.get("/profiles/me/export")
async def export_user_data(user: CurrentUser = Depends(get_current_user)):
    education_profile = await database.value.education_profiles.find_one({"user_id": user.id})
    teacher_profile = await database.value.teacher_profiles.find_one({"user_id": user.id})
    teacher_events = await database.value.teacher_profile_events.find({"teacher_id": user.id}).sort("created_at", 1).to_list(100000)
    attempts = await database.value.attempts.find({"student_id": user.id}).sort("created_at", 1).to_list(100000)
    attempt_ids = [attempt["_id"] for attempt in attempts]
    assignments = await database.value.assignments.find({"student_id": user.id}).sort("created_at", 1).to_list(100000)
    responses = await database.value.responses.find({"attempt_id": {"$in": attempt_ids}}).sort("submitted_at", 1).to_list(100000)
    export_id = new_id("EXP")
    await audit(
        user.id,
        "user_data_exported",
        "UserDataExport",
        export_id,
        {"attempt_count": len(attempts), "assignment_count": len(assignments), "response_count": len(responses)},
    )
    return {
        "export_id": export_id,
        "generated_at": now(),
        "education_profile": education_profile,
        "teacher_profile": teacher_profile,
        "teacher_profile_events": teacher_events,
        "assignments": assignments,
        "attempts": attempts,
        "responses": responses,
    }


@router.put("/teacher-profile/me")
async def update_teacher_profile(payload: TeacherProfileInput, user: CurrentUser = Depends(require_author)):
    profile = await database.value.teacher_profiles.find_one_and_update(
        {"user_id": user.id},
        {
            "$set": {**payload.model_dump(), "updated_at": now()},
            "$setOnInsert": {"_id": new_id("TP"), "user_id": user.id, "inferred_preferences": {}, "created_at": now()},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    await audit(user.id, "teacher_profile_updated", "TeacherProfile", profile["_id"])
    return profile


@router.get("/teacher-profile/me")
async def get_teacher_profile(user: CurrentUser = Depends(require_author)):
    profile = await database.value.teacher_profiles.find_one({"user_id": user.id})
    return profile or {"user_id": user.id, "explicit_preferences": {}, "inferred_preferences": {}, "use_own_materials": True}


@router.get("/internal/teacher-profile/{user_id}/material-policy", dependencies=[Depends(require_internal_token)])
async def get_teacher_material_policy(user_id: str):
    profile = await database.value.teacher_profiles.find_one(
        {"user_id": user_id},
        {"use_own_materials": 1},
    )
    return {"user_id": user_id, "use_own_materials": not profile or profile.get("use_own_materials") is not False}


@router.delete("/teacher-profile/me/personalization")
async def reset_teacher_personalization(user: CurrentUser = Depends(require_author)):
    await database.value.teacher_profiles.update_one(
        {"user_id": user.id},
        {"$set": {"explicit_preferences": {}, "inferred_preferences": {}, "updated_at": now()}},
        upsert=True,
    )
    await database.value.teacher_profile_events.delete_many({"teacher_id": user.id})
    await audit(user.id, "teacher_personalization_reset", "TeacherProfile", user.id)
    return {"status": "reset"}


@router.get("/teacher-profile/me/events")
async def list_teacher_profile_events(user: CurrentUser = Depends(require_author)):
    return await database.value.teacher_profile_events.find({"teacher_id": user.id}).sort("created_at", -1).limit(100).to_list(100)


@router.post("/teacher-profile/me/events", status_code=201)
async def record_teacher_profile_event(
    payload: TeacherProfileEventInput,
    user: CurrentUser = Depends(require_author),
):
    event, created = await persist_teacher_profile_event(
        user.id,
        payload.event_type,
        payload.payload,
        payload.idempotency_key,
    )
    if created:
        await audit(user.id, "teacher_profile_signal_recorded", "TeacherProfileEvent", event["_id"], {"event_type": payload.event_type})
    return event


@router.post("/curriculum")
async def create_curriculum_node(payload: CurriculumNodeInput, user: CurrentUser = Depends(require_admin)):
    node = payload.model_dump(exclude={"id"})
    node["_id"] = payload.id or new_id("CUR")
    node.update({"revision": 1, "status": "active", "created_at": now(), "updated_at": now()})
    await database.value.curriculum_nodes.insert_one(node)
    await audit(user.id, "curriculum_node_created", "CurriculumNode", node["_id"])
    return node


@router.patch("/curriculum/{node_id}")
async def update_curriculum_node(
    node_id: str,
    payload: CurriculumNodePatch,
    user: CurrentUser = Depends(require_admin),
):
    changes = {key: value for key, value in payload.model_dump().items() if value is not None and key != "expected_revision"}
    changes["updated_at"] = now()
    changes["revision"] = payload.expected_revision + 1
    revision_query = [{"revision": payload.expected_revision}]
    if payload.expected_revision == 1:
        revision_query.append({"revision": {"$exists": False}})
    node = await database.value.curriculum_nodes.find_one_and_update(
        {"_id": node_id, "$or": revision_query},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    if not node:
        existing = await database.value.curriculum_nodes.find_one({"_id": node_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Không tìm thấy curriculum node")
        raise HTTPException(status_code=409, detail={"code": "curriculum_revision_conflict", "current_revision": existing.get("revision")})
    await audit(user.id, "curriculum_node_updated", "CurriculumNode", node_id, {"revision": node["revision"], "changes": sorted(changes)})
    return node


@router.post("/curriculum/{target_node_id}/merge")
async def merge_curriculum_nodes(
    target_node_id: str,
    payload: CurriculumMergeInput,
    user: CurrentUser = Depends(require_admin),
):
    if target_node_id in payload.source_node_ids:
        raise HTTPException(status_code=422, detail={"code": "curriculum_merge_target_in_sources"})
    node_ids = [target_node_id, *payload.source_node_ids]
    merged_at = now()

    async def merge_transaction(session):
        nodes = await database.value.curriculum_nodes.find(
            {"_id": {"$in": node_ids}},
            session=session,
        ).to_list(101)
        by_id = {node["_id"]: node for node in nodes}
        if set(by_id) != set(node_ids):
            raise HTTPException(status_code=404, detail={"code": "curriculum_merge_node_missing"})
        target = by_id[target_node_id]
        if target.get("status", "active") != "active" or int(target.get("revision", 1)) != payload.expected_target_revision:
            raise HTTPException(status_code=409, detail={"code": "curriculum_merge_target_conflict"})
        context_fields = ["education_level", "subject", "target_program", "curriculum_version"]
        for source_id in payload.source_node_ids:
            source = by_id[source_id]
            if source.get("status", "active") != "active" or int(source.get("revision", 1)) != payload.expected_source_revisions[source_id]:
                raise HTTPException(status_code=409, detail={"code": "curriculum_merge_source_conflict", "node_id": source_id})
            if any(source.get(field) != target.get(field) for field in context_fields):
                raise HTTPException(status_code=422, detail={"code": "curriculum_merge_context_mismatch", "node_id": source_id})
        target_update = await database.value.curriculum_nodes.update_one(
            {"_id": target_node_id, "revision": payload.expected_target_revision, "status": "active"},
            {
                "$set": {"updated_at": merged_at},
                "$inc": {"revision": 1},
                "$addToSet": {"merged_from_node_ids": {"$each": payload.source_node_ids}},
            },
            session=session,
        )
        if target_update.modified_count != 1:
            raise HTTPException(status_code=409, detail={"code": "curriculum_merge_target_conflict"})
        for source_id in payload.source_node_ids:
            source_update = await database.value.curriculum_nodes.update_one(
                {"_id": source_id, "revision": payload.expected_source_revisions[source_id], "status": "active"},
                {"$set": {"status": "obsolete", "merged_into_node_id": target_node_id, "updated_at": merged_at}, "$inc": {"revision": 1}},
                session=session,
            )
            if source_update.modified_count != 1:
                raise HTTPException(status_code=409, detail={"code": "curriculum_merge_source_conflict", "node_id": source_id})
        await database.value.curriculum_nodes.update_many(
            {"parent_id": {"$in": payload.source_node_ids}},
            {"$set": {"parent_id": target_node_id, "updated_at": merged_at}, "$inc": {"revision": 1}},
            session=session,
        )
        await database.value.source_mappings.update_many(
            {"curriculum_node_ids": {"$in": payload.source_node_ids}},
            [
                {
                    "$set": {
                        "curriculum_node_ids": {
                            "$setUnion": [
                                {"$setDifference": [{"$ifNull": ["$curriculum_node_ids", []]}, payload.source_node_ids]},
                                [target_node_id],
                            ]
                        },
                        "updated_at": merged_at,
                    }
                }
            ],
            session=session,
        )
        return await database.value.curriculum_nodes.find_one({"_id": target_node_id}, session=session)

    async with await database.client.start_session() as session:
        merged = await session.with_transaction(merge_transaction)
    await audit(user.id, "curriculum_nodes_merged", "CurriculumNode", target_node_id, {"source_node_ids": payload.source_node_ids})
    return merged


@router.post("/curriculum/{node_id}/split", status_code=201)
async def split_curriculum_node(
    node_id: str,
    payload: CurriculumSplitInput,
    user: CurrentUser = Depends(require_admin),
):
    codes = [part.canonical_code for part in payload.parts]
    split_at = now()

    async def split_transaction(session):
        source = await database.value.curriculum_nodes.find_one({"_id": node_id}, session=session)
        if not source:
            raise HTTPException(status_code=404, detail="Không tìm thấy curriculum node")
        if source.get("status", "active") != "active" or int(source.get("revision", 1)) != payload.expected_revision:
            raise HTTPException(status_code=409, detail={"code": "curriculum_split_revision_conflict", "current_revision": source.get("revision", 1)})
        collision = await database.value.curriculum_nodes.find_one(
            {"canonical_code": {"$in": codes}, "curriculum_version": source["curriculum_version"]},
            session=session,
        )
        if collision:
            raise HTTPException(status_code=409, detail={"code": "curriculum_split_code_conflict", "canonical_code": collision["canonical_code"]})
        parts = []
        for part_input in payload.parts:
            part = {
                **{key: source.get(key) for key in ["education_level", "subject", "target_program", "curriculum_version", "parent_id"]},
                **part_input.model_dump(exclude_none=True),
                "_id": new_id("CUR"),
                "node_type": part_input.node_type or source["node_type"],
                "revision": 1,
                "status": "active",
                "split_from_node_id": node_id,
                "created_at": split_at,
                "updated_at": split_at,
            }
            parts.append(part)
        primary_part_id = parts[0]["_id"]
        updated = await database.value.curriculum_nodes.find_one_and_update(
            {"_id": node_id, "revision": payload.expected_revision, "status": "active"},
            {
                "$set": {"status": "obsolete", "split_into_node_ids": [part["_id"] for part in parts], "updated_at": split_at},
                "$inc": {"revision": 1},
            },
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        if not updated:
            raise HTTPException(status_code=409, detail={"code": "curriculum_split_revision_conflict"})
        await database.value.curriculum_nodes.insert_many(parts, session=session)
        await database.value.curriculum_nodes.update_many(
            {"parent_id": node_id},
            {"$set": {"parent_id": primary_part_id, "updated_at": split_at}, "$inc": {"revision": 1}},
            session=session,
        )
        await database.value.source_mappings.update_many(
            {"curriculum_node_ids": node_id},
            [
                {
                    "$set": {
                        "curriculum_node_ids": {
                            "$setUnion": [
                                {"$setDifference": [{"$ifNull": ["$curriculum_node_ids", []]}, [node_id]]},
                                [primary_part_id],
                            ]
                        },
                        "updated_at": split_at,
                    }
                }
            ],
            session=session,
        )
        return updated, parts

    try:
        async with await database.client.start_session() as session:
            updated, parts = await session.with_transaction(split_transaction)
    except DuplicateKeyError as error:
        raise HTTPException(status_code=409, detail={"code": "curriculum_split_code_conflict"}) from error
    await audit(user.id, "curriculum_node_split", "CurriculumNode", node_id, {"part_node_ids": [part["_id"] for part in parts], "allocation_policy": "existing_relations_to_first_part"})
    return {"source": updated, "parts": parts, "allocation_policy": "existing_relations_to_first_part"}


@router.get("/curriculum")
async def list_curriculum(
    education_level: str | None = None,
    subject: str | None = None,
    target_program: str | None = None,
    parent_id: str | None = None,
    include_obsolete: bool = False,
    user: CurrentUser = Depends(get_current_user),
):
    query = {}
    if not include_obsolete:
        query["status"] = {"$ne": "obsolete"}
    for key, value in {
        "education_level": education_level,
        "subject": subject,
        "target_program": target_program,
        "parent_id": parent_id,
    }.items():
        if value is not None:
            query[key] = value
    return await database.value.curriculum_nodes.find(query).sort("canonical_code", 1).to_list(1000)


@router.get("/mappings/review")
async def list_mapping_review_backlog(user: CurrentUser = Depends(require_admin)):
    mappings = await database.value.source_mappings.find(
        {
            "mapping_status": {"$ne": "rejected"},
            "$or": [
                {"mapping_status": "needs_review"},
                {"mapping_confidence": {"$lt": 0.7}},
                {
                    "$and": [
                        {"curriculum_node_ids": {"$size": 0}},
                        {"concept_ids": {"$size": 0}},
                        {"skill_ids": {"$size": 0}},
                    ]
                },
            ]
        }
    ).sort("mapping_confidence", 1).limit(2000).to_list(2000)
    return {
        "items": mappings,
        "low_confidence_count": sum(1 for mapping in mappings if float(mapping.get("mapping_confidence", 0)) < 0.7),
        "unmapped_count": sum(
            1
            for mapping in mappings
            if not mapping.get("curriculum_node_ids") and not mapping.get("concept_ids") and not mapping.get("skill_ids")
        ),
    }


@router.get("/curriculum/{node_id}")
async def get_curriculum_node(node_id: str, user: CurrentUser = Depends(get_current_user)):
    return await database.value.curriculum_nodes.find_one({"_id": node_id})


@router.post("/sources/{document_id}/map")
async def create_source_mapping(
    document_id: str,
    payload: SourceMappingInput,
    user: CurrentUser = Depends(get_current_user),
):
    if payload.document_id != document_id:
        raise HTTPException(status_code=422, detail={"code": "mapping_document_id_mismatch"})
    if payload.source_type == "curriculum" and not user.is_admin:
        raise HTTPException(status_code=403, detail={"code": "curriculum_mapping_requires_admin"})
    if payload.source_type == "teacher_material" and user.role not in {Role.AUTHOR, Role.ADMIN}:
        raise HTTPException(status_code=403, detail={"code": "teacher_material_mapping_requires_author"})
    if payload.source_type == "teacher_material":
        await require_owned_teacher_material(document_id, user)
    mapping = payload.model_dump()
    mapping["document_id"] = document_id
    mapping["_id"] = new_id("MAP")
    mapping["creator_id"] = None if payload.source_type == "curriculum" else user.id
    mapping["created_at"] = now()
    mapping["request_hash"] = hashlib.sha256(
        json.dumps(
            {key: value for key, value in mapping.items() if key not in {"_id", "created_at"}},
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ).encode()
    ).hexdigest()
    try:
        await database.value.source_mappings.insert_one(mapping)
    except DuplicateKeyError:
        duplicate = await database.value.source_mappings.find_one(
            {"document_id": document_id, "chunk_id": payload.chunk_id}
        )
        if duplicate and (user.is_admin or duplicate.get("creator_id") == user.id):
            if duplicate.get("request_hash") == mapping["request_hash"]:
                return duplicate
            legacy_matches = all(
                duplicate.get(key) == mapping.get(key)
                for key in type(payload).model_fields
            )
            if legacy_matches:
                return duplicate
            raise HTTPException(status_code=409, detail={"code": "source_mapping_payload_conflict"})
        raise HTTPException(status_code=409, detail={"code": "source_mapping_conflict"})
    await audit(user.id, "source_mapping_created", "SourceMapping", mapping["_id"])
    metrics.set("question_mapping_confidence", payload.mapping_confidence)
    return mapping


@router.get("/sources/{document_id}/mapping")
async def list_source_mappings(document_id: str, user: CurrentUser = Depends(get_current_user)):
    query = {
        "document_id": document_id,
        "$or": [
            {"source_type": "curriculum", "authority": {"$in": ["official", "verified"]}},
            {"source_type": "teacher_material", "creator_id": user.id},
        ],
    }
    return await database.value.source_mappings.find(query).sort("created_at", -1).to_list(1000)


@router.post("/sources/{document_id}/reindex")
async def reindex_source_document(document_id: str, user: CurrentUser = Depends(require_admin)):
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            f"{settings.RAG_URL}/rag/ingest",
            headers={"X-Internal-Token": settings.SECRET_KEY},
            json={"document_id": document_id, "requester_id": user.id, "is_admin": True},
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail={"code": "source_reindex_failed"})
    result = response.json().get("data", {})
    await audit(user.id, "curriculum_source_reindexed", "SourceDocument", document_id, {"chunks_count": result.get("chunks_count", 0)})
    return result


@router.post("/sources/{document_id}/obsolete")
async def mark_curriculum_source_obsolete(
    document_id: str,
    payload: SourceObsoleteInput,
    user: CurrentUser = Depends(require_admin),
):
    mappings = await database.value.source_mappings.find({"document_id": document_id, "source_type": "curriculum"}).to_list(100000)
    if not mappings:
        raise HTTPException(status_code=404, detail={"code": "curriculum_source_mapping_missing"})
    obsolete_at = now()
    await database.value.source_mappings.update_many(
        {"document_id": document_id, "source_type": "curriculum"},
        {"$set": {"source_status": "obsolete_pending_deindex", "obsolete_reason": payload.reason, "obsolete_at": obsolete_at}},
    )
    async with httpx.AsyncClient(timeout=180) as client:
        content_response = await client.post(
            f"{settings.CONTENT_URL}/tai-lieu/noi-bo/trao-doi",
            headers={"X-Internal-Token": settings.SECRET_KEY},
            json={"action": "mark_source_obsolete", "document_id": document_id, "reason": payload.reason},
        )
        rag_response = await client.delete(
            f"{settings.RAG_URL}/rag/document/{document_id}",
            headers={"X-Internal-Token": settings.SECRET_KEY},
            params={"requester_id": user.id, "is_admin": "true"},
        )
    content_updated = content_response.status_code < 400 and bool(content_response.json().get("data", {}).get("updated"))
    if not content_updated or rag_response.status_code >= 400:
        await audit(user.id, "curriculum_source_obsolete_failed", "SourceDocument", document_id, {"reason": payload.reason})
        raise HTTPException(status_code=502, detail={"code": "curriculum_source_obsolete_failed"})
    await database.value.source_mappings.update_many(
        {"document_id": document_id, "source_type": "curriculum"},
        {"$set": {"source_status": "obsolete", "updated_at": now()}},
    )
    await audit(user.id, "curriculum_source_marked_obsolete", "SourceDocument", document_id, {"reason": payload.reason})
    return {"document_id": document_id, "status": "obsolete", "deindexed": True}


@router.patch("/sources/{document_id}/mapping/{mapping_id}")
async def review_source_mapping(
    document_id: str,
    mapping_id: str,
    payload: SourceMappingReviewInput,
    user: CurrentUser = Depends(get_current_user),
):
    current = await database.value.source_mappings.find_one({"_id": mapping_id, "document_id": document_id})
    if not current:
        raise HTTPException(status_code=404, detail="Không tìm thấy mapping")
    if not user.is_admin and not (current.get("source_type") == "teacher_material" and current.get("creator_id") == user.id):
        raise HTTPException(status_code=403, detail={"code": "mapping_review_forbidden"})
    changes = {key: value for key, value in payload.model_dump().items() if value is not None}
    changes.update({"reviewed_by": user.id, "updated_at": now()})
    mapping = await database.value.source_mappings.find_one_and_update(
        {"_id": mapping_id, "document_id": document_id},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    await audit(user.id, "source_mapping_reviewed", "SourceMapping", mapping_id, {"mapping_status": payload.mapping_status})
    metrics.set("question_mapping_confidence", float(mapping.get("mapping_confidence", 0)))
    return mapping
