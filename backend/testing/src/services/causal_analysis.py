import json

from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.services.design_assistance import ai_contract_metadata, request_design_assistance


async def validate_member(db, project_id, user_id):
    if not await db.project_members.find_one(
        {"project_id": project_id, "user_id": user_id, "status": "ACTIVE"}
    ):
        raise HTTPException(status_code=422, detail={"code": "ACTION_OWNER_NOT_PROJECT_MEMBER"})


async def get_analysis(db, analysis_id, user, permission="causalanalysis.read"):
    value = await db.causal_analyses.find_one({"_id": analysis_id})
    if not value:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(value["project_id"], user, permission)
    return value


async def list_analyses(db, project_id, user):
    await get_project(project_id, user, "causalanalysis.read")
    items = (
        await db.causal_analyses.find({"project_id": project_id})
        .sort("updated_at", -1)
        .to_list(1000)
    )
    return {"items": items, "total": len(items)}


async def suggest_candidates(db, project_id, user):
    project = await get_project(project_id, user, "causalanalysis.read")
    project_settings = project.get("settings") or {}
    reopen_threshold = max(int(project_settings.get("rca_reopen_threshold", 2)), 1)
    duplicate_threshold = max(int(project_settings.get("rca_duplicate_threshold", 3)), 2)
    defects = await db.defects.find({"project_id": project_id}).sort("updated_at", -1).to_list(2000)
    existing = await db.causal_analyses.find(
        {"project_id": project_id, "status": {"$ne": "CLOSED"}}, {"defect_ids": 1}
    ).to_list(1000)
    linked = {defect_id for analysis in existing for defect_id in analysis.get("defect_ids", [])}
    duplicate_counts = {}
    root_cause_counts = {}
    for defect in defects:
        duplicate_key = defect.get("duplicate_cluster_id") or defect.get("duplicate_of")
        if duplicate_key:
            duplicate_counts[duplicate_key] = duplicate_counts.get(duplicate_key, 0) + 1
        category = defect.get("root_cause_category")
        if category and category != "UNKNOWN":
            root_cause_counts[category] = root_cause_counts.get(category, 0) + 1
    items = []
    for defect in defects:
        if defect["_id"] in linked:
            continue
        reason_codes = []
        if str(defect.get("severity", "")).upper() in {"BLOCKER", "CRITICAL"}:
            reason_codes.append("SEVERITY_TRIGGER")
        if (
            int(defect.get("reopen_count", 0) or 0) >= reopen_threshold
            or defect.get("status") == "REOPENED"
        ):
            reason_codes.append("REOPEN_TRIGGER")
        duplicate_key = defect.get("duplicate_cluster_id") or defect.get("duplicate_of")
        if duplicate_key and duplicate_counts.get(duplicate_key, 0) >= duplicate_threshold:
            reason_codes.append("DUPLICATE_CLUSTER_TRIGGER")
        category = defect.get("root_cause_category")
        if (
            category
            and category != "UNKNOWN"
            and root_cause_counts.get(category, 0) >= duplicate_threshold
        ):
            reason_codes.append("REPEATED_ROOT_CAUSE_TRIGGER")
        if reason_codes:
            items.append(
                {
                    "candidate_id": f"RCA-CANDIDATE-{defect['_id']}",
                    "defect_ids": [defect["_id"]],
                    "problem_statement": defect.get("title")
                    or defect.get("summary")
                    or defect["_id"],
                    "reason_codes": reason_codes,
                    "evidence_refs": [defect["_id"]],
                }
            )
    return {
        "items": items,
        "total": len(items),
        "thresholds": {"reopen_count": reopen_threshold, "duplicate_cluster": duplicate_threshold},
    }


async def create_analysis(db, project_id, payload, user):
    await get_project(project_id, user, "causalanalysis.create")
    defect_ids = list(dict.fromkeys(payload.defect_ids))
    if defect_ids:
        defects = await db.defects.find(
            {"_id": {"$in": defect_ids}, "project_id": project_id}
        ).to_list(1000)
        if len(defects) != len(defect_ids):
            raise HTTPException(status_code=422, detail={"code": "DEFECT_NOT_IN_PROJECT"})
    await validate_member(db, project_id, payload.owner_id)
    if payload.idempotency_key:
        existing = await db.causal_analyses.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if existing:
            if set(existing.get("defect_ids", [])) != set(defect_ids):
                raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
            return existing
    timestamp = now()
    identifier = new_id("RCA")
    data = payload.model_dump(exclude={"evidence"})
    value = {
        "_id": identifier,
        "analysis_key": identifier,
        "project_id": project_id,
        **data,
        "defect_ids": defect_ids,
        "root_causes": [],
        "contributing_factors": [],
        "five_whys": [],
        "corrective_actions": [],
        "preventive_actions": [],
        "approved_by": None,
        "effectiveness_reviews": [],
        "status": "DRAFT",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await db.causal_analyses.insert_one(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await db.causal_analyses.find_one(
                {"project_id": project_id, "idempotency_key": payload.idempotency_key}
            )
        raise
    await audit(
        user.id,
        "causal_analysis_created",
        "CausalAnalysis",
        value["_id"],
        project_id,
        {"defect_ids": defect_ids},
    )
    return value


async def update_analysis(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.update")
    if value["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "CAUSAL_ANALYSIS_NOT_DRAFT"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if "owner_id" in changes:
        await validate_member(db, value["project_id"], changes["owner_id"])
    changes["updated_at"] = now()
    updated = await db.causal_analyses.find_one_and_update(
        {"_id": analysis_id, "revision": payload.expected_revision, "status": "DRAFT"},
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "causal_analysis_updated",
        "CausalAnalysis",
        analysis_id,
        value["project_id"],
        {"fields": sorted(changes)},
    )
    return updated


async def link_defects(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.update")
    if value["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "CAUSAL_ANALYSIS_NOT_DRAFT"})
    defect_ids = list(dict.fromkeys(payload.defect_ids))
    defects = await db.defects.find(
        {"_id": {"$in": defect_ids}, "project_id": value["project_id"]}
    ).to_list(1000)
    if len(defects) != len(defect_ids):
        raise HTTPException(status_code=422, detail={"code": "DEFECT_NOT_IN_PROJECT"})
    linked = list(dict.fromkeys([*value.get("defect_ids", []), *defect_ids]))
    updated = await db.causal_analyses.find_one_and_update(
        {"_id": analysis_id, "revision": payload.expected_revision, "status": "DRAFT"},
        {"$set": {"defect_ids": linked, "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "causal_analysis_defects_linked",
        "CausalAnalysis",
        analysis_id,
        value["project_id"],
        {"defect_ids": defect_ids},
    )
    return updated


async def add_five_why(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.update")
    if value["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "CAUSAL_ANALYSIS_NOT_DRAFT"})
    five_whys = list(value.get("five_whys", []))
    if len(five_whys) >= 5:
        raise HTTPException(status_code=409, detail={"code": "FIVE_WHYS_LIMIT_REACHED"})
    five_whys.append(payload.why)
    updated = await db.causal_analyses.find_one_and_update(
        {"_id": analysis_id, "revision": payload.expected_revision, "status": "DRAFT"},
        {"$set": {"five_whys": five_whys, "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "causal_analysis_five_why_added",
        "CausalAnalysis",
        analysis_id,
        value["project_id"],
        {"sequence": len(five_whys)},
    )
    return updated


async def record_root_cause(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.update")
    if value["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "CAUSAL_ANALYSIS_NOT_DRAFT"})
    root_cause = {
        "category": payload.category,
        "detail": payload.detail,
        "evidence_refs": payload.evidence_refs,
        "recorded_by": user.id,
        "recorded_at": now(),
    }
    updated = await db.causal_analyses.find_one_and_update(
        {"_id": analysis_id, "revision": payload.expected_revision, "status": "DRAFT"},
        {
            "$set": {
                "root_causes": [root_cause],
                "contributing_factors": payload.contributing_factors,
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "causal_analysis_root_cause_recorded",
        "CausalAnalysis",
        analysis_id,
        value["project_id"],
        {"category": payload.category},
    )
    return updated


async def create_action(db, analysis_id, payload, user, action_type):
    value = await get_analysis(db, analysis_id, user, "preventionaction.manage")
    if value["status"] not in {"APPROVED", "ACTION_IN_PROGRESS"}:
        raise HTTPException(status_code=409, detail={"code": "CAUSAL_ANALYSIS_NOT_APPROVED"})
    if value["status"] == "CLOSED":
        raise HTTPException(status_code=409, detail={"code": "CLOSED_CAUSAL_ANALYSIS_IMMUTABLE"})
    timestamp = now()
    action = {
        "_id": new_id("CAPA"),
        "causal_analysis_id": analysis_id,
        "project_id": value["project_id"],
        **payload.model_dump(),
        "action_type": action_type,
        "owner_id": None,
        "status": "OPEN",
        "result": "",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await db.preventive_actions.insert_one(action)
    field = "corrective_actions" if action_type == "CORRECTIVE" else "preventive_actions"
    analysis = await db.causal_analyses.find_one_and_update(
        {
            "_id": analysis_id,
            "revision": value["revision"],
            "status": {"$in": ["APPROVED", "ACTION_IN_PROGRESS"]},
        },
        {
            "$addToSet": {field: action["_id"]},
            "$set": {"status": "ACTION_IN_PROGRESS", "updated_at": timestamp},
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not analysis:
        await db.preventive_actions.delete_one({"_id": action["_id"]})
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "capa_action_created",
        "PreventionAction",
        action["_id"],
        value["project_id"],
        {"causal_analysis_id": analysis_id, "type": action_type},
    )
    return action


async def assign_action(db, action_id, payload, user):
    action = await db.preventive_actions.find_one({"_id": action_id})
    if not action:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(action["project_id"], user, "preventionaction.manage")
    await validate_member(db, action["project_id"], payload.owner_id)
    if action["status"] == "CLOSED":
        raise HTTPException(status_code=409, detail={"code": "CAPA_ACTION_CLOSED"})
    updated = await db.preventive_actions.find_one_and_update(
        {"_id": action_id, "revision": payload.expected_revision, "status": {"$ne": "CLOSED"}},
        {
            "$set": {
                "owner_id": payload.owner_id,
                "assigned_by": user.id,
                "assigned_at": now(),
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "capa_action_assigned",
        "PreventionAction",
        action_id,
        action["project_id"],
        {"owner_id": payload.owner_id},
    )
    return updated


async def update_action(db, action_id, payload, user):
    action = await db.preventive_actions.find_one({"_id": action_id})
    if not action:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(action["project_id"], user, "preventionaction.manage")
    if payload.status != "OPEN" and not action.get("owner_id"):
        raise HTTPException(status_code=409, detail={"code": "CAPA_ACTION_OWNER_REQUIRED"})
    states = ["OPEN", "IN_PROGRESS", "IMPLEMENTED", "EFFECTIVENESS_REVIEW", "CLOSED"]
    if (
        states.index(payload.status) < states.index(action["status"])
        or states.index(payload.status) > states.index(action["status"]) + 1
    ):
        raise HTTPException(status_code=409, detail={"code": "INVALID_CAPA_TRANSITION"})
    changes = {"status": payload.status, "result": payload.result, "updated_at": now()}
    if payload.evidence_refs is not None:
        changes["evidence_refs"] = payload.evidence_refs
    updated = await db.preventive_actions.find_one_and_update(
        {"_id": action_id, "revision": payload.expected_revision, "status": action["status"]},
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    event = "preventive_action_closed" if payload.status == "CLOSED" else "capa_action_updated"
    await audit(
        user.id,
        event,
        "PreventionAction",
        action_id,
        action["project_id"],
        {"from": action["status"], "to": payload.status},
    )
    return updated


async def submit_review(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.update")
    if not value.get("defect_ids"):
        raise HTTPException(status_code=409, detail={"code": "CAUSAL_ANALYSIS_DEFECT_REQUIRED"})
    if not value.get("five_whys"):
        raise HTTPException(status_code=409, detail={"code": "FIVE_WHYS_REQUIRED"})
    if not value.get("root_causes"):
        raise HTTPException(status_code=409, detail={"code": "ROOT_CAUSE_REQUIRED"})
    timestamp = now()
    updated = await db.causal_analyses.find_one_and_update(
        {"_id": analysis_id, "revision": payload.expected_revision, "status": "DRAFT"},
        {
            "$set": {
                "status": "IN_REVIEW",
                "submitted_by": user.id,
                "submitted_at": timestamp,
                "review_note": payload.note,
                "updated_at": timestamp,
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "CAUSAL_ANALYSIS_SUBMIT_CONFLICT"})
    await audit(
        user.id,
        "causal_analysis_submitted",
        "CausalAnalysis",
        analysis_id,
        value["project_id"],
        {"note": payload.note},
    )
    return updated


async def approve_analysis(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.approve")
    target = "APPROVED" if payload.decision == "APPROVE" else "DRAFT"
    timestamp = now()
    changes = {
        "status": target,
        "approval_note": payload.note,
        "reviewed_by": user.id,
        "reviewed_at": timestamp,
        "updated_at": timestamp,
    }
    if target == "APPROVED":
        changes.update({"approved_by": user.id, "approved_at": timestamp})
    else:
        changes.update({"approved_by": None, "approved_at": None})
    updated = await db.causal_analyses.find_one_and_update(
        {"_id": analysis_id, "revision": payload.expected_revision, "status": "IN_REVIEW"},
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "CAUSAL_ANALYSIS_REVIEW_CONFLICT"})
    event = "causal_analysis_approved" if target == "APPROVED" else "causal_analysis_reviewed"
    await audit(
        user.id,
        event,
        "CausalAnalysis",
        analysis_id,
        value["project_id"],
        {"decision": payload.decision},
    )
    return updated


async def review_effectiveness(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.update")
    if value["status"] != "ACTION_IN_PROGRESS":
        raise HTTPException(
            status_code=409, detail={"code": "CAUSAL_ANALYSIS_ACTIONS_NOT_IN_PROGRESS"}
        )
    actions = await db.preventive_actions.find({"causal_analysis_id": analysis_id}).to_list(1000)
    if not actions or any(
        item["status"] not in {"IMPLEMENTED", "EFFECTIVENESS_REVIEW", "CLOSED"} for item in actions
    ):
        raise HTTPException(status_code=409, detail={"code": "CAPA_ACTIONS_NOT_IMPLEMENTED"})
    review = {
        "decision": payload.decision,
        "result": payload.result,
        "evidence_refs": payload.evidence_refs,
        "reviewed_at": payload.reviewed_at,
        "reviewed_by": user.id,
    }
    reviews = [*value.get("effectiveness_reviews", []), review]
    target = "EFFECTIVENESS_REVIEW" if payload.decision == "EFFECTIVE" else "ACTION_IN_PROGRESS"
    updated = await db.causal_analyses.find_one_and_update(
        {"_id": analysis_id, "revision": payload.expected_revision, "status": "ACTION_IN_PROGRESS"},
        {
            "$set": {
                "status": target,
                "effectiveness_reviews": reviews,
                "effectiveness_review_at": payload.reviewed_at,
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "causal_analysis_effectiveness_reviewed",
        "CausalAnalysis",
        analysis_id,
        value["project_id"],
        {"decision": payload.decision, "evidence_refs": payload.evidence_refs},
    )
    return updated


async def close_analysis(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.approve")
    actions = await db.preventive_actions.find({"causal_analysis_id": analysis_id}).to_list(1000)
    if not actions or any(item["status"] != "CLOSED" for item in actions):
        raise HTTPException(status_code=409, detail={"code": "CAPA_ACTIONS_NOT_CLOSED"})
    if (
        not value.get("effectiveness_reviews")
        or value["effectiveness_reviews"][-1].get("decision") != "EFFECTIVE"
    ):
        raise HTTPException(status_code=409, detail={"code": "EFFECTIVENESS_APPROVAL_REQUIRED"})
    timestamp = now()
    updated = await db.causal_analyses.find_one_and_update(
        {
            "_id": analysis_id,
            "revision": payload.expected_revision,
            "status": "EFFECTIVENESS_REVIEW",
        },
        {
            "$set": {
                "status": "CLOSED",
                "closed_by": user.id,
                "closed_at": timestamp,
                "close_note": payload.note,
                "updated_at": timestamp,
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "CAUSAL_ANALYSIS_CLOSE_CONFLICT"})
    await audit(
        user.id,
        "causal_analysis_closed",
        "CausalAnalysis",
        analysis_id,
        value["project_id"],
        {"note": payload.note},
    )
    return updated


async def generate_hypotheses(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.update")
    existing = await db.ai_results.find_one(
        {"project_id": value["project_id"], "idempotency_key": payload.idempotency_key}
    )
    if existing:
        if (
            existing.get("result_type") != "CAUSAL_ANALYSIS_HYPOTHESES"
            or existing.get("subject_id") != analysis_id
        ):
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
        return existing
    defects = await db.defects.find(
        {"_id": {"$in": value["defect_ids"]}, "project_id": value["project_id"]}
    ).to_list(500)
    historical = (
        await db.defects.find(
            {
                "project_id": value["project_id"],
                "_id": {"$nin": value["defect_ids"]},
                "root_cause_category": {"$ne": "UNKNOWN"},
            },
            {"_id": 1, "title": 1, "root_cause_category": 1, "root_cause_detail": 1},
        )
        .limit(100)
        .to_list(100)
    )
    evidence = [
        {
            "artifact_type": "defect",
            "artifact_id": item["_id"],
            "authority": "PROJECT_RECORD",
            "text": json.dumps(
                {
                    key: item.get(key)
                    for key in [
                        "title",
                        "severity",
                        "status",
                        "root_cause_category",
                        "root_cause_detail",
                        "injected_phase",
                        "detected_phase",
                        "escape_reason",
                    ]
                },
                ensure_ascii=False,
                default=str,
            ),
        }
        for item in [*defects, *historical]
    ]
    instruction = json.dumps(
        {
            "task": "Đề xuất giả thuyết nguyên nhân gốc cụm lỗi, yếu tố đóng góp và TestCondition hoặc TestCase còn thiếu; không xác nhận nguyên nhân và không phê duyệt CAPA",
            "problem_statement": value["problem_statement"],
            "user_instruction": payload.instruction,
        },
        ensure_ascii=False,
    )
    ai = await request_design_assistance(
        "causal_analysis", value["project_id"], instruction, evidence
    )
    result = {
        "_id": new_id("AIR"),
        "project_id": value["project_id"],
        "result_type": "CAUSAL_ANALYSIS_HYPOTHESES",
        "subject_id": analysis_id,
        "candidate_only": True,
        "human_confirmation_required": True,
        "suggestions": ai.get("suggestions", []),
        **ai_contract_metadata(ai),
        "idempotency_key": payload.idempotency_key,
        "created_by": user.id,
        "created_at": now(),
    }
    try:
        await db.ai_results.insert_one(result)
    except DuplicateKeyError:
        return await db.ai_results.find_one(
            {"project_id": value["project_id"], "idempotency_key": payload.idempotency_key}
        )
    await audit(
        user.id,
        "causal_analysis_ai_hypotheses_generated",
        "AIResult",
        result["_id"],
        value["project_id"],
        {"analysis_id": analysis_id, "candidate_count": len(result["suggestions"])},
    )
    return result
