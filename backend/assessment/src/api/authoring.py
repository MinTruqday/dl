from copy import deepcopy
import asyncio
import hashlib
import json
import time
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.api.common import audit, new_id, now, optimistic_patch, require_owned
from src.core.auth import CurrentUser, require_author
from src.core.database import database
from src.core.metrics import metrics
from src.domain.models import (
    AssessmentDraftCreate,
    AssessmentDraftPatch,
    AssessmentRebalanceInput,
    BlueprintInput,
    BlueprintPatch,
    BlueprintSuggestionInput,
    DistractorRevisionInput,
    DraftAiActionInput,
    DifficultyPredictionInput,
    DifficultyTargetInput,
    GenerateRequest,
    ImportConfirmInput,
    ImportFileRequest,
    ImportRequest,
    LearnerFitInput,
    QuestionArchiveInput,
    QuestionBankAddInput,
    QuestionDraftCreate,
    QuestionDraftPatch,
    ReviewDecisionInput,
    RevisionProposalInput,
    TeacherEstimateInput,
    ValidityReviewInput,
)
from src.services.blueprint import difficulty_level, validate_blueprint
from src.services.difficulty import predict_difficulty
from src.services.generation import generated_question, requested_difficulties
from src.services.importing import duplicate_fingerprint, split_page, structure_pages, tiptap_doc
from src.services.learner_fit import evaluate_learner_fit
from src.services.optimizer import optimize_blueprint
from src.core.configuration import settings
from src.services.validation import near_duplicate_score, text_projection, validate_question, validate_tiptap_content
from src.services.teacher_profile import persist_teacher_profile_event


router = APIRouter(tags=["authoring"])


def teacher_material_requested(payload: GenerateRequest):
    return payload.use_teacher_materials or payload.source_scope == "curriculum_and_owned_material"


async def enforce_teacher_material_setting(user: CurrentUser):
    profile = await database.value.teacher_profiles.find_one(
        {"user_id": user.id},
        {"use_own_materials": 1},
    )
    if profile and profile.get("use_own_materials") is False:
        raise HTTPException(status_code=409, detail={"code": "teacher_material_use_disabled"})


async def enforce_teacher_material_policy(payload: GenerateRequest, user: CurrentUser):
    supplied_material = any(item.get("source_type") == "teacher_material" for item in payload.source_evidence)
    if not teacher_material_requested(payload) and not supplied_material:
        return
    await enforce_teacher_material_setting(user)


async def validate_owned_question(question: dict[str, Any], user: CurrentUser):
    result = validate_question(question)
    draft_query: dict[str, Any] = {"owner_id": user.id, "_id": {"$ne": question.get("_id")}}
    version_query: dict[str, Any] = {"owner_id": user.id}
    if question.get("question_id"):
        draft_query["question_id"] = {"$ne": question["question_id"]}
        version_query["question_id"] = {"$ne": question["question_id"]}
    drafts, versions = await asyncio.gather(
        database.value.question_drafts.find(draft_query).limit(5000).to_list(5000),
        database.value.question_versions.find(version_query).limit(5000).to_list(5000),
    )
    matches = [
        {"entity_id": candidate.get("_id"), "score": round(score, 4)}
        for candidate in [*drafts, *versions]
        if (score := near_duplicate_score(question, candidate)) >= 0.9
    ]
    if matches:
        issue = {
            "code": "near_duplicate_question",
            "severity": "NEEDS_REVIEW",
            "status": "NEEDS_REVIEW",
            "confidence": 0.95,
            "matches": sorted(matches, key=lambda item: item["score"], reverse=True)[:20],
        }
        result["warnings"].append(issue)
        result["checks"].append(issue)
        if not result["blockers"]:
            result["status"] = "NEEDS_REVIEW"
    return result


async def retrieve_generation_evidence(payload: GenerateRequest, user: CurrentUser):
    filters = {
        "education_level": payload.education_level,
        "subject": payload.subject,
        "target_program": payload.target_program,
        "source_type": "curriculum",
        "authority": ["official", "verified"],
    }
    if payload.chapter_id:
        filters["chapter_id"] = payload.chapter_id
    if payload.lesson_id:
        filters["lesson_id"] = payload.lesson_id
    requests = [(filters, False)]
    material_requested = teacher_material_requested(payload)
    if material_requested:
        requests.append(({**filters, "source_type": "teacher_material", "authority": None}, True))
    evidence = []
    conflicts = []
    material_evidence_found = False
    async with httpx.AsyncClient(timeout=90) as client:
        for metadata_filters, owned in requests:
            response = await client.post(
                f"{settings.RAG_URL}/rag/retrieve",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                json={
                    "query": payload.topic,
                    "k": 8,
                    "requester_id": user.id,
                    "metadata_filters": {key: value for key, value in metadata_filters.items() if value is not None},
                },
            )
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail={"code": "generation_evidence_unavailable"})
            result = response.json().get("data", {})
            conflicts.extend(result.get("conflicts", []))
            for document in result.get("documents", []):
                metadata = document.get("metadata", {})
                if owned and str(metadata.get("owner_id") or metadata.get("creator_id")) != user.id:
                    continue
                evidence.append({"text": document.get("text", "")[:4000], **metadata})
                material_evidence_found = material_evidence_found or owned
    if conflicts:
        raise HTTPException(status_code=409, detail={"code": "generation_source_conflict", "conflicts": conflicts})
    if not evidence:
        raise HTTPException(status_code=422, detail={"code": "generation_evidence_required"})
    if material_evidence_found:
        await persist_teacher_profile_event(
            user.id,
            "material_used",
            {"topic": payload.topic, "subject": payload.subject},
            f"material-{payload.idempotency_key}",
        )
    return evidence[:12]


async def generate_with_agent(payload: dict[str, Any], difficulty: float, evidence: list[dict[str, Any]]):
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{settings.AI_URL}/suy-luan/noi-bo/tao-cau-hoi-danh-gia",
            headers={"X-Internal-Token": settings.SECRET_KEY},
            json={
                "education_level": payload["education_level"],
                "target_program": payload["target_program"],
                "subject": payload["subject"],
                "topic": payload["topic"],
                "question_type": payload["question_type"],
                "target_difficulty": difficulty,
                "cognitive_level": payload.get("cognitive_level"),
                "evidence": evidence,
            },
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail={"code": "ai_question_generation_failed"})
    return response.json()


async def judge_difficulty_with_agent(question: dict[str, Any]):
    curriculum = (question.get("curriculum_links") or [{}])[0]
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{settings.AI_URL}/suy-luan/noi-bo/danh-gia-do-kho-truc-tiep",
            headers={"X-Internal-Token": settings.SECRET_KEY},
            json={
                "question_type": question.get("question_type", "unknown"),
                "stem": text_projection(question.get("stem_doc", {})),
                "options": [text_projection(option.get("content_doc", {})) for option in question.get("options", [])],
                "answer_key": question.get("answer_key", {}),
                "solution": text_projection(question.get("solution_doc", {})),
                "education_level": curriculum.get("education_level", ""),
                "subject": curriculum.get("subject", ""),
                "target_program": curriculum.get("target_program", ""),
            },
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail={"code": "llm_direct_difficulty_unavailable"})
    return response.json()


async def similar_historical_items(question: dict[str, Any], user: CurrentUser):
    similar_versions = await database.value.question_versions.find(
        {
            "owner_id": user.id,
            "_id": {"$ne": question.get("frozen_version_id")},
            "concept_ids": {"$in": question.get("concept_ids", [])},
        }
    ).sort("created_at", -1).limit(20).to_list(20)
    similar_calibrations = await database.value.calibrations.find(
        {"question_version_id": {"$in": [version["_id"] for version in similar_versions]}, "status": "calibrated"}
    ).sort("created_at", -1).to_list(100)
    latest_similar = {}
    for calibration in similar_calibrations:
        latest_similar.setdefault(calibration["question_version_id"], calibration)
    return [
        {
            "question_version_id": version["_id"],
            "question_id": version.get("question_id"),
            "same_logical_question": bool(question.get("question_id") and version.get("question_id") == question.get("question_id")),
            "difficulty": latest_similar[version["_id"]].get("difficulty"),
            "sample_size": latest_similar[version["_id"]].get("sample_size", 0),
        }
        for version in similar_versions
        if version["_id"] in latest_similar
    ][:5]


async def prediction_with_empirical_context(prediction: dict[str, Any], question: dict[str, Any]):
    result = deepcopy(prediction)
    version_id = question.get("frozen_version_id")
    calibration = None
    if version_id:
        calibration = await database.value.calibrations.find_one(
            {"question_version_id": version_id, "status": "calibrated"},
            sort=[("created_at", -1)],
        )
    result["calibrated_difficulty"] = calibration.get("difficulty") if calibration else None
    result["calibration_sample_size"] = calibration.get("sample_size", 0) if calibration else 0
    result["calibration_population_context"] = calibration.get("population_context", {}) if calibration else {}
    result["calibration_drift_flag"] = bool(calibration and calibration.get("drift_flag"))
    result["predicted_empirical_gap"] = (
        round(float(prediction["predicted_difficulty"]) - float(calibration["difficulty"]), 3)
        if calibration and calibration.get("difficulty") is not None
        else None
    )
    return result


async def persist_question_draft(
    draft_id: str,
    payload: dict[str, Any],
    user: CurrentUser,
    question_draft_id: str | None = None,
    allow_existing: bool = False,
):
    question = question_draft_document(draft_id, payload, user.id, question_draft_id)
    try:
        await database.value.question_drafts.insert_one(question)
    except DuplicateKeyError:
        existing = await database.value.question_drafts.find_one(
            {"_id": question["_id"], "assessment_draft_id": draft_id, "owner_id": user.id}
        )
        if existing and allow_existing:
            draft = await database.value.assessment_drafts.find_one(
                {"_id": draft_id, "owner_id": user.id}, {"question_order": 1}
            )
            if draft and question["_id"] not in draft.get("question_order", []):
                await database.value.assessment_drafts.update_one(
                    {"_id": draft_id, "owner_id": user.id, "question_order": {"$ne": question["_id"]}},
                    {"$addToSet": {"question_order": question["_id"]}, "$inc": {"revision": 1}, "$set": {"updated_at": now()}},
                )
            return existing
        raise HTTPException(status_code=409, detail={"code": "question_draft_identity_conflict"})
    await database.value.assessment_drafts.update_one(
        {"_id": draft_id, "owner_id": user.id},
        {"$push": {"question_order": question["_id"]}, "$inc": {"revision": 1}, "$set": {"updated_at": now()}},
    )
    await audit(user.id, "question_draft_created", "QuestionDraft", question["_id"], {"source": question["authoring_source"]})
    return question


def question_draft_document(
    draft_id: str,
    payload: dict[str, Any],
    owner_id: str,
    question_draft_id: str | None = None,
):
    question = deepcopy(payload)
    created_at = now()
    question.update(
        {
            "_id": question_draft_id or new_id("QD"),
            "question_id": None,
            "assessment_draft_id": draft_id,
            "owner_id": owner_id,
            "revision": 1,
            "status": "draft",
            "created_at": created_at,
            "updated_at": created_at,
        }
    )
    return question


@router.post("/assessment-drafts", status_code=201)
async def create_assessment_draft(payload: AssessmentDraftCreate, user: CurrentUser = Depends(require_author)):
    draft = payload.model_dump()
    draft.update(
        {
            "_id": new_id("AD"),
            "owner_id": user.id,
            "question_order": [],
            "blueprint_id": None,
            "revision": 1,
            "status": "draft",
            "created_at": now(),
            "updated_at": now(),
        }
    )
    await database.value.assessment_drafts.insert_one(draft)
    await audit(user.id, "assessment_draft_created", "AssessmentDraft", draft["_id"])
    return draft


@router.get("/assessment-drafts")
async def list_assessment_drafts(user: CurrentUser = Depends(require_author)):
    return await database.value.assessment_drafts.find({"owner_id": user.id}).sort("updated_at", -1).to_list(500)


@router.get("/teacher-materials/search")
async def search_teacher_materials(
    q: str,
    subject: str | None = None,
    limit: int = 10,
    user: CurrentUser = Depends(require_author),
):
    if not q.strip():
        raise HTTPException(status_code=422, detail={"code": "teacher_material_search_query_required"})
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=422, detail={"code": "teacher_material_search_limit_invalid"})
    filters = {"source_type": "teacher_material"}
    if subject:
        filters["subject"] = subject
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{settings.RAG_URL}/rag/retrieve",
            headers={"X-Internal-Token": settings.SECRET_KEY},
            json={
                "query": q.strip(),
                "k": limit,
                "requester_id": user.id,
                "is_admin": user.is_admin,
                "metadata_filters": filters,
            },
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail={"code": "teacher_material_search_unavailable"})
    return response.json().get("data", {})


@router.get("/assessment-drafts/{draft_id}")
async def get_assessment_draft(draft_id: str, user: CurrentUser = Depends(require_author)):
    draft = await require_owned("assessment_drafts", draft_id, user)
    questions = await database.value.question_drafts.find({"assessment_draft_id": draft_id}).to_list(500)
    by_id = {question["_id"]: question for question in questions}
    draft["questions"] = [by_id[question_id] for question_id in draft.get("question_order", []) if question_id in by_id]
    return draft


@router.patch("/assessment-drafts/{draft_id}")
async def patch_assessment_draft(
    draft_id: str,
    payload: AssessmentDraftPatch,
    user: CurrentUser = Depends(require_author),
):
    draft = await optimistic_patch("assessment_drafts", draft_id, user.id, payload.expected_revision, payload.model_dump())
    await audit(user.id, "assessment_draft_updated", "AssessmentDraft", draft_id, {"revision": draft["revision"]})
    return draft


@router.post("/assessment-drafts/{draft_id}/questions", status_code=201)
async def create_question_draft(
    draft_id: str,
    payload: QuestionDraftCreate,
    user: CurrentUser = Depends(require_author),
):
    await require_owned("assessment_drafts", draft_id, user)
    return await persist_question_draft(draft_id, payload.model_dump(mode="json", by_alias=True), user)


@router.post("/assessment-drafts/{draft_id}/import", status_code=202)
async def import_assessment_draft(
    draft_id: str,
    payload: ImportRequest,
    user: CurrentUser = Depends(require_author),
):
    started = time.perf_counter()
    await require_owned("assessment_drafts", draft_id, user)
    existing = await database.value.import_jobs.find_one({"owner_id": user.id, "idempotency_key": payload.idempotency_key})
    if existing:
        metrics.set("assessment_import_duration", time.perf_counter() - started)
        return existing
    candidates = []
    for page in payload.pages:
        page_data = page.model_dump()
        page_data["document_id"] = payload.document_id
        candidates.extend(split_page(page_data))
    existing_drafts = await database.value.question_drafts.find({"owner_id": user.id}).to_list(5000)
    existing_versions = await database.value.question_versions.find({"owner_id": user.id}).to_list(5000)
    fingerprints = {duplicate_fingerprint(question) for question in [*existing_drafts, *existing_versions]}
    for candidate in candidates:
        answer = payload.answer_key.get(str(candidate["source_number"]))
        if answer is not None:
            if candidate["question_type"] == "single_choice":
                candidate["answer_key"] = {"option_id": str(answer)}
            else:
                candidate["answer_key"] = {"accepted": [str(answer)]}
        candidate["duplicate_flag"] = duplicate_fingerprint(candidate) in fingerprints
        candidate["exception_flags"] = []
        if candidate["parse_confidence"] < 0.7:
            candidate["exception_flags"].append("low_parse_confidence")
        if not candidate["answer_key"]:
            candidate["exception_flags"].append("missing_answer_key")
        evidence = candidate.get("source_evidence", [{}])[0]
        if evidence.get("formula_refs") and not any(ref.get("latex") for ref in evidence["formula_refs"]):
            candidate["exception_flags"].append("formula_needs_review")
        if evidence.get("image_refs") and not all(ref.get("url") for ref in evidence["image_refs"]):
            candidate["exception_flags"].append("image_reference_missing")
    job = {
        "_id": new_id("IMP"),
        "owner_id": user.id,
        "assessment_draft_id": draft_id,
        "document_id": payload.document_id,
        "file_name": payload.file_name,
        "parser_version": payload.parser_version,
        "idempotency_key": payload.idempotency_key,
        "status": "needs_review",
        "progress": 100,
        "candidates": candidates,
        "created_at": now(),
        "updated_at": now(),
    }
    try:
        await database.value.import_jobs.insert_one(job)
    except DuplicateKeyError:
        duplicate = await database.value.import_jobs.find_one(
            {"owner_id": user.id, "idempotency_key": payload.idempotency_key}
        )
        if duplicate:
            return duplicate
        raise HTTPException(status_code=409, detail={"code": "assessment_import_conflict"})
    await audit(user.id, "assessment_import_parsed", "ImportJob", job["_id"], {"candidate_count": len(candidates)})
    metrics.set("assessment_import_duration", time.perf_counter() - started)
    return job


@router.post("/assessment-drafts/{draft_id}/import-file", status_code=202)
async def import_assessment_file(
    draft_id: str,
    payload: ImportFileRequest,
    user: CurrentUser = Depends(require_author),
):
    await require_owned("assessment_drafts", draft_id, user)
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            f"{settings.RAG_URL}/rag/convert",
            headers={"X-Internal-Token": settings.SECRET_KEY},
            json={"data": payload.data, "filename": payload.file_name},
        )
    if response.status_code == 413:
        raise HTTPException(status_code=413, detail="Tệp vượt quá giới hạn dung lượng")
    if response.status_code >= 400:
        raise HTTPException(status_code=422, detail={"code": "document_parsing_failed"})
    parsed = response.json().get("data", {})
    document_id = f"IMPDOC-{hashlib.sha256(payload.data.encode()).hexdigest()[:32]}"
    pages = structure_pages(document_id, str(parsed.get("markdown") or ""), parsed.get("structure") or [])
    if not any(page["text"].strip() for page in pages):
        raise HTTPException(status_code=422, detail={"code": "document_text_unavailable"})
    request = ImportRequest(
        idempotency_key=payload.idempotency_key,
        document_id=document_id,
        file_name=payload.file_name,
        pages=pages,
        answer_key=payload.answer_key,
        parser_version="docling_question_parser_v1",
    )
    return await import_assessment_draft(draft_id, request, user)


@router.get("/imports/{job_id}")
async def get_import_job(job_id: str, user: CurrentUser = Depends(require_author)):
    return await require_owned("import_jobs", job_id, user)


@router.post("/imports/{job_id}/confirm", status_code=201)
async def confirm_import(
    job_id: str,
    payload: ImportConfirmInput,
    user: CurrentUser = Depends(require_author),
):
    job = await require_owned("import_jobs", job_id, user)
    if job["status"] == "confirmed":
        questions = await database.value.question_drafts.find(
            {"_id": {"$in": job.get("question_draft_ids", [])}, "owner_id": user.id}
        ).to_list(500)
        by_id = {question["_id"]: question for question in questions}
        return {
            "job_id": job_id,
            "status": "confirmed",
            "question_draft_ids": job.get("question_draft_ids", []),
            "questions": [by_id[question_id] for question_id in job.get("question_draft_ids", []) if question_id in by_id],
        }
    candidates = {candidate["candidate_id"]: candidate for candidate in job["candidates"]}
    selected = payload.selected_candidate_ids or list(candidates)
    if len(selected) != len(set(selected)):
        raise HTTPException(status_code=422, detail={"code": "import_candidate_selection_duplicate"})
    for candidate_id in selected:
        source_candidate = candidates.get(candidate_id)
        derived = any(candidate_id.startswith(f"{known_id}-split-") for known_id in candidates)
        if not source_candidate and not derived:
            raise HTTPException(status_code=422, detail={"code": "import_candidate_missing", "candidate_id": candidate_id})
        if derived and candidate_id not in payload.corrected_questions:
            raise HTTPException(status_code=422, detail={"code": "derived_import_candidate_requires_correction", "candidate_id": candidate_id})
    confirmation_payload = payload.model_dump(mode="json", by_alias=True)
    confirmation_hash = hashlib.sha256(
        json.dumps(confirmation_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if job.get("confirmation_hash") and job["confirmation_hash"] != confirmation_hash:
        raise HTTPException(status_code=409, detail={"code": "import_confirmation_payload_conflict"})
    claimed = await database.value.import_jobs.find_one_and_update(
        {
            "_id": job_id,
            "owner_id": user.id,
            "status": {"$in": ["needs_review", "confirmation_failed"]},
            "$or": [
                {"confirmation_hash": {"$exists": False}},
                {"confirmation_hash": confirmation_hash},
            ],
        },
        {"$set": {"status": "confirming", "confirmation_hash": confirmation_hash, "updated_at": now()}},
        return_document=ReturnDocument.AFTER,
    )
    if not claimed:
        current = await require_owned("import_jobs", job_id, user)
        if current["status"] == "confirmed":
            return await confirm_import(job_id, payload, user)
        raise HTTPException(status_code=409, detail={"code": "import_confirmation_in_progress"})
    job = claimed
    created = []
    try:
        for candidate_id in selected:
            source_candidate = candidates.get(candidate_id)
            derived = any(candidate_id.startswith(f"{known_id}-split-") for known_id in candidates)
            candidate = deepcopy(source_candidate) if source_candidate else {}
            if candidate_id in payload.corrected_questions:
                candidate = payload.corrected_questions[candidate_id].model_dump(mode="json", by_alias=True)
                if source_candidate:
                    candidate["source_page"] = source_candidate.get("source_page")
                    candidate["parse_confidence"] = source_candidate.get("parse_confidence")
            for key in ["candidate_id", "source_number", "duplicate_flag", "exception_flags", "recognized", "needs_teacher_review"]:
                candidate.pop(key, None)
            candidate["import_job_id"] = job_id
            candidate["import_candidate_id"] = candidate_id
            deterministic_id = f"QD-{hashlib.sha256(f'{job_id}:{candidate_id}'.encode()).hexdigest()[:32]}"
            question = await persist_question_draft(
                job["assessment_draft_id"], candidate, user, deterministic_id, allow_existing=True
            )
            created.append(question)
            await database.value.import_jobs.update_one(
                {"_id": job_id, "owner_id": user.id, "status": "confirming"},
                {"$addToSet": {"question_draft_ids": question["_id"]}, "$set": {"updated_at": now()}},
            )
    except Exception as error:
        await database.value.import_jobs.update_one(
            {"_id": job_id, "owner_id": user.id, "status": "confirming"},
            {"$set": {"status": "confirmation_failed", "error_code": type(error).__name__, "updated_at": now()}},
        )
        raise
    question_ids = [question["_id"] for question in created]
    await database.value.import_jobs.update_one(
        {"_id": job_id, "owner_id": user.id, "status": "confirming"},
        {"$set": {"status": "confirmed", "question_draft_ids": question_ids, "updated_at": now()}, "$unset": {"error_code": ""}},
    )
    await audit(user.id, "assessment_import_confirmed", "ImportJob", job_id, {"question_count": len(created)})
    return {"job_id": job_id, "status": "confirmed", "questions": created}


@router.post("/assessment-drafts/{draft_id}/generate", status_code=201)
async def generate_assessment_questions(
    draft_id: str,
    payload: GenerateRequest,
    user: CurrentUser = Depends(require_author),
):
    assessment_draft = await require_owned("assessment_drafts", draft_id, user)
    await enforce_teacher_material_policy(payload, user)
    existing = await database.value.generation_runs.find_one({"owner_id": user.id, "idempotency_key": payload.idempotency_key})
    if existing:
        questions = await database.value.question_drafts.find({"_id": {"$in": existing.get("question_draft_ids", [])}}).to_list(100)
        return {**existing, "questions": questions}
    for evidence in payload.source_evidence:
        if evidence.get("source_type") == "teacher_material" and str(evidence.get("owner_id") or evidence.get("creator_id")) != user.id:
            raise HTTPException(status_code=403, detail={"code": "teacher_material_scope_violation"})
    run = {
        "_id": new_id("GEN"),
        "owner_id": user.id,
        "assessment_draft_id": draft_id,
        "idempotency_key": payload.idempotency_key,
        "question_draft_ids": [],
        "status": "processing",
        "created_at": now(),
        "updated_at": now(),
    }
    reserved = await database.value.generation_runs.find_one_and_update(
        {"owner_id": user.id, "idempotency_key": payload.idempotency_key},
        {"$setOnInsert": run},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    if reserved["_id"] != run["_id"]:
        questions = await database.value.question_drafts.find(
            {"_id": {"$in": reserved.get("question_draft_ids", [])}}
        ).to_list(100)
        return {**reserved, "questions": questions}
    generation = payload.model_dump(mode="json")
    try:
        evidence = payload.source_evidence if settings.ASSESSMENT_ALLOW_TEST_IDENTITY and payload.source_evidence else await retrieve_generation_evidence(payload, user)
        generation["source_evidence"] = evidence
        difficulties = requested_difficulties(generation)
        questions = []
        for position, difficulty in enumerate(difficulties, start=1):
            model_output = await generate_with_agent(generation, difficulty, evidence)
            question_data = generated_question(generation, position, difficulty, model_output)
            generation_validation = validate_question(question_data)
            if generation_validation["blockers"]:
                raise HTTPException(
                    status_code=502,
                    detail={"code": "ai_question_generation_invalid", "validation": generation_validation},
                )
            question = await persist_question_draft(draft_id, question_data, user)
            await database.value.generation_runs.update_one(
                {"_id": run["_id"]},
                {"$push": {"question_draft_ids": question["_id"]}, "$set": {"updated_at": now()}},
            )
            estimate = predict_difficulty(question, "structured_generation_v1")
            generation_prediction_identity = hashlib.sha256(
                f"{question['_id']}:{question['revision']}:structured_generation_v1".encode()
            ).hexdigest()
            estimate.update(
                {
                    "_id": f"DIF-{generation_prediction_identity[:32]}",
                    "question_draft_id": question["_id"],
                    "question_version_id": None,
                    "question_revision": question["revision"],
                    "owner_id": user.id,
                    "requested_target_difficulty": difficulty,
                    "revealed_at": None if assessment_draft.get("research_blind_mode") else now(),
                    "created_at": now(),
                }
            )
            await database.value.difficulty_estimates.insert_one(estimate)
            question["difficulty_prediction"] = None if assessment_draft.get("research_blind_mode") else estimate
            question["quality_checks"] = generation_validation
            questions.append(question)
    except Exception as error:
        await database.value.generation_runs.update_one(
            {"_id": run["_id"]},
            {"$set": {"status": "failed", "error_code": type(error).__name__, "updated_at": now()}},
        )
        raise
    await database.value.generation_runs.update_one(
        {"_id": run["_id"]},
        {"$set": {"status": "needs_teacher_review", "updated_at": now()}},
    )
    run.update({"question_draft_ids": [question["_id"] for question in questions], "status": "needs_teacher_review", "updated_at": now()})
    await audit(user.id, "assessment_questions_generated", "GenerationRun", run["_id"], {"question_count": len(questions)})
    return {**run, "questions": questions}


@router.post("/assessment-drafts/{draft_id}/preview")
async def preview_assessment_draft(draft_id: str, user: CurrentUser = Depends(require_author)):
    draft = await require_owned("assessment_drafts", draft_id, user)
    questions = await database.value.question_drafts.find({"assessment_draft_id": draft_id}).to_list(500)
    by_id = {question["_id"]: question for question in questions}
    items = []
    for position, question_id in enumerate(draft.get("question_order", []), start=1):
        question = by_id.get(question_id)
        if question:
            items.append(
                {
                    "position": position,
                    "question_draft_id": question_id,
                    "question_type": question["question_type"],
                    "stem_doc": question["stem_doc"],
                    "options": question["options"],
                    "points": float(question.get("scoring_rule", {}).get("points", 1)),
                }
            )
    return {"assessment_draft_id": draft_id, "title": draft["title"], "layout_doc": draft["layout_doc"], "items": items}


@router.get("/assessment-drafts/{draft_id}/difficulty-analysis")
async def analyze_assessment_difficulty(draft_id: str, user: CurrentUser = Depends(require_author)):
    draft = await require_owned("assessment_drafts", draft_id, user)
    questions = await database.value.question_drafts.find(
        {"assessment_draft_id": draft_id, "owner_id": user.id}
    ).to_list(500)
    question_ids = [question["_id"] for question in questions]
    predictions = await database.value.difficulty_estimates.find(
        {
            "question_draft_id": {"$in": question_ids},
            "owner_id": user.id,
            "revealed_at": {"$ne": None},
            "$or": [{"predictor_kind": "structured"}, {"predictor_kind": {"$exists": False}}],
        }
    ).sort("created_at", -1).to_list(5000)
    targets = await database.value.difficulty_targets.find(
        {"question_draft_id": {"$in": question_ids}, "owner_id": user.id}
    ).sort("created_at", -1).to_list(5000)
    judgments = await database.value.teacher_judgments.find(
        {"question_draft_id": {"$in": question_ids}, "teacher_id": user.id}
    ).sort("created_at", -1).to_list(5000)
    version_ids = [question["frozen_version_id"] for question in questions if question.get("frozen_version_id")]
    calibrations = await database.value.calibrations.find(
        {"question_version_id": {"$in": version_ids}, "status": "calibrated"}
    ).sort("created_at", -1).to_list(5000)
    current_revision = {question["_id"]: question["revision"] for question in questions}
    latest_predictions = {}
    latest_targets = {}
    latest_judgments = {}
    latest_calibrations = {}
    for prediction in predictions:
        question_id = prediction["question_draft_id"]
        if prediction.get("question_revision") == current_revision.get(question_id):
            latest_predictions.setdefault(question_id, prediction)
    for target in targets:
        question_id = target["question_draft_id"]
        if target.get("question_revision") == current_revision.get(question_id):
            latest_targets.setdefault(question_id, target)
    for judgment in judgments:
        question_id = judgment["question_draft_id"]
        if judgment.get("question_revision") == current_revision.get(question_id):
            latest_judgments.setdefault(question_id, judgment)
    for calibration in calibrations:
        latest_calibrations.setdefault(calibration["question_version_id"], calibration)
    predicted_distribution = {str(level): 0 for level in range(1, 6)}
    target_distribution = {str(level): 0 for level in range(1, 6)}
    teacher_distribution = {str(level): 0 for level in range(1, 6)}
    calibrated_distribution = {str(level): 0 for level in range(1, 6)}
    for prediction in latest_predictions.values():
        predicted_distribution[str(difficulty_level(float(prediction["predicted_difficulty"])))] += 1
    for target in latest_targets.values():
        target_distribution[str(difficulty_level(float(target["target_difficulty"])))] += 1
    for judgment in latest_judgments.values():
        teacher_distribution[str(difficulty_level(float(judgment["estimated_difficulty"])))] += 1
    for calibration in latest_calibrations.values():
        calibrated_distribution[str(difficulty_level(float(calibration["difficulty"])))] += 1
    blueprint = None
    expected_distribution = None
    recommendations = []
    if draft.get("blueprint_id"):
        blueprint = await require_owned("blueprints", draft["blueprint_id"], user)
        expected_distribution = blueprint.get("difficulty_distribution")
        for level in range(1, 6):
            key = str(level)
            delta = int(expected_distribution.get(key, 0)) - predicted_distribution[key]
            if delta:
                recommendations.append(
                    {
                        "difficulty_level": level,
                        "delta": delta,
                        "action": "add_or_raise" if delta > 0 else "reduce_or_lower",
                    }
                )
    unresolved = [question_id for question_id in question_ids if question_id not in latest_predictions]
    return {
        "assessment_draft_id": draft_id,
        "question_count": len(questions),
        "predicted_distribution": predicted_distribution,
        "target_distribution": target_distribution,
        "teacher_distribution": teacher_distribution,
        "calibrated_distribution": calibrated_distribution,
        "blueprint_distribution": expected_distribution,
        "unresolved_question_draft_ids": unresolved,
        "research_blind_hidden_count": len(unresolved) if draft.get("research_blind_mode") else 0,
        "recommendations": recommendations,
        "requires_teacher_acceptance": True,
        "mutated": False,
    }


@router.post("/assessment-drafts/{draft_id}/learner-fit")
async def analyze_assessment_learner_fit(
    draft_id: str,
    payload: LearnerFitInput,
    user: CurrentUser = Depends(require_author),
):
    draft = await require_owned("assessment_drafts", draft_id, user)
    questions = await database.value.question_drafts.find(
        {"assessment_draft_id": draft_id, "owner_id": user.id}
    ).to_list(500)
    by_id = {question["_id"]: question for question in questions}
    ordered = [by_id[question_id] for question_id in draft.get("question_order", []) if question_id in by_id]
    question_ids = [question["_id"] for question in ordered]
    version_ids = [question["frozen_version_id"] for question in ordered if question.get("frozen_version_id")]
    predictions, targets, calibrations = await asyncio.gather(
        database.value.difficulty_estimates.find(
            {
                "question_draft_id": {"$in": question_ids},
                "owner_id": user.id,
                "revealed_at": {"$ne": None},
                "$or": [{"predictor_kind": "structured"}, {"predictor_kind": {"$exists": False}}],
            }
        ).sort("created_at", -1).to_list(5000),
        database.value.difficulty_targets.find(
            {"question_draft_id": {"$in": question_ids}, "owner_id": user.id}
        ).sort("created_at", -1).to_list(5000),
        database.value.calibrations.find(
            {"question_version_id": {"$in": version_ids}, "status": "calibrated"}
        ).sort("created_at", -1).to_list(5000),
    )
    current_revision = {question["_id"]: question["revision"] for question in ordered}
    latest_predictions = {}
    latest_targets = {}
    latest_calibrations = {}
    for prediction in predictions:
        question_id = prediction["question_draft_id"]
        if prediction.get("question_revision") == current_revision.get(question_id):
            latest_predictions.setdefault(question_id, prediction)
    for target in targets:
        question_id = target["question_draft_id"]
        if target.get("question_revision") == current_revision.get(question_id):
            latest_targets.setdefault(question_id, target)
    for calibration in calibrations:
        latest_calibrations.setdefault(calibration["question_version_id"], calibration)
    items = []
    for question in ordered:
        calibration = latest_calibrations.get(question.get("frozen_version_id"))
        prediction = latest_predictions.get(question["_id"])
        target = latest_targets.get(question["_id"])
        if calibration and calibration.get("difficulty") is not None:
            standard_error = float(calibration.get("standard_error") or 1)
            confidence = max(0.35, min(0.98, 1 - standard_error / 2))
            if calibration.get("drift_flag"):
                confidence *= 0.6
            difficulty = float(calibration["difficulty"])
            source = "calibrated"
        elif prediction and prediction.get("predicted_difficulty") is not None:
            difficulty = float(prediction["predicted_difficulty"])
            confidence = float(prediction.get("confidence", 0.35))
            source = "predicted"
        elif target and target.get("target_difficulty") is not None:
            difficulty = float(target["target_difficulty"])
            confidence = 0.3
            source = "teacher_target"
        else:
            difficulty = 3.0
            confidence = 0.15
            source = "reference_population"
        items.append(
            {
                **question,
                "question_draft_id": question["_id"],
                "question_version_id": question.get("frozen_version_id"),
                "difficulty": difficulty,
                "confidence": confidence,
                "difficulty_source": source,
            }
        )
    target_learner = deepcopy(payload.target_learner)
    blueprint = None
    if draft.get("blueprint_id"):
        blueprint = await database.value.blueprints.find_one(
            {"_id": draft["blueprint_id"], "owner_id": user.id}
        )
    if not target_learner:
        target_learner = deepcopy((blueprint or {}).get("target_learner") or draft.get("context", {}).get("target_learner") or {})
    if not target_learner.get("ability_band"):
        target_learner["ability_band"] = [2.0, 4.0]
        target_learner["source"] = "target_program_baseline"
    target_learner.setdefault("confidence", 0.4)
    try:
        validated_target = LearnerFitInput(
            target_learner=target_learner,
            target_success_range=payload.target_success_range,
        )
    except ValueError:
        raise HTTPException(status_code=422, detail={"code": "learner_fit_target_invalid"})
    result = evaluate_learner_fit(items, validated_target.target_learner, validated_target.target_success_range)
    result["assessment_draft_id"] = draft_id
    result["mutated"] = False
    result["requires_teacher_acceptance"] = True
    await audit(
        user.id,
        "assessment_learner_fit_analyzed",
        "AssessmentDraft",
        draft_id,
        {
            "question_count": result["question_count"],
            "low_evidence_warning": result["low_evidence_warning"],
            "target_source": result["target_learner"]["source"],
        },
    )
    return result


def optimizer_item(
    entity: dict[str, Any],
    source_kind: str,
    source_question_id: str | None = None,
    calibrated_difficulty: float | None = None,
    exposure_count: int = 0,
):
    projection = entity.get("plain_text_projection") or text_projection(entity.get("stem_doc", {}))
    curriculum_nodes = []
    for link in entity.get("curriculum_links", []):
        curriculum_nodes.extend(
            str(value)
            for key in ["curriculum_node_id", "chapter_id", "lesson_id", "section_id"]
            if (value := link.get(key))
        )
    predicted = predict_difficulty(entity, "blueprint_optimizer_v1")
    item_difficulty = calibrated_difficulty if calibrated_difficulty is not None else float(predicted["predicted_difficulty"])
    validity_review = entity.get("validity_review") or {}
    content_fingerprint = hashlib.sha256(projection.casefold().strip().encode()).hexdigest()
    return {
        "id": f"{source_kind}:{entity['_id']}",
        "entity_id": entity["_id"],
        "source_kind": source_kind,
        "source_question_id": source_question_id,
        "question_type": entity.get("question_type"),
        "cognitive_level": entity.get("cognitive_level") or "",
        "difficulty_level": difficulty_level(item_difficulty),
        "difficulty_source": "calibrated" if calibrated_difficulty is not None else "structured_cold_start",
        "concept_ids": entity.get("concept_ids", []),
        "skill_ids": entity.get("skill_ids", []),
        "curriculum_node_ids": curriculum_nodes,
        "locked": bool(entity.get("locked")) if source_kind == "draft" else False,
        "valid": not validate_question(entity)["blockers"],
        "status": entity.get("status", "active"),
        "duplicate_group": source_question_id or content_fingerprint,
        "duplicate_groups": [value for value in [source_question_id, content_fingerprint] if value],
        "exposure_count": exposure_count,
        "construct_risk": len(validity_review.get("risk_flags", [])) + int(validity_review.get("status") == "rejected"),
    }


@router.post("/assessment-drafts/{draft_id}/rebalance", status_code=201)
async def propose_assessment_rebalance(
    draft_id: str,
    payload: AssessmentRebalanceInput,
    user: CurrentUser = Depends(require_author),
):
    draft = await require_owned("assessment_drafts", draft_id, user)
    existing = await database.value.assessment_rebalance_proposals.find_one(
        {"owner_id": user.id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        if existing.get("assessment_draft_id") != draft_id or existing.get("base_revision") != payload.expected_revision:
            raise HTTPException(status_code=409, detail={"code": "rebalance_idempotency_conflict"})
        return existing
    if draft["revision"] != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "revision_conflict", "current_revision": draft["revision"]})
    if not draft.get("blueprint_id"):
        raise HTTPException(status_code=422, detail={"code": "assessment_blueprint_required"})
    blueprint = await require_owned("blueprints", draft["blueprint_id"], user)
    blueprint_validation = validate_blueprint(blueprint)
    if not blueprint_validation["valid"]:
        raise HTTPException(status_code=422, detail={"code": "blueprint_invalid", "validation": blueprint_validation})
    current = await database.value.question_drafts.find(
        {"assessment_draft_id": draft_id, "owner_id": user.id}
    ).to_list(1000)
    current_question_ids = {
        value
        for item in current
        for value in [item.get("question_id"), item.get("bank_source_question_id")]
        if value
    }
    current_source_questions = await database.value.questions.find(
        {"owner_id": user.id, "_id": {"$in": list(current_question_ids)}}
    ).to_list(1000)
    source_version_by_question = {
        item["_id"]: item.get("current_version_id")
        for item in current_source_questions
        if item.get("current_version_id")
    }
    bank_questions = await database.value.questions.find(
        {"owner_id": user.id, "status": "active", "_id": {"$nin": list(current_question_ids)}}
    ).limit(1000).to_list(1000)
    bank_version_ids = [item["current_version_id"] for item in bank_questions if item.get("current_version_id")]
    current_version_by_draft = {
        item["_id"]: item.get("frozen_version_id")
        or source_version_by_question.get(item.get("question_id") or item.get("bank_source_question_id"))
        for item in current
    }
    candidate_version_ids = list(
        {
            *bank_version_ids,
            *[version_id for version_id in current_version_by_draft.values() if version_id],
        }
    )
    bank_versions = await database.value.question_versions.find(
        {"_id": {"$in": bank_version_ids}, "owner_id": user.id}
    ).to_list(1000)
    exposure_rows = await database.value.responses.aggregate(
        [
            {"$match": {"question_version_id": {"$in": candidate_version_ids}, "is_first_exposure": True}},
            {"$group": {"_id": "$question_version_id", "count": {"$sum": 1}}},
        ]
    ).to_list(1000)
    calibration_rows = await database.value.calibrations.find(
        {"question_version_id": {"$in": candidate_version_ids}, "status": "calibrated"}
    ).sort("created_at", -1).to_list(5000)
    exposure_by_version = {row["_id"]: int(row["count"]) for row in exposure_rows}
    calibration_by_version = {}
    for row in calibration_rows:
        calibration_by_version.setdefault(row["question_version_id"], row)
    question_by_version = {item["current_version_id"]: item["_id"] for item in bank_questions if item.get("current_version_id")}
    candidates = [
        optimizer_item(
            item,
            "draft",
            item.get("question_id") or item.get("bank_source_question_id"),
            calibration_by_version.get(current_version_by_draft.get(item["_id"]), {}).get("difficulty"),
            exposure_by_version.get(current_version_by_draft.get(item["_id"]), 0),
        )
        for item in current
    ]
    candidates.extend(
        optimizer_item(
            version,
            "bank",
            question_by_version.get(version["_id"]),
            calibration_by_version.get(version["_id"], {}).get("difficulty"),
            exposure_by_version.get(version["_id"], 0),
        )
        for version in bank_versions
    )
    ability_band = blueprint.get("target_learner", {}).get("ability_band")
    if isinstance(ability_band, list) and len(ability_band) == 2:
        target_center = (float(ability_band[0]) + float(ability_band[1])) / 2
        for candidate in candidates:
            candidate["learner_fit_penalty"] = abs(float(candidate["difficulty_level"]) - target_center)
    result = optimize_blueprint(candidates, blueprint)
    selected = result["selected"]
    current_by_id = {item["_id"]: item for item in current}
    proposal = {
        "_id": new_id("ARP"),
        "assessment_draft_id": draft_id,
        "blueprint_id": blueprint["_id"],
        "owner_id": user.id,
        "idempotency_key": payload.idempotency_key,
        "base_revision": draft["revision"],
        "before": [
            {"question_draft_id": question_id, "locked": bool(current_by_id.get(question_id, {}).get("locked"))}
            for question_id in draft.get("question_order", [])
        ],
        "before_question_snapshots": deepcopy(current),
        "after": selected,
        "why": result["audit"],
        "target_effect": {
            "difficulty_distribution": blueprint["difficulty_distribution"],
            "question_type_constraints": blueprint.get("question_type_constraints", {}),
            "coverage_constraints": blueprint.get("coverage_constraints", []),
            "maximum_exposure_count": blueprint.get("maximum_exposure_count"),
        },
        "construct_check": {"passed": result["feasible"] and all(item.get("valid") for item in selected)},
        "infeasibility": result["gaps"],
        "status": "proposed" if result["feasible"] else "infeasible",
        "created_at": now(),
        "updated_at": now(),
    }
    try:
        await database.value.assessment_rebalance_proposals.insert_one(proposal)
    except DuplicateKeyError:
        existing = await database.value.assessment_rebalance_proposals.find_one(
            {"owner_id": user.id, "idempotency_key": payload.idempotency_key}
        )
        if existing and existing.get("assessment_draft_id") == draft_id and existing.get("base_revision") == payload.expected_revision:
            return existing
        raise HTTPException(status_code=409, detail={"code": "rebalance_idempotency_conflict"})
    await audit(
        user.id,
        "assessment_rebalance_proposed",
        "AssessmentRebalanceProposal",
        proposal["_id"],
        {"feasible": result["feasible"], "selected_count": len(selected)},
    )
    return proposal


@router.post("/assessment-drafts/{draft_id}/rebalance-proposals/{proposal_id}/approve")
async def approve_assessment_rebalance(
    draft_id: str,
    proposal_id: str,
    user: CurrentUser = Depends(require_author),
):
    proposal = await require_owned("assessment_rebalance_proposals", proposal_id, user)
    if proposal.get("assessment_draft_id") != draft_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất cân bằng")
    if proposal.get("status") == "approved":
        return {
            "proposal_id": proposal_id,
            "assessment_draft_revision": proposal.get("applied_revision"),
            "question_order": proposal.get("applied_question_order", []),
        }
    if proposal.get("status") != "proposed":
        raise HTTPException(status_code=409, detail={"code": "rebalance_proposal_not_pending"})
    bank_entries = [item for item in proposal["after"] if item["source_kind"] == "bank"]
    bank_version_ids = [item["entity_id"] for item in bank_entries]
    bank_versions = await database.value.question_versions.find(
        {"_id": {"$in": bank_version_ids}, "owner_id": user.id}
    ).to_list(1000)
    bank_by_id = {item["_id"]: item for item in bank_versions}
    if len(bank_by_id) != len(set(bank_version_ids)):
        raise HTTPException(status_code=409, detail={"code": "rebalance_candidate_changed"})
    draft_fields = {
        "question_type",
        "stem_doc",
        "options",
        "answer_key",
        "solution_doc",
        "scoring_rule",
        "curriculum_links",
        "concept_ids",
        "skill_ids",
        "tags",
        "cognitive_level",
        "construct",
        "source_evidence",
        "locked",
    }
    created_by_version = {}
    created_documents = []
    for entry in bank_entries:
        version = bank_by_id[entry["entity_id"]]
        question_data = {key: deepcopy(version.get(key)) for key in draft_fields}
        question_data["authoring_source"] = "hybrid"
        question_data["bank_source_question_id"] = entry.get("source_question_id")
        question_data["locked"] = False
        version_id = version["_id"]
        deterministic_id = f"QD-{hashlib.sha256(f'rebalance:{draft_id}:{version_id}'.encode()).hexdigest()[:32]}"
        created_documents.append(question_draft_document(draft_id, question_data, user.id, deterministic_id))
        created_by_version[version_id] = deterministic_id
    question_order = [
        entry["entity_id"] if entry["source_kind"] == "draft" else created_by_version[entry["entity_id"]]
        for entry in proposal["after"]
    ]
    selected_current_ids = {
        entry["entity_id"]
        for entry in proposal["after"]
        if entry["source_kind"] == "draft"
    }
    removed_documents = [
        snapshot
        for snapshot in proposal.get("before_question_snapshots", [])
        if snapshot["_id"] not in selected_current_ids
    ]
    removed_ids = [item["_id"] for item in removed_documents]
    approved_at = now()

    async def approve_transaction(session):
        current_proposal = await database.value.assessment_rebalance_proposals.find_one(
            {"_id": proposal_id, "owner_id": user.id},
            session=session,
        )
        if not current_proposal or current_proposal.get("status") != "proposed":
            raise HTTPException(status_code=409, detail={"code": "rebalance_proposal_not_pending"})
        current_draft = await database.value.assessment_drafts.find_one(
            {"_id": draft_id, "owner_id": user.id},
            session=session,
        )
        if not current_draft or current_draft.get("revision") != proposal["base_revision"]:
            raise HTTPException(
                status_code=409,
                detail={"code": "revision_conflict", "current_revision": current_draft.get("revision") if current_draft else None},
            )
        if created_documents:
            await database.value.question_drafts.insert_many(created_documents, session=session)
        if removed_ids:
            await database.value.question_drafts.delete_many(
                {"_id": {"$in": removed_ids}, "assessment_draft_id": draft_id, "owner_id": user.id},
                session=session,
            )
        updated = await database.value.assessment_drafts.find_one_and_update(
            {"_id": draft_id, "owner_id": user.id, "revision": proposal["base_revision"]},
            {"$set": {"question_order": question_order, "updated_at": approved_at}, "$inc": {"revision": 1}},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        if not updated:
            raise HTTPException(status_code=409, detail={"code": "revision_conflict"})
        proposal_update = await database.value.assessment_rebalance_proposals.update_one(
            {"_id": proposal_id, "owner_id": user.id, "status": "proposed"},
            {"$set": {"status": "approved", "approved_at": approved_at, "applied_revision": updated["revision"], "applied_question_order": question_order, "applied_created_question_ids": [item["_id"] for item in created_documents], "applied_removed_question_ids": removed_ids, "updated_at": approved_at}},
            session=session,
        )
        if proposal_update.modified_count != 1:
            raise HTTPException(status_code=409, detail={"code": "rebalance_proposal_not_pending"})
        return updated

    try:
        async with await database.client.start_session() as session:
            updated = await session.with_transaction(approve_transaction)
    except DuplicateKeyError as error:
        raise HTTPException(status_code=409, detail={"code": "rebalance_candidate_already_added"}) from error
    await audit(user.id, "assessment_rebalance_approved", "AssessmentRebalanceProposal", proposal_id)
    return {"proposal_id": proposal_id, "assessment_draft": updated, "question_order": question_order}


@router.post("/assessment-drafts/{draft_id}/rebalance-proposals/{proposal_id}/undo")
async def undo_assessment_rebalance(
    draft_id: str,
    proposal_id: str,
    user: CurrentUser = Depends(require_author),
):
    proposal = await require_owned("assessment_rebalance_proposals", proposal_id, user)
    if proposal.get("assessment_draft_id") != draft_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất cân bằng")
    if proposal.get("status") != "approved":
        raise HTTPException(status_code=409, detail={"code": "rebalance_proposal_not_approved"})
    published = await database.value.assessments.find_one(
        {"assessment_draft_id": draft_id, "owner_id": user.id, "current_version_id": {"$ne": None}}
    )
    if published:
        raise HTTPException(status_code=409, detail={"code": "rebalance_undo_after_publish_forbidden"})
    restored_order = [item["question_draft_id"] for item in proposal.get("before", [])]
    snapshots_by_id = {item["_id"]: item for item in proposal.get("before_question_snapshots", [])}
    restored_documents = [
        deepcopy(snapshots_by_id[question_id])
        for question_id in proposal.get("applied_removed_question_ids", [])
        if question_id in snapshots_by_id
    ]
    undone_at = now()

    async def undo_transaction(session):
        current_proposal = await database.value.assessment_rebalance_proposals.find_one(
            {"_id": proposal_id, "owner_id": user.id},
            session=session,
        )
        if not current_proposal or current_proposal.get("status") != "approved":
            raise HTTPException(status_code=409, detail={"code": "rebalance_proposal_not_approved"})
        published_in_transaction = await database.value.assessments.find_one(
            {"assessment_draft_id": draft_id, "owner_id": user.id, "current_version_id": {"$ne": None}},
            session=session,
        )
        if published_in_transaction:
            raise HTTPException(status_code=409, detail={"code": "rebalance_undo_after_publish_forbidden"})
        current_draft = await database.value.assessment_drafts.find_one(
            {"_id": draft_id, "owner_id": user.id},
            session=session,
        )
        if not current_draft or current_draft.get("revision") != proposal.get("applied_revision"):
            raise HTTPException(
                status_code=409,
                detail={"code": "revision_conflict", "current_revision": current_draft.get("revision") if current_draft else None},
            )
        created_ids = proposal.get("applied_created_question_ids", [])
        if created_ids:
            await database.value.question_drafts.delete_many(
                {"_id": {"$in": created_ids}, "assessment_draft_id": draft_id, "owner_id": user.id},
                session=session,
            )
        if restored_documents:
            await database.value.question_drafts.insert_many(restored_documents, session=session)
        updated = await database.value.assessment_drafts.find_one_and_update(
            {"_id": draft_id, "owner_id": user.id, "revision": proposal["applied_revision"]},
            {"$set": {"question_order": restored_order, "updated_at": undone_at}, "$inc": {"revision": 1}},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        if not updated:
            raise HTTPException(status_code=409, detail={"code": "revision_conflict"})
        proposal_update = await database.value.assessment_rebalance_proposals.update_one(
            {"_id": proposal_id, "owner_id": user.id, "status": "approved"},
            {"$set": {"status": "undone", "undone_at": undone_at, "undo_revision": updated["revision"], "updated_at": undone_at}},
            session=session,
        )
        if proposal_update.modified_count != 1:
            raise HTTPException(status_code=409, detail={"code": "rebalance_proposal_not_approved"})
        return updated

    try:
        async with await database.client.start_session() as session:
            updated = await session.with_transaction(undo_transaction)
    except DuplicateKeyError as error:
        raise HTTPException(status_code=409, detail={"code": "rebalance_undo_identity_conflict"}) from error
    await audit(user.id, "assessment_rebalance_undone", "AssessmentRebalanceProposal", proposal_id)
    return {"proposal_id": proposal_id, "assessment_draft": updated, "question_order": restored_order}


@router.post("/assessment-drafts/{draft_id}/rebalance-proposals/{proposal_id}/reject")
async def reject_assessment_rebalance(
    draft_id: str,
    proposal_id: str,
    user: CurrentUser = Depends(require_author),
):
    proposal = await require_owned("assessment_rebalance_proposals", proposal_id, user)
    if proposal.get("assessment_draft_id") != draft_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất cân bằng")
    rejected = await database.value.assessment_rebalance_proposals.find_one_and_update(
        {"_id": proposal_id, "owner_id": user.id, "status": "proposed"},
        {"$set": {"status": "rejected", "rejected_at": now(), "updated_at": now()}},
        return_document=ReturnDocument.AFTER,
    )
    if not rejected:
        raise HTTPException(status_code=409, detail={"code": "rebalance_proposal_not_pending"})
    await audit(user.id, "assessment_rebalance_rejected", "AssessmentRebalanceProposal", proposal_id)
    return rejected


@router.post("/assessment-drafts/{draft_id}/freeze", status_code=201)
async def freeze_assessment_draft(draft_id: str, user: CurrentUser = Depends(require_author)):
    draft = await require_owned("assessment_drafts", draft_id, user)
    validation = await validate_assessment_draft(draft_id, user)
    if not validation["valid"]:
        raise HTTPException(status_code=422, detail={"code": "assessment_validation_failed", "validation": validation})
    frozen = {
        "_id": new_id("ADF"),
        "assessment_draft_id": draft_id,
        "owner_id": user.id,
        "revision": draft["revision"],
        "title": draft["title"],
        "context": deepcopy(draft.get("context", {})),
        "layout_doc": deepcopy(draft.get("layout_doc", {})),
        "question_order": deepcopy(draft.get("question_order", [])),
        "blueprint_id": draft.get("blueprint_id"),
        "created_at": now(),
    }
    await database.value.assessment_draft_freezes.insert_one(frozen)
    await audit(user.id, "assessment_draft_frozen", "AssessmentDraftFreeze", frozen["_id"])
    return frozen


@router.get("/question-drafts/{question_draft_id}")
async def get_question_draft(question_draft_id: str, user: CurrentUser = Depends(require_author)):
    return await require_owned("question_drafts", question_draft_id, user)


@router.patch("/question-drafts/{question_draft_id}")
async def patch_question_draft(
    question_draft_id: str,
    payload: QuestionDraftPatch,
    user: CurrentUser = Depends(require_author),
):
    current = await require_owned("question_drafts", question_draft_id, user)
    changes = payload.model_dump(by_alias=True)
    content_fields = {
        "question_type",
        "stem_doc",
        "options",
        "answer_key",
        "solution_doc",
        "scoring_rule",
        "curriculum_links",
        "concept_ids",
        "skill_ids",
        "tags",
        "cognitive_level",
        "construct",
        "source_evidence",
    }
    if any(changes.get(field) is not None for field in content_fields):
        changes["validity_review"] = {"status": "pending", "risk_flags": []}
    changed_fields = sorted(
        field
        for field in content_fields.union({"locked"})
        if changes.get(field) is not None and changes.get(field) != current.get(field)
    )
    updated = await optimistic_patch("question_drafts", question_draft_id, user.id, payload.expected_revision, changes)
    if changed_fields:
        await persist_teacher_profile_event(
            user.id,
            "manual_edit",
            {"question_draft_id": question_draft_id, "fields": changed_fields},
            f"edit-{question_draft_id}-{updated['revision']}",
        )
    if "question_type" in changed_fields:
        await persist_teacher_profile_event(
            user.id,
            "question_type_selected",
            {"question_type": updated["question_type"], "question_draft_id": question_draft_id},
            f"question-type-{question_draft_id}-{updated['revision']}",
        )
    await audit(user.id, "question_draft_updated", "QuestionDraft", question_draft_id, {"revision": updated["revision"]})
    return updated


@router.delete("/question-drafts/{question_draft_id}", status_code=204)
async def delete_question_draft(question_draft_id: str, user: CurrentUser = Depends(require_author)):
    question = await require_owned("question_drafts", question_draft_id, user)
    await database.value.question_drafts.delete_one({"_id": question_draft_id, "owner_id": user.id})
    await database.value.assessment_drafts.update_one(
        {"_id": question["assessment_draft_id"], "owner_id": user.id},
        {"$pull": {"question_order": question_draft_id}, "$inc": {"revision": 1}, "$set": {"updated_at": now()}},
    )
    await audit(user.id, "question_draft_deleted", "QuestionDraft", question_draft_id)


@router.post("/question-drafts/{question_draft_id}/restore-version/{version_id}")
async def restore_question_draft_version(
    question_draft_id: str,
    version_id: str,
    user: CurrentUser = Depends(require_author),
):
    draft = await require_owned("question_drafts", question_draft_id, user)
    version = await require_owned("question_versions", version_id, user)
    if not draft.get("question_id") or version.get("question_id") != draft.get("question_id"):
        raise HTTPException(status_code=409, detail={"code": "question_version_lineage_mismatch"})
    restore_fields = {
        "question_type",
        "stem_doc",
        "options",
        "answer_key",
        "solution_doc",
        "scoring_rule",
        "curriculum_links",
        "concept_ids",
        "skill_ids",
        "tags",
        "cognitive_level",
        "construct",
        "source_evidence",
        "locked",
    }
    restored = await database.value.question_drafts.find_one_and_update(
        {"_id": question_draft_id, "owner_id": user.id, "revision": draft["revision"]},
        {
            "$set": {
                **{
                    field: deepcopy(version.get(field) or []) if field == "tags" else deepcopy(version.get(field))
                    for field in restore_fields
                },
                "status": "draft",
                "frozen_version_id": None,
                "frozen_revision": None,
                "validity_review": {"status": "pending", "risk_flags": []},
                "restored_from_version_id": version_id,
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not restored:
        raise HTTPException(status_code=409, detail={"code": "revision_conflict"})
    await audit(user.id, "question_draft_version_restored", "QuestionDraft", question_draft_id, {"source_version_id": version_id, "revision": restored["revision"]})
    return restored


@router.post("/question-drafts/{question_draft_id}/duplicate", status_code=201)
async def duplicate_question_draft(question_draft_id: str, user: CurrentUser = Depends(require_author)):
    source = await require_owned("question_drafts", question_draft_id, user)
    duplicate = deepcopy(source)
    duplicate["_id"] = new_id("QD")
    duplicate["question_id"] = None
    duplicate["revision"] = 1
    duplicate["authoring_source"] = "hybrid"
    duplicate["status"] = "draft"
    duplicate["frozen_version_id"] = None
    duplicate["frozen_revision"] = None
    duplicate["validity_review"] = {"status": "pending", "risk_flags": []}
    duplicate["cloned_from_question_draft_id"] = question_draft_id
    for key in ["validation", "reviewed_at", "reviewer_note", "import_job_id", "import_candidate_id"]:
        duplicate.pop(key, None)
    duplicate["created_at"] = now()
    duplicate["updated_at"] = now()
    await database.value.question_drafts.insert_one(duplicate)
    await database.value.assessment_drafts.update_one(
        {"_id": duplicate["assessment_draft_id"], "owner_id": user.id},
        {"$push": {"question_order": duplicate["_id"]}, "$inc": {"revision": 1}, "$set": {"updated_at": now()}},
    )
    await audit(user.id, "question_draft_duplicated", "QuestionDraft", duplicate["_id"], {"source_id": question_draft_id})
    return duplicate


@router.post("/question-drafts/{question_draft_id}/validate")
async def validate_question_draft(question_draft_id: str, user: CurrentUser = Depends(require_author)):
    question = await require_owned("question_drafts", question_draft_id, user)
    result = await validate_owned_question(question, user)
    await database.value.question_drafts.update_one(
        {"_id": question_draft_id},
        {"$set": {"validation": result, "status": "prevalidated" if not result["blockers"] else "needs_revision", "updated_at": now()}},
    )
    metrics.increment("question_validation_failures", len(result["blockers"]))
    return result


@router.post("/question-drafts/{question_draft_id}/validity-review")
async def record_validity_review(
    question_draft_id: str,
    payload: ValidityReviewInput,
    user: CurrentUser = Depends(require_author),
):
    question = await require_owned("question_drafts", question_draft_id, user)
    review = {
        **payload.model_dump(),
        "reviewed_by": user.id,
        "reviewed_revision": question["revision"],
        "reviewed_at": now(),
    }
    updated = await database.value.question_drafts.find_one_and_update(
        {"_id": question_draft_id, "owner_id": user.id, "revision": question["revision"]},
        {"$set": {"validity_review": review, "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "revision_conflict"})
    await audit(
        user.id,
        "question_validity_reviewed",
        "QuestionDraft",
        question_draft_id,
        {"status": payload.status, "risk_flags": payload.risk_flags},
    )
    return updated


@router.post("/question-drafts/{question_draft_id}/teacher-estimate", status_code=201)
async def record_teacher_estimate(
    question_draft_id: str,
    payload: TeacherEstimateInput,
    user: CurrentUser = Depends(require_author),
):
    question = await require_owned("question_drafts", question_draft_id, user)
    prediction_visible = bool(
        await database.value.difficulty_estimates.find_one(
            {
                "question_draft_id": question_draft_id,
                "question_revision": question["revision"],
                "revealed_at": {"$ne": None},
            }
        )
    )
    judgment = payload.model_dump()
    judgment.update(
        {
            "_id": new_id("TDJ"),
            "question_draft_id": question_draft_id,
            "question_version_id": None,
            "question_revision": question["revision"],
            "teacher_id": user.id,
            "ai_prediction_visible_before_estimate": prediction_visible,
            "created_at": now(),
        }
    )
    if question.get("assessment_draft_id"):
        assessment_draft = await database.value.assessment_drafts.find_one({"_id": question["assessment_draft_id"]})
        if assessment_draft and assessment_draft.get("research_blind_mode") and prediction_visible:
            judgment["research_eligible"] = False
        else:
            judgment["research_eligible"] = True
    await database.value.teacher_judgments.insert_one(judgment)
    await audit(user.id, "teacher_estimate_recorded", "TeacherDifficultyJudgment", judgment["_id"])
    return judgment


@router.post("/question-drafts/{question_draft_id}/predict-difficulty", status_code=201)
async def predict_question_difficulty(
    question_draft_id: str,
    payload: DifficultyPredictionInput,
    user: CurrentUser = Depends(require_author),
):
    question = await require_owned("question_drafts", question_draft_id, user)
    assessment_draft = await database.value.assessment_drafts.find_one({"_id": question["assessment_draft_id"]})
    if assessment_draft and assessment_draft.get("research_blind_mode"):
        judgment = await database.value.teacher_judgments.find_one(
            {
                "question_draft_id": question_draft_id,
                "question_revision": question["revision"],
                "teacher_id": user.id,
            },
            sort=[("created_at", -1)],
        )
        if not judgment:
            raise HTTPException(status_code=409, detail={"code": "teacher_estimate_required_before_ai_reveal"})
    existing = await database.value.difficulty_estimates.find_one(
        {
            "question_draft_id": question_draft_id,
            "question_revision": question["revision"],
            "model_version": payload.model_version,
            "predictor_kind": payload.prediction_kind,
        },
        sort=[("created_at", -1)],
    )
    if existing:
        if existing.get("revealed_at") is None:
            await database.value.difficulty_estimates.update_one(
                {"_id": existing["_id"]},
                {"$set": {"revealed_at": now()}},
            )
            existing["revealed_at"] = now()
        metrics.set("difficulty_prediction_confidence", float(existing.get("confidence", 0)))
        return await prediction_with_empirical_context(existing, question)
    historical_items = await similar_historical_items(question, user)
    if payload.prediction_kind == "llm_direct":
        direct = await judge_difficulty_with_agent(question)
        confidence = float(direct["confidence"])
        estimate = {
            "method": "llm_direct_judge",
            "predictor_kind": "llm_direct",
            "predicted_difficulty": float(direct["predicted_difficulty"]),
            "ui_difficulty_level": difficulty_level(float(direct["predicted_difficulty"])),
            "confidence": confidence,
            "uncertainty": round(1 - confidence, 3),
            "reason_summary": direct.get("reason_summary", []),
            "feature_snapshot": {},
            "model_version": payload.model_version,
            "provider_model_version": direct.get("provider_model_version"),
            "feature_schema_version": "llm_direct_input_v1",
            "training_data_window": "provider_model_pretraining_unknown",
            "normalization_version": "difficulty_scale_1_5_v1",
            "status": "provisional",
        }
    else:
        estimate = predict_difficulty(question, payload.model_version, historical_items)
    prediction_identity = hashlib.sha256(
        f"{question_draft_id}:{question['revision']}:{payload.prediction_kind}:{payload.model_version}".encode()
    ).hexdigest()
    estimate["similar_historical_items"] = historical_items
    estimate.update(
        {
            "_id": f"DIF-{prediction_identity[:32]}",
            "question_draft_id": question_draft_id,
            "question_version_id": None,
            "question_revision": question["revision"],
            "owner_id": user.id,
            "revealed_at": now(),
            "created_at": now(),
        }
    )
    try:
        await database.value.difficulty_estimates.insert_one(estimate)
    except DuplicateKeyError:
        duplicate = await database.value.difficulty_estimates.find_one({"_id": estimate["_id"], "owner_id": user.id})
        if duplicate:
            return await prediction_with_empirical_context(duplicate, question)
        raise HTTPException(status_code=409, detail={"code": "difficulty_prediction_conflict"})
    await audit(
        user.id,
        "difficulty_predicted",
        "DifficultyEstimate",
        estimate["_id"],
        {"model_version": payload.model_version, "predictor_kind": payload.prediction_kind},
    )
    metrics.set("difficulty_prediction_confidence", float(estimate.get("confidence", 0)))
    return await prediction_with_empirical_context(estimate, question)


@router.post("/question-drafts/{question_draft_id}/target-difficulty", status_code=201)
async def record_difficulty_target(
    question_draft_id: str,
    payload: DifficultyTargetInput,
    user: CurrentUser = Depends(require_author),
):
    question = await require_owned("question_drafts", question_draft_id, user)
    target = payload.model_dump()
    target.update(
        {
            "_id": new_id("TGT"),
            "scope": "question",
            "question_draft_id": question_draft_id,
            "question_version_id": question.get("frozen_version_id") if question.get("frozen_revision") == question.get("revision") else None,
            "question_revision": question["revision"],
            "owner_id": user.id,
            "created_by": user.id,
            "created_at": now(),
        }
    )
    await database.value.difficulty_targets.insert_one(target)
    await persist_teacher_profile_event(
        user.id,
        "difficulty_targeted",
        {"target_difficulty": payload.target_difficulty, "question_draft_id": question_draft_id},
        f"difficulty-target-{target['_id']}",
    )
    await audit(user.id, "difficulty_target_recorded", "DifficultyTarget", target["_id"])
    return target


@router.post("/question-drafts/{question_draft_id}/freeze", status_code=201)
async def freeze_question_draft(question_draft_id: str, user: CurrentUser = Depends(require_author)):
    draft = await require_owned("question_drafts", question_draft_id, user)
    if draft.get("frozen_version_id") and draft.get("frozen_revision") == draft.get("revision"):
        existing_frozen = await database.value.question_versions.find_one(
            {"_id": draft["frozen_version_id"], "owner_id": user.id}
        )
        if existing_frozen:
            return existing_frozen
    validation = await validate_owned_question(draft, user)
    if validation["blockers"]:
        raise HTTPException(status_code=422, detail={"code": "question_validation_failed", "validation": validation})
    question_id = draft.get("question_id")
    if not question_id:
        candidate_question_id = new_id("Q")
        claimed = await database.value.question_drafts.find_one_and_update(
            {
                "_id": question_draft_id,
                "owner_id": user.id,
                "$or": [{"question_id": None}, {"question_id": {"$exists": False}}],
            },
            {"$set": {"question_id": candidate_question_id}},
            return_document=ReturnDocument.AFTER,
        )
        if claimed:
            question_id = candidate_question_id
        else:
            refreshed = await require_owned("question_drafts", question_draft_id, user)
            question_id = refreshed.get("question_id")
        if not question_id:
            raise HTTPException(status_code=409, detail={"code": "question_identity_conflict"})
    latest = await database.value.question_versions.find_one({"question_id": question_id}, sort=[("version", -1)])
    version = 1 if not latest else latest["version"] + 1
    version_id = f"{question_id}-v{version}"
    snapshot_fields = {
        "question_type",
        "authoring_source",
        "stem_doc",
        "options",
        "answer_key",
        "solution_doc",
        "scoring_rule",
        "curriculum_links",
        "concept_ids",
        "skill_ids",
        "tags",
        "cognitive_level",
        "construct",
        "source_evidence",
        "locked",
        "validity_review",
    }
    snapshot = {key: deepcopy(draft.get(key)) for key in snapshot_fields}
    snapshot.update(
        {
            "_id": version_id,
            "question_id": question_id,
            "version": version,
            "owner_id": user.id,
            "content_format": "tiptap_json_v1",
            "plain_text_projection": validation["plain_text_projection"],
            "quality_status": validation["status"],
            "quality_validation": deepcopy(validation),
            "created_by": draft["authoring_source"],
            "parent_version_id": latest["_id"] if latest else None,
            "source_draft_revision": draft["revision"],
            "created_at": now(),
        }
    )
    try:
        await database.value.question_versions.insert_one(snapshot)
    except DuplicateKeyError:
        duplicate = await database.value.question_versions.find_one(
            {"question_id": question_id, "version": version, "owner_id": user.id}
        )
        if not duplicate or duplicate.get("source_draft_revision") != draft["revision"]:
            raise HTTPException(status_code=409, detail={"code": "question_freeze_conflict"})
        snapshot = duplicate
        version_id = duplicate["_id"]
    await database.value.questions.update_one(
        {"_id": question_id},
        {
            "$set": {"owner_id": user.id, "status": "active", "current_version_id": version_id, "updated_at": now()},
            "$setOnInsert": {"created_at": now()},
        },
        upsert=True,
    )
    await database.value.question_drafts.update_one(
        {"_id": question_draft_id},
        {"$set": {"question_id": question_id, "frozen_version_id": version_id, "frozen_revision": draft["revision"], "status": "approved", "updated_at": now()}},
    )
    await database.value.teacher_judgments.update_many(
        {"question_draft_id": question_draft_id, "question_revision": draft["revision"], "question_version_id": None},
        {"$set": {"question_version_id": version_id}},
    )
    await database.value.difficulty_estimates.update_many(
        {"question_draft_id": question_draft_id, "question_revision": draft["revision"], "question_version_id": None},
        {"$set": {"question_version_id": version_id}},
    )
    await database.value.difficulty_targets.update_many(
        {"question_draft_id": question_draft_id, "question_revision": draft["revision"], "question_version_id": None},
        {"$set": {"question_version_id": version_id}},
    )
    await audit(user.id, "question_version_frozen", "QuestionVersion", version_id, {"question_draft_id": question_draft_id})
    return snapshot


@router.post("/blueprints", status_code=201)
async def create_blueprint(payload: BlueprintInput, user: CurrentUser = Depends(require_author)):
    blueprint = payload.model_dump()
    blueprint["name"] = blueprint.get("name") or f"Blueprint {blueprint['total_questions']} câu"
    blueprint.update({"_id": new_id("BP"), "owner_id": user.id, "revision": 1, "created_at": now(), "updated_at": now()})
    blueprint["validation"] = validate_blueprint(blueprint)
    await database.value.blueprints.insert_one(blueprint)
    await audit(user.id, "blueprint_created", "TestBlueprint", blueprint["_id"])
    return blueprint


@router.get("/blueprints")
async def list_blueprints(
    templates_only: bool = False,
    user: CurrentUser = Depends(require_author),
):
    query: dict[str, Any] = {"owner_id": user.id}
    if templates_only:
        query["is_template"] = True
    return await database.value.blueprints.find(query).sort("updated_at", -1).to_list(500)


@router.post("/blueprints/suggest-distribution")
async def suggest_blueprint_distribution(
    payload: BlueprintSuggestionInput,
    user: CurrentUser = Depends(require_author),
):
    distribution = {str(level): int(payload.current_distribution.get(str(level), 0)) for level in range(1, 6)}
    allocated = sum(distribution.values())
    if allocated > payload.total_questions:
        return {
            "suggested_distribution": distribution,
            "missing_or_excess": payload.total_questions - allocated,
            "valid": False,
            "requires_teacher_acceptance": True,
            "mutated": False,
        }
    order = ["3", "2", "4", "1", "5"]
    for index in range(payload.total_questions - allocated):
        distribution[order[index % len(order)]] += 1
    return {
        "suggested_distribution": distribution,
        "missing_or_excess": 0,
        "valid": True,
        "requires_teacher_acceptance": True,
        "mutated": False,
    }


@router.patch("/blueprints/{blueprint_id}")
async def patch_blueprint(
    blueprint_id: str,
    payload: BlueprintPatch,
    user: CurrentUser = Depends(require_author),
):
    updated = await optimistic_patch("blueprints", blueprint_id, user.id, payload.expected_revision, payload.model_dump())
    updated["validation"] = validate_blueprint(updated)
    await database.value.blueprints.update_one({"_id": blueprint_id}, {"$set": {"validation": updated["validation"]}})
    await audit(user.id, "blueprint_updated", "TestBlueprint", blueprint_id, {"revision": updated["revision"]})
    return updated


@router.post("/blueprints/{blueprint_id}/clone", status_code=201)
async def clone_blueprint(blueprint_id: str, user: CurrentUser = Depends(require_author)):
    source = await require_owned("blueprints", blueprint_id, user)
    clone = deepcopy(source)
    clone.update(
        {
            "_id": new_id("BP"),
            "name": f"{source.get('name') or 'Blueprint'} bản sao",
            "owner_id": user.id,
            "revision": 1,
            "is_template": False,
            "created_at": now(),
            "updated_at": now(),
            "cloned_from_blueprint_id": source["_id"],
        }
    )
    clone["validation"] = validate_blueprint(clone)
    await database.value.blueprints.insert_one(clone)
    await audit(user.id, "blueprint_cloned", "TestBlueprint", clone["_id"], {"source_blueprint_id": source["_id"]})
    return clone


@router.post("/question-drafts/{question_draft_id}/ai/revise", status_code=201)
async def propose_draft_revision(
    question_draft_id: str,
    payload: DraftAiActionInput,
    user: CurrentUser = Depends(require_author),
):
    question = await require_owned("question_drafts", question_draft_id, user)
    if question.get("locked"):
        raise HTTPException(status_code=423, detail={"code": "question_locked_from_ai"})
    proposed = deepcopy(question)
    for key in ["_id", "revision", "created_at", "updated_at", "validation", "frozen_version_id"]:
        proposed.pop(key, None)
    proposed["authoring_source"] = "hybrid"
    proposed["validity_review"] = {"status": "pending", "risk_flags": []}
    if payload.action in {"regenerate_item", "change_question_type", "increase_difficulty", "decrease_difficulty"}:
        supported_types = {
            "single_choice",
            "multiple_choice",
            "true_false",
            "matching",
            "ordering",
            "numeric",
            "symbolic_math",
            "short_answer",
            "essay",
        }
        target_type = question["question_type"]
        if payload.action == "change_question_type":
            target_type = payload.instruction.strip()
            if target_type not in supported_types:
                raise HTTPException(status_code=422, detail={"code": "target_question_type_invalid"})
            if target_type == question["question_type"]:
                raise HTTPException(status_code=422, detail={"code": "target_question_type_unchanged"})
        curriculum = (question.get("curriculum_links") or [{}])[0]
        difficulty = float(predict_difficulty(question, "revision_generation_v1")["predicted_difficulty"])
        if payload.action == "increase_difficulty":
            difficulty = min(5.0, difficulty + 1.0)
        if payload.action == "decrease_difficulty":
            difficulty = max(1.0, difficulty - 1.0)
        evidence = [
            *question.get("source_evidence", []),
            {
                "source_type": "question_draft",
                "question_draft_id": question_draft_id,
                "text": text_projection(question.get("stem_doc", {})),
            },
        ]
        uses_teacher_material = any(item.get("source_type") == "teacher_material" for item in evidence)
        if uses_teacher_material:
            await enforce_teacher_material_setting(user)
        generation = {
            "education_level": curriculum.get("education_level") or "unspecified",
            "target_program": curriculum.get("target_program") or "unspecified",
            "subject": curriculum.get("subject") or "unspecified",
            "topic": curriculum.get("topic") or question.get("construct", {}).get("primary_concept") or text_projection(question.get("stem_doc", {})),
            "chapter_id": curriculum.get("chapter_id"),
            "lesson_id": curriculum.get("lesson_id"),
            "concept_ids": question.get("concept_ids", []),
            "skill_ids": question.get("skill_ids", []),
            "tags": question.get("tags", []),
            "question_type": target_type,
            "cognitive_level": question.get("cognitive_level"),
            "source_evidence": evidence,
            "source_scope": "curriculum_only",
            "use_teacher_materials": any(item.get("source_type") == "teacher_material" for item in evidence),
        }
        model_output = await generate_with_agent(generation, difficulty, evidence)
        if uses_teacher_material:
            await persist_teacher_profile_event(
                user.id,
                "material_used",
                {"question_draft_id": question_draft_id, "action": payload.action},
                f"material-revision-{question_draft_id}-{question['revision']}-{payload.action}",
            )
        regenerated = generated_question(generation, 1, difficulty, model_output)
        for field in ["question_type", "stem_doc", "options", "answer_key", "solution_doc", "cognitive_level", "generation_provenance"]:
            proposed[field] = regenerated[field]
        proposed["scoring_rule"] = {**question.get("scoring_rule", {}), "points": float(question.get("scoring_rule", {}).get("points", 1))}
        proposed["curriculum_links"] = deepcopy(question.get("curriculum_links", []))
        proposed["concept_ids"] = deepcopy(question.get("concept_ids", []))
        proposed["skill_ids"] = deepcopy(question.get("skill_ids", []))
        proposed["tags"] = deepcopy(question.get("tags", []))
        proposed["source_evidence"] = deepcopy(question.get("source_evidence", []))
        proposed["construct"] = deepcopy(question.get("construct", {}))
        proposal_validation = validate_question(proposed)
        if proposal_validation["blockers"]:
            raise HTTPException(status_code=502, detail={"code": "ai_revision_invalid", "validation": proposal_validation})
    if payload.action == "increase_difficulty":
        proposed.setdefault("construct", {})["reasoning_steps"] = int(proposed.get("construct", {}).get("reasoning_steps", 1)) + 1
    if payload.action == "decrease_difficulty":
        proposed.setdefault("construct", {})["reasoning_steps"] = max(1, int(proposed.get("construct", {}).get("reasoning_steps", 1)) - 1)
    if payload.action == "clarify_wording":
        if not payload.instruction.strip():
            raise HTTPException(status_code=422, detail={"code": "revised_wording_required"})
        proposed["stem_doc"] = tiptap_doc(payload.instruction.strip())
    if payload.action == "regenerate_distractors":
        try:
            replacements = json.loads(payload.instruction)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail={"code": "distractor_replacements_invalid"})
        correct_ids = {
            question.get("answer_key", {}).get("option_id"),
            *question.get("answer_key", {}).get("option_ids", []),
        }
        editable_ids = {option.get("id") for option in question.get("options", [])} - correct_ids
        if not isinstance(replacements, dict) or not replacements or any(
            option_id not in editable_ids or not isinstance(text, str) or not text.strip()
            for option_id, text in replacements.items()
        ):
            raise HTTPException(status_code=422, detail={"code": "distractor_replacements_invalid"})
        proposed["options"] = [
            {**option, "content_doc": tiptap_doc(replacements[option["id"]].strip())}
            if option.get("id") in replacements
            else option
            for option in proposed.get("options", [])
        ]
    construct_keys = ["primary_concept", "primary_skill", "learning_objective"]
    construct_check = {
        "passed": all(
            proposed.get("construct", {}).get(key) == question.get("construct", {}).get(key)
            for key in construct_keys
        ),
        "checks": {
            key: proposed.get("construct", {}).get(key) == question.get("construct", {}).get(key)
            for key in construct_keys
        },
    }
    metrics.record_outcome("construct_preservation", "construct_preservation_failure_rate", not construct_check["passed"])
    proposal = {
        "_id": new_id("DRP"),
        "question_draft_id": question_draft_id,
        "owner_id": user.id,
        "action": payload.action,
        "instruction": payload.instruction,
        "before": {key: deepcopy(question.get(key)) for key in proposed},
        "after": proposed,
        "why": [payload.action],
        "target_effect": payload.action if payload.action in {"increase_difficulty", "decrease_difficulty"} else "quality",
        "construct_check": construct_check,
        "status": "proposed",
        "created_at": now(),
    }
    await database.value.draft_revision_proposals.insert_one(proposal)
    await audit(user.id, "draft_revision_proposed", "DraftRevisionProposal", proposal["_id"])
    return proposal


@router.post("/question-drafts/{question_draft_id}/ai/distractors", status_code=201)
async def propose_distractors(
    question_draft_id: str,
    payload: DistractorRevisionInput,
    user: CurrentUser = Depends(require_author),
):
    return await propose_draft_revision(
        question_draft_id,
        DraftAiActionInput(action="regenerate_distractors", instruction=json.dumps(payload.replacements)),
        user,
    )


@router.get("/review-queue")
async def list_review_queue(user: CurrentUser = Depends(require_author)):
    questions = await database.value.question_drafts.find(
        {
            "owner_id": user.id,
            "$or": [
                {"needs_teacher_review": True},
                {"status": {"$in": ["needs_revision", "prevalidated"]}},
                {"parse_confidence": {"$lt": 0.7}},
            ],
        }
    ).sort("updated_at", -1).to_list(1000)
    all_questions = await database.value.question_drafts.find({"owner_id": user.id}).to_list(5000)
    question_ids = [question["_id"] for question in all_questions]
    version_ids = [question["frozen_version_id"] for question in all_questions if question.get("frozen_version_id")]
    predictions, targets, calibrations = await asyncio.gather(
        database.value.difficulty_estimates.find(
            {"question_draft_id": {"$in": question_ids}, "owner_id": user.id}
        ).sort("created_at", -1).to_list(10000),
        database.value.difficulty_targets.find(
            {"question_draft_id": {"$in": question_ids}, "owner_id": user.id}
        ).sort("created_at", -1).to_list(10000),
        database.value.calibrations.find(
            {
                "question_version_id": {"$in": version_ids},
                "$or": [{"drift_flag": True}, {"item_fit_status": "review"}],
            }
        ).sort("created_at", -1).to_list(10000),
    )
    current_revision = {question["_id"]: question.get("revision") for question in all_questions}
    latest_prediction = {}
    latest_target = {}
    latest_calibration = {}
    for prediction in predictions:
        question_id = prediction.get("question_draft_id")
        if prediction.get("question_revision") == current_revision.get(question_id):
            latest_prediction.setdefault(question_id, prediction)
    for target in targets:
        question_id = target.get("question_draft_id")
        if target.get("question_revision") == current_revision.get(question_id):
            latest_target.setdefault(question_id, target)
    for calibration in calibrations:
        latest_calibration.setdefault(calibration.get("question_version_id"), calibration)
    queued_by_id = {question["_id"]: deepcopy(question) for question in questions}
    for question in all_questions:
        reasons = []
        prediction = latest_prediction.get(question["_id"])
        target = latest_target.get(question["_id"])
        calibration = latest_calibration.get(question.get("frozen_version_id"))
        if (
            prediction
            and target
            and isinstance(prediction.get("predicted_difficulty"), (int, float))
            and isinstance(target.get("target_difficulty"), (int, float))
            and abs(float(prediction["predicted_difficulty"]) - float(target["target_difficulty"])) >= 0.75
        ):
            reasons.append("difficulty_mismatch")
        if calibration and calibration.get("drift_flag"):
            reasons.append("calibration_drift")
        if calibration and calibration.get("item_fit_status") == "review":
            reasons.append("psychometric_fit_review")
        if question.get("validation", {}).get("warnings"):
            reasons.append("quality_warning")
        if reasons or question["_id"] in queued_by_id:
            queued = queued_by_id.setdefault(question["_id"], deepcopy(question))
            queued["review_reason_codes"] = sorted(
                set([*queued.get("review_reason_codes", []), *reasons])
            )
            if calibration:
                queued["flagged_calibration"] = calibration
    questions = sorted(queued_by_id.values(), key=lambda question: str(question.get("updated_at", "")), reverse=True)
    revisions = await database.value.revision_proposals.find({"owner_id": user.id, "status": "proposed"}).to_list(1000)
    draft_revisions = await database.value.draft_revision_proposals.find({"owner_id": user.id, "status": "proposed"}).to_list(1000)
    revision_version_ids = [revision["question_version_id"] for revision in revisions]
    original_versions = await database.value.question_versions.find(
        {"_id": {"$in": revision_version_ids}, "owner_id": user.id}
    ).to_list(1000)
    originals_by_id = {version["_id"]: version for version in original_versions}
    return {
        "questions": questions,
        "question_revisions": [
            {**revision, "original_version": originals_by_id.get(revision["question_version_id"])}
            for revision in revisions
        ],
        "draft_revisions": draft_revisions,
    }


@router.post("/question-drafts/{question_draft_id}/approve")
async def approve_question_draft(
    question_draft_id: str,
    payload: ReviewDecisionInput,
    user: CurrentUser = Depends(require_author),
):
    question = await require_owned("question_drafts", question_draft_id, user)
    validation = validate_question(question)
    if validation["blockers"]:
        raise HTTPException(status_code=422, detail={"code": "question_validation_failed", "validation": validation})
    updated = await database.value.question_drafts.find_one_and_update(
        {"_id": question_draft_id, "owner_id": user.id},
        {"$set": {"status": "approved", "needs_teacher_review": False, "reviewer_note": payload.reviewer_note, "reviewed_at": now(), "updated_at": now()}},
        return_document=ReturnDocument.AFTER,
    )
    await audit(user.id, "question_draft_approved", "QuestionDraft", question_draft_id, {"reviewer_note": payload.reviewer_note})
    if question.get("authoring_source") == "ai_generated":
        await persist_teacher_profile_event(
            user.id,
            "generation_accepted",
            {"question_draft_id": question_draft_id, "question_type": question.get("question_type")},
            f"generation-accepted-{question_draft_id}-{question['revision']}",
        )
    return updated


@router.post("/question-drafts/{question_draft_id}/reject")
async def reject_question_draft(
    question_draft_id: str,
    payload: ReviewDecisionInput,
    user: CurrentUser = Depends(require_author),
):
    question = await require_owned("question_drafts", question_draft_id, user)
    updated = await database.value.question_drafts.find_one_and_update(
        {"_id": question_draft_id, "owner_id": user.id},
        {"$set": {"status": "rejected", "reviewer_note": payload.reviewer_note, "reviewed_at": now(), "updated_at": now()}},
        return_document=ReturnDocument.AFTER,
    )
    await audit(user.id, "question_draft_rejected", "QuestionDraft", question_draft_id, {"reviewer_note": payload.reviewer_note})
    if question.get("authoring_source") == "ai_generated":
        await persist_teacher_profile_event(
            user.id,
            "generation_rejected",
            {"question_draft_id": question_draft_id, "question_type": question.get("question_type")},
            f"generation-rejected-{question_draft_id}-{question['revision']}",
        )
    return updated


@router.get("/questions")
async def list_question_bank(
    search: str | None = None,
    subject: str | None = None,
    target_program: str | None = None,
    chapter: str | None = None,
    lesson: str | None = None,
    concept_id: str | None = None,
    skill_id: str | None = None,
    question_type: str | None = None,
    cognitive_level: str | None = None,
    authoring_source: str | None = None,
    quality_status: str | None = None,
    minimum_prediction_confidence: float | None = None,
    minimum_predicted_difficulty: float | None = None,
    maximum_predicted_difficulty: float | None = None,
    minimum_calibrated_difficulty: float | None = None,
    maximum_calibrated_difficulty: float | None = None,
    publication_status: str | None = None,
    sort_by: str = "updated",
    sort_direction: str = "desc",
    status: str | None = None,
    user: CurrentUser = Depends(require_author),
):
    query: dict[str, Any] = {"owner_id": user.id, "status": status or "active"}
    questions = await database.value.questions.find(query).sort("updated_at", -1).to_list(1000)
    version_ids = [question["current_version_id"] for question in questions if question.get("current_version_id")]
    version_query: dict[str, Any] = {"_id": {"$in": version_ids}}
    if question_type:
        version_query["question_type"] = question_type
    if subject:
        version_query["curriculum_links.subject"] = subject
    if target_program:
        version_query["curriculum_links.target_program"] = target_program
    if chapter:
        version_query["curriculum_links.chapter"] = chapter
    if lesson:
        version_query["curriculum_links.lesson"] = lesson
    if concept_id:
        version_query["concept_ids"] = concept_id
    if skill_id:
        version_query["skill_ids"] = skill_id
    if cognitive_level:
        version_query["cognitive_level"] = cognitive_level
    if authoring_source:
        version_query["authoring_source"] = authoring_source
    if quality_status:
        version_query["quality_status"] = quality_status
    versions = await database.value.question_versions.find(version_query).to_list(1000)
    versions_by_id = {version["_id"]: version for version in versions}
    included_version_ids = list(versions_by_id)
    predictions = await database.value.difficulty_estimates.find(
        {"question_version_id": {"$in": included_version_ids}}
    ).sort("created_at", -1).to_list(5000)
    calibrations = await database.value.calibrations.find(
        {"question_version_id": {"$in": included_version_ids}, "status": "calibrated"}
    ).sort("created_at", -1).to_list(5000)
    latest_prediction = {}
    latest_calibration = {}
    for prediction in predictions:
        latest_prediction.setdefault(prediction["question_version_id"], prediction)
    for calibration in calibrations:
        latest_calibration.setdefault(calibration["question_version_id"], calibration)
    assessment_versions = await database.value.assessment_versions.find(
        {"owner_id": user.id, "items.question_version_id": {"$in": included_version_ids}},
        {"items": 1},
    ).to_list(5000)
    usage_count = {version_id: 0 for version_id in included_version_ids}
    for assessment_version in assessment_versions:
        for item in assessment_version.get("items", []):
            if item.get("question_version_id") in usage_count:
                usage_count[item["question_version_id"]] += 1
    exposure_rows = await database.value.responses.aggregate(
        [
            {"$match": {"question_version_id": {"$in": included_version_ids}}},
            {"$group": {"_id": "$question_version_id", "count": {"$sum": 1}}},
        ]
    ).to_list(5000)
    exposure_count = {row["_id"]: row["count"] for row in exposure_rows}
    rows = []
    search_value = search.casefold().strip() if search else ""
    for question in questions:
        version_id = question.get("current_version_id")
        version = versions_by_id.get(version_id)
        if not version:
            continue
        prediction = latest_prediction.get(version_id)
        calibration = latest_calibration.get(version_id)
        predicted = prediction.get("predicted_difficulty") if prediction else None
        calibrated = calibration.get("difficulty") if calibration else None
        confidence = prediction.get("confidence") if prediction else None
        if search_value and search_value not in version.get("plain_text_projection", "").casefold():
            continue
        if minimum_prediction_confidence is not None and (confidence is None or confidence < minimum_prediction_confidence):
            continue
        if minimum_predicted_difficulty is not None and (predicted is None or predicted < minimum_predicted_difficulty):
            continue
        if maximum_predicted_difficulty is not None and (predicted is None or predicted > maximum_predicted_difficulty):
            continue
        if minimum_calibrated_difficulty is not None and (calibrated is None or calibrated < minimum_calibrated_difficulty):
            continue
        if maximum_calibrated_difficulty is not None and (calibrated is None or calibrated > maximum_calibrated_difficulty):
            continue
        used = usage_count.get(version_id, 0)
        if publication_status == "published" and not used:
            continue
        if publication_status == "unpublished" and used:
            continue
        rows.append(
            {
                **question,
                "current_version": version,
                "difficulty_prediction": prediction,
                "calibration": calibration,
                "usage_count": used,
                "exposure_count": exposure_count.get(version_id, 0),
            }
        )
    sort_fields = {
        "created": lambda row: str(row.get("created_at") or ""),
        "updated": lambda row: str(row.get("updated_at") or ""),
        "predicted_difficulty": lambda row: (row.get("difficulty_prediction") or {}).get("predicted_difficulty") or -1,
        "calibrated_difficulty": lambda row: (row.get("calibration") or {}).get("difficulty") or -1,
        "usage": lambda row: row.get("usage_count", 0),
        "exposure": lambda row: row.get("exposure_count", 0),
    }
    if sort_by not in sort_fields or sort_direction not in {"asc", "desc"}:
        raise HTTPException(status_code=422, detail={"code": "question_bank_sort_invalid"})
    return sorted(rows, key=sort_fields[sort_by], reverse=sort_direction == "desc")


@router.post("/question-bank/add-to-draft", status_code=201)
async def add_question_bank_items_to_draft(
    payload: QuestionBankAddInput,
    user: CurrentUser = Depends(require_author),
):
    await require_owned("assessment_drafts", payload.assessment_draft_id, user)
    existing_sources = await database.value.question_drafts.distinct(
        "bank_source_question_id",
        {"assessment_draft_id": payload.assessment_draft_id, "owner_id": user.id},
    )
    if any(question_id in existing_sources for question_id in payload.question_ids):
        raise HTTPException(status_code=409, detail={"code": "question_already_in_assessment_draft"})
    questions = await database.value.questions.find(
        {"_id": {"$in": payload.question_ids}, "owner_id": user.id, "status": "active"}
    ).to_list(500)
    by_id = {question["_id"]: question for question in questions}
    if any(question_id not in by_id for question_id in payload.question_ids):
        raise HTTPException(status_code=404, detail={"code": "question_bank_item_missing"})
    versions = await database.value.question_versions.find(
        {"_id": {"$in": [by_id[question_id]["current_version_id"] for question_id in payload.question_ids]}}
    ).to_list(500)
    versions_by_id = {version["_id"]: version for version in versions}
    created = []
    draft_fields = {
        "question_type",
        "stem_doc",
        "options",
        "answer_key",
        "solution_doc",
        "scoring_rule",
        "curriculum_links",
        "concept_ids",
        "skill_ids",
        "tags",
        "cognitive_level",
        "construct",
        "source_evidence",
        "locked",
    }
    for question_id in payload.question_ids:
        source = versions_by_id[by_id[question_id]["current_version_id"]]
        question_data = {key: deepcopy(source.get(key)) for key in draft_fields}
        question_data["authoring_source"] = "hybrid"
        question_data["bank_source_question_id"] = question_id
        deterministic_id = f"QD-{hashlib.sha256(f'bank:{payload.assessment_draft_id}:{question_id}'.encode()).hexdigest()[:32]}"
        created_question = await persist_question_draft(
            payload.assessment_draft_id,
            question_data,
            user,
            deterministic_id,
        )
        created.append(created_question)
    await audit(
        user.id,
        "question_bank_items_added_to_draft",
        "AssessmentDraft",
        payload.assessment_draft_id,
        {"question_ids": payload.question_ids, "question_count": len(created)},
    )
    return {"assessment_draft_id": payload.assessment_draft_id, "questions": created}


@router.post("/questions/{question_id}/duplicate", status_code=201)
async def duplicate_question_bank_item(question_id: str, user: CurrentUser = Depends(require_author)):
    question = await require_owned("questions", question_id, user)
    current = await database.value.question_versions.find_one({"_id": question["current_version_id"]})
    if not current:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên bản câu hỏi")
    duplicated_question_id = new_id("Q")
    duplicated_version = deepcopy(current)
    duplicated_version.update(
        {
            "_id": f"{duplicated_question_id}-v1",
            "question_id": duplicated_question_id,
            "version": 1,
            "owner_id": user.id,
            "parent_version_id": None,
            "cloned_from_version_id": current["_id"],
            "created_by": "teacher_duplicate",
            "created_at": now(),
        }
    )
    duplicated_question = {
        "_id": duplicated_question_id,
        "owner_id": user.id,
        "status": "active",
        "current_version_id": duplicated_version["_id"],
        "created_at": now(),
        "updated_at": now(),
    }
    await database.value.question_versions.insert_one(duplicated_version)
    await database.value.questions.insert_one(duplicated_question)
    await audit(user.id, "question_bank_item_duplicated", "Question", duplicated_question_id, {"source_question_id": question_id})
    return {**duplicated_question, "current_version": duplicated_version}


@router.post("/questions/{question_id}/archive")
async def archive_question_bank_item(
    question_id: str,
    payload: QuestionArchiveInput,
    user: CurrentUser = Depends(require_author),
):
    await require_owned("questions", question_id, user)
    archived = await database.value.questions.find_one_and_update(
        {"_id": question_id, "owner_id": user.id},
        {"$set": {"status": "archived", "archived_at": now(), "updated_at": now()}},
        return_document=ReturnDocument.AFTER,
    )
    await audit(user.id, "question_bank_item_archived", "Question", question_id, {"reason": payload.reason})
    return archived


@router.get("/questions/{question_id}/usage")
async def get_question_usage(question_id: str, user: CurrentUser = Depends(require_author)):
    question = await require_owned("questions", question_id, user)
    version_ids = await database.value.question_versions.distinct("_id", {"question_id": question["_id"]})
    assessment_versions = await database.value.assessment_versions.find(
        {"owner_id": user.id, "items.question_version_id": {"$in": version_ids}},
        {"assessment_id": 1, "version": 1, "items": 1, "published_at": 1},
    ).to_list(1000)
    responses = await database.value.responses.count_documents({"question_version_id": {"$in": version_ids}})
    return {"question_id": question_id, "versions": version_ids, "assessment_versions": assessment_versions, "exposure_count": responses}


@router.get("/questions/{question_id}/versions")
async def list_question_versions(question_id: str, user: CurrentUser = Depends(require_author)):
    await require_owned("questions", question_id, user)
    return await database.value.question_versions.find({"question_id": question_id}).sort("version", -1).to_list(100)


@router.patch("/question-versions/{version_id}")
async def reject_question_version_mutation(
    version_id: str,
    payload: dict,
    user: CurrentUser = Depends(require_author),
):
    await require_owned("question_versions", version_id, user)
    await audit(user.id, "published_question_mutation_denied", "QuestionVersion", version_id, {"fields": sorted(payload)})
    raise HTTPException(status_code=409, detail={"code": "immutable_question_version"})


@router.post("/blueprints/{blueprint_id}/validate")
async def validate_blueprint_route(blueprint_id: str, user: CurrentUser = Depends(require_author)):
    blueprint = await require_owned("blueprints", blueprint_id, user)
    return validate_blueprint(blueprint)


@router.post("/assessment-drafts/{draft_id}/validate")
async def validate_assessment_draft(draft_id: str, user: CurrentUser = Depends(require_author)):
    draft = await require_owned("assessment_drafts", draft_id, user)
    questions = await database.value.question_drafts.find({"assessment_draft_id": draft_id, "owner_id": user.id}).to_list(500)
    question_results = {question["_id"]: validate_question(question) for question in questions}
    issues = []
    coverage_results = []
    issues.extend(validate_tiptap_content(draft.get("layout_doc", {})))
    if not questions:
        issues.append({"code": "assessment_has_no_questions", "severity": "BLOCKER"})
    question_order = draft.get("question_order", [])
    if len(question_order) != len(set(question_order)) or set(question_order) != set(question_results):
        issues.append({"code": "question_order_invalid", "severity": "BLOCKER"})
    if any(result["blockers"] for result in question_results.values()):
        issues.append({"code": "question_blockers_exist", "severity": "BLOCKER"})
    if any(question.get("frozen_revision") != question.get("revision") for question in questions):
        issues.append({"code": "question_current_revision_not_frozen", "severity": "BLOCKER"})
    high_stakes = bool(draft.get("context", {}).get("high_stakes"))
    if high_stakes:
        unapproved = [
            question["_id"]
            for question in questions
            if question.get("validity_review", {}).get("status") != "approved"
        ]
        if unapproved:
            issues.append(
                {
                    "code": "high_stakes_validity_review_required",
                    "severity": "BLOCKER",
                    "question_draft_ids": unapproved,
                }
            )
        essay_policy_missing = [
            question["_id"]
            for question in questions
            if question.get("question_type") == "essay"
            and (
                not question.get("scoring_rule", {}).get("rubric")
                or not question.get("scoring_rule", {}).get("teacher_review_required")
            )
        ]
        if essay_policy_missing:
            issues.append(
                {
                    "code": "high_stakes_essay_scoring_policy_required",
                    "severity": "BLOCKER",
                    "question_draft_ids": essay_policy_missing,
                }
            )
    if draft.get("blueprint_id"):
        blueprint = await require_owned("blueprints", draft["blueprint_id"], user)
        blueprint_result = validate_blueprint(blueprint)
        if not blueprint_result["valid"]:
            issues.extend(blueprint_result["issues"])
        if blueprint["total_questions"] != len(questions):
            issues.append({"code": "blueprint_question_count_mismatch", "severity": "BLOCKER", "expected": blueprint["total_questions"], "actual": len(questions)})
        actual_types = {}
        for question in questions:
            actual_types[question["question_type"]] = actual_types.get(question["question_type"], 0) + 1
        if blueprint.get("question_type_constraints") and actual_types != blueprint["question_type_constraints"]:
            issues.append({"code": "blueprint_question_type_mismatch", "severity": "BLOCKER", "expected": blueprint["question_type_constraints"], "actual": actual_types})
        actual_cognitive = {}
        for question in questions:
            cognitive = question.get("cognitive_level") or "unspecified"
            actual_cognitive[cognitive] = actual_cognitive.get(cognitive, 0) + 1
        if blueprint.get("cognitive_level_constraints") and actual_cognitive != blueprint["cognitive_level_constraints"]:
            issues.append({"code": "blueprint_cognitive_level_mismatch", "severity": "BLOCKER", "expected": blueprint["cognitive_level_constraints"], "actual": actual_cognitive})
        for constraint in blueprint.get("coverage_constraints", []):
            dimension = constraint["dimension"]
            requested_ids = set(constraint["ids"])
            matched = 0
            for question in questions:
                if dimension == "concept":
                    actual_ids = set(question.get("concept_ids", []))
                elif dimension == "skill":
                    actual_ids = set(question.get("skill_ids", []))
                else:
                    actual_ids = {
                        str(link.get("curriculum_node_id") or link.get("node_id"))
                        for link in question.get("curriculum_links", [])
                        if link.get("curriculum_node_id") or link.get("node_id")
                    }
                if requested_ids.intersection(actual_ids):
                    matched += 1
            coverage_result = {**constraint, "actual_count": matched, "satisfied": matched >= constraint["minimum_count"]}
            coverage_results.append(coverage_result)
            if constraint.get("required", True) and not coverage_result["satisfied"]:
                issues.append({"code": "blueprint_coverage_missing", "severity": "BLOCKER", **coverage_result})
        if blueprint.get("total_points") is not None:
            actual_points = round(sum(float(question.get("scoring_rule", {}).get("points", 1)) for question in questions), 6)
            if abs(actual_points - float(blueprint["total_points"])) > 0.000001:
                issues.append({"code": "blueprint_total_points_mismatch", "severity": "BLOCKER", "expected": blueprint["total_points"], "actual": actual_points})
        target_rows = await database.value.difficulty_targets.find(
            {"question_draft_id": {"$in": list(question_results)}, "owner_id": user.id}
        ).sort("created_at", -1).to_list(5000)
        latest_targets = {}
        for target in target_rows:
            latest_targets.setdefault(target["question_draft_id"], target)
        if len(latest_targets) != len(questions):
            issues.append({"code": "blueprint_question_targets_missing", "severity": "BLOCKER", "expected": len(questions), "actual": len(latest_targets)})
        else:
            actual_difficulty = {str(level): 0 for level in range(1, 6)}
            for target in latest_targets.values():
                actual_difficulty[str(difficulty_level(float(target["target_difficulty"])))] += 1
            if actual_difficulty != blueprint["difficulty_distribution"]:
                issues.append({"code": "blueprint_difficulty_mismatch", "severity": "BLOCKER", "expected": blueprint["difficulty_distribution"], "actual": actual_difficulty})
    return {"valid": not issues, "issues": issues, "questions": question_results, "coverage": coverage_results}


@router.post("/questions/{question_id}/revisions", status_code=201)
async def create_revision_proposal(
    question_id: str,
    payload: RevisionProposalInput,
    user: CurrentUser = Depends(require_author),
):
    question = await require_owned("questions", question_id, user)
    current = await database.value.question_versions.find_one({"_id": question["current_version_id"]})
    if not current:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên bản nguồn")
    keys = ["primary_concept", "primary_skill", "learning_objective"]
    construct_checks = {
        key: current.get("construct", {}).get(key) == payload.proposed_version.get("construct", {}).get(key)
        for key in keys
    }
    proposal = payload.model_dump()
    proposal["proposed_version"] = deepcopy(proposal["proposed_version"])
    proposal["proposed_version"]["validity_review"] = {"status": "pending", "risk_flags": []}
    proposal["construct_check"] = {
        **payload.construct_check,
        "passed": all(construct_checks.values()),
        "checks": construct_checks,
    }
    metrics.record_outcome(
        "construct_preservation",
        "construct_preservation_failure_rate",
        not proposal["construct_check"]["passed"],
    )
    proposal.update(
        {
            "_id": new_id("REV"),
            "question_version_id": question["current_version_id"],
            "question_id": question_id,
            "owner_id": user.id,
            "status": "proposed",
            "created_at": now(),
        }
    )
    await database.value.revision_proposals.insert_one(proposal)
    await audit(user.id, "revision_proposed", "RevisionProposal", proposal["_id"])
    return proposal


@router.post("/revisions/{proposal_id}/approve", status_code=201)
async def approve_revision(proposal_id: str, user: CurrentUser = Depends(require_author)):
    proposal = await require_owned("revision_proposals", proposal_id, user)
    if proposal["status"] == "approved" and proposal.get("approved_version_id"):
        approved = await database.value.question_versions.find_one({"_id": proposal["approved_version_id"], "owner_id": user.id})
        if approved:
            return approved
    if proposal["status"] != "proposed":
        raise HTTPException(status_code=409, detail="Đề xuất không còn ở trạng thái chờ duyệt")
    if not proposal.get("construct_check", {}).get("passed"):
        raise HTTPException(status_code=422, detail="Kiểm tra bảo toàn construct chưa đạt")
    current = await database.value.question_versions.find_one({"_id": proposal["question_version_id"]})
    if not current:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên bản nguồn")
    canonical = await require_owned("questions", current["question_id"], user)
    if canonical.get("current_version_id") != current["_id"]:
        raise HTTPException(status_code=409, detail={"code": "revision_source_stale"})
    linked_drafts = await database.value.question_drafts.find(
        {"question_id": current["question_id"], "owner_id": user.id}
    ).to_list(500)
    source_draft_revision = max(
        [int(draft.get("revision", 1)) for draft in linked_drafts],
        default=0,
    ) + 1
    version = current["version"] + 1
    version_id = f"{current['question_id']}-v{version}"
    snapshot = deepcopy(proposal["proposed_version"])
    snapshot.update(
        {
            "_id": version_id,
            "question_id": current["question_id"],
            "version": version,
            "owner_id": user.id,
            "content_format": "tiptap_json_v1",
            "parent_version_id": current["_id"],
            "source_draft_revision": source_draft_revision,
            "created_by": "ai_approved_by_teacher",
            "created_at": now(),
        }
    )
    validation = validate_question(snapshot)
    if validation["blockers"]:
        raise HTTPException(status_code=422, detail={"code": "revision_validation_failed", "validation": validation})
    snapshot["plain_text_projection"] = validation["plain_text_projection"]
    snapshot["quality_status"] = validation["status"]
    snapshot["quality_validation"] = deepcopy(validation)
    try:
        await database.value.question_versions.insert_one(snapshot)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "revision_version_conflict"})
    updated_question = await database.value.questions.update_one(
        {"_id": current["question_id"], "owner_id": user.id, "current_version_id": current["_id"]},
        {"$set": {"current_version_id": version_id, "updated_at": now()}},
    )
    if updated_question.modified_count != 1:
        await database.value.question_versions.delete_one({"_id": version_id, "owner_id": user.id})
        raise HTTPException(status_code=409, detail={"code": "revision_source_stale"})
    revision_fields = {
        key: snapshot.get(key)
        for key in {
            "question_type",
            "authoring_source",
            "stem_doc",
            "options",
            "answer_key",
            "solution_doc",
            "scoring_rule",
            "curriculum_links",
            "concept_ids",
            "skill_ids",
            "tags",
            "cognitive_level",
            "construct",
            "source_evidence",
            "locked",
            "validity_review",
        }
    }
    await database.value.question_drafts.update_many(
        {"question_id": current["question_id"], "owner_id": user.id},
        [
            {
                "$set": {
                    **{key: {"$literal": value} for key, value in revision_fields.items()},
                    "frozen_version_id": {"$literal": version_id},
                    "revision": {"$literal": source_draft_revision},
                    "frozen_revision": {"$literal": source_draft_revision},
                    "status": "approved",
                    "updated_at": {"$literal": now()},
                }
            }
        ],
    )
    estimate = predict_difficulty(snapshot, "structured_revision_v1")
    estimate.update(
        {
            "_id": new_id("DIF"),
            "question_draft_id": None,
            "question_version_id": version_id,
            "owner_id": user.id,
            "revealed_at": now(),
            "created_at": now(),
        }
    )
    await database.value.difficulty_estimates.insert_one(estimate)
    await database.value.difficulty_targets.insert_one(
        {
            "_id": new_id("TGT"),
            "scope": "question",
            "question_draft_id": None,
            "question_version_id": version_id,
            "target_difficulty": proposal["target_difficulty"],
            "owner_id": user.id,
            "created_by": user.id,
            "created_at": now(),
        }
    )
    await database.value.revision_proposals.update_one(
        {"_id": proposal_id}, {"$set": {"status": "approved", "approved_by": user.id, "approved_version_id": version_id, "updated_at": now()}}
    )
    metrics.record_outcome("teacher_revision_decision", "teacher_revision_acceptance_rate", True)
    await audit(user.id, "revision_approved", "RevisionProposal", proposal_id, {"question_version_id": version_id})
    return snapshot


@router.get("/revisions/{proposal_id}")
async def get_revision_proposal(proposal_id: str, user: CurrentUser = Depends(require_author)):
    return await require_owned("revision_proposals", proposal_id, user)


@router.get("/questions/{question_id}/revisions")
async def list_revision_proposals(question_id: str, user: CurrentUser = Depends(require_author)):
    await require_owned("questions", question_id, user)
    return await database.value.revision_proposals.find({"question_id": question_id}).sort("created_at", -1).to_list(100)


@router.post("/draft-revisions/{proposal_id}/approve")
async def approve_draft_revision(proposal_id: str, user: CurrentUser = Depends(require_author)):
    proposal = await require_owned("draft_revision_proposals", proposal_id, user)
    if proposal["status"] != "proposed":
        raise HTTPException(status_code=409, detail="Đề xuất không còn ở trạng thái chờ duyệt")
    if not proposal.get("construct_check", {}).get("passed"):
        raise HTTPException(status_code=422, detail="Kiểm tra bảo toàn construct chưa đạt")
    proposal_validation = validate_question(proposal["after"])
    if proposal_validation["blockers"]:
        raise HTTPException(status_code=422, detail={"code": "draft_revision_validation_failed", "validation": proposal_validation})
    question = await require_owned("question_drafts", proposal["question_draft_id"], user)
    changes = deepcopy(proposal["after"])
    for key in ["owner_id", "assessment_draft_id", "question_id", "status"]:
        changes.pop(key, None)
    updated = await optimistic_patch(
        "question_drafts",
        question["_id"],
        user.id,
        question["revision"],
        changes,
    )
    await database.value.draft_revision_proposals.update_one(
        {"_id": proposal_id},
        {"$set": {"status": "approved", "approved_by": user.id, "updated_at": now()}},
    )
    metrics.record_outcome("teacher_revision_decision", "teacher_revision_acceptance_rate", True)
    await audit(user.id, "draft_revision_approved", "DraftRevisionProposal", proposal_id)
    return updated


@router.post("/draft-revisions/{proposal_id}/reject")
async def reject_draft_revision(proposal_id: str, user: CurrentUser = Depends(require_author)):
    await require_owned("draft_revision_proposals", proposal_id, user)
    proposal = await database.value.draft_revision_proposals.find_one_and_update(
        {"_id": proposal_id, "owner_id": user.id, "status": "proposed"},
        {"$set": {"status": "rejected", "rejected_by": user.id, "updated_at": now()}},
        return_document=ReturnDocument.AFTER,
    )
    if not proposal:
        raise HTTPException(status_code=409, detail="Đề xuất không còn ở trạng thái chờ duyệt")
    metrics.record_outcome("teacher_revision_decision", "teacher_revision_acceptance_rate", False)
    await audit(user.id, "draft_revision_rejected", "DraftRevisionProposal", proposal_id)
    return proposal


@router.post("/revisions/{proposal_id}/reject")
async def reject_revision(proposal_id: str, user: CurrentUser = Depends(require_author)):
    await require_owned("revision_proposals", proposal_id, user)
    proposal = await database.value.revision_proposals.find_one_and_update(
        {"_id": proposal_id, "status": "proposed"},
        {"$set": {"status": "rejected", "rejected_by": user.id, "updated_at": now()}},
        return_document=ReturnDocument.AFTER,
    )
    if not proposal:
        raise HTTPException(status_code=409, detail="Đề xuất không còn ở trạng thái chờ duyệt")
    metrics.record_outcome("teacher_revision_decision", "teacher_revision_acceptance_rate", False)
    await audit(user.id, "revision_rejected", "RevisionProposal", proposal_id)
    return proposal
