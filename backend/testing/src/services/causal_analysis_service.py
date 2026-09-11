import json

from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.services.design_assistance import request_design_assistance


async def validate_member(db, project_id, user_id):
    if not await db.project_members.find_one({"project_id": project_id, "user_id": user_id, "status": "ACTIVE"}):
        raise HTTPException(status_code=422, detail={"code": "ACTION_OWNER_NOT_PROJECT_MEMBER"})


async def get_analysis(db, analysis_id, user, permission="causalanalysis.read"):
    value = await db.causal_analyses.find_one({"_id": analysis_id})
    if not value:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(value["project_id"], user, permission)
    return value


async def list_analyses(db, project_id, user):
    await get_project(project_id, user, "causalanalysis.read")
    items = await db.causal_analyses.find({"project_id": project_id}).sort("updated_at", -1).to_list(1000)
    return {"items": items, "total": len(items)}


async def create_analysis(db, project_id, payload, user):
    await get_project(project_id, user, "causalanalysis.create")
    defect_ids = list(dict.fromkeys(payload.defect_ids))
    defects = await db.defects.find({"_id": {"$in": defect_ids}, "project_id": project_id}).to_list(1000)
    if len(defects) != len(defect_ids):
        raise HTTPException(status_code=422, detail={"code": "DEFECT_NOT_IN_PROJECT"})
    eligible = len(defects) >= 3 or any(str(item.get("severity", "")).lower() in {"blocker", "critical"} or int(item.get("reopen_count", 0)) > 0 or item.get("status") == "REOPENED" for item in defects)
    if not eligible:
        raise HTTPException(status_code=422, detail={"code": "CAUSAL_ANALYSIS_TRIGGER_NOT_MET"})
    await validate_member(db, project_id, payload.owner_id)
    if payload.idempotency_key:
        existing = await db.causal_analyses.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        if existing:
            if set(existing.get("defect_ids", [])) != set(defect_ids):
                raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
            return existing
    timestamp = now()
    value = {"_id": new_id("RCA"), "project_id": project_id, **payload.model_dump(), "defect_ids": defect_ids, "corrective_actions": [], "preventive_actions": [], "root_cause_approved": False, "approved_by": None, "status": "OPEN", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    try:
        await db.causal_analyses.insert_one(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await db.causal_analyses.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        raise
    await audit(user.id, "causal_analysis_created", "CausalAnalysis", value["_id"], project_id, {"defect_ids": defect_ids})
    return value


async def update_analysis(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.update")
    if value["status"] == "CLOSED":
        raise HTTPException(status_code=409, detail={"code": "CLOSED_CAUSAL_ANALYSIS_IMMUTABLE"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if "owner_id" in changes:
        await validate_member(db, value["project_id"], changes["owner_id"])
    if "root_causes" in changes:
        changes["root_cause_approved"] = False
        changes["approved_by"] = None
    changes["updated_at"] = now()
    updated = await db.causal_analyses.find_one_and_update({"_id": analysis_id, "revision": payload.expected_revision, "status": {"$ne": "CLOSED"}}, {"$set": changes, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "causal_analysis_updated", "CausalAnalysis", analysis_id, value["project_id"], {"fields": sorted(changes)})
    return updated


async def approve_root_cause(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.approve")
    if not value.get("root_causes"):
        raise HTTPException(status_code=409, detail={"code": "ROOT_CAUSE_REQUIRED"})
    changes = {"root_cause_approved": payload.decision == "APPROVE", "approved_by": user.id if payload.decision == "APPROVE" else None, "approval_note": payload.note, "updated_at": now()}
    updated = await db.causal_analyses.find_one_and_update({"_id": analysis_id, "revision": payload.expected_revision, "status": {"$ne": "CLOSED"}}, {"$set": changes, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "causal_root_cause_decided", "CausalAnalysis", analysis_id, value["project_id"], {"decision": payload.decision})
    return updated


async def create_action(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "preventionaction.manage")
    if value["status"] == "CLOSED":
        raise HTTPException(status_code=409, detail={"code": "CLOSED_CAUSAL_ANALYSIS_IMMUTABLE"})
    await validate_member(db, value["project_id"], payload.owner_id)
    timestamp = now()
    action = {"_id": new_id("CAPA"), "causal_analysis_id": analysis_id, "project_id": value["project_id"], **payload.model_dump(), "status": "OPEN", "result": "", "revision": 1, "approved_by": None, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    await db.preventive_actions.insert_one(action)
    field = "corrective_actions" if payload.action_type == "CORRECTIVE" else "preventive_actions"
    await db.causal_analyses.update_one({"_id": analysis_id}, {"$addToSet": {field: action["_id"]}, "$set": {"updated_at": timestamp}, "$inc": {"revision": 1}})
    await audit(user.id, "capa_action_created", "PreventionAction", action["_id"], value["project_id"], {"causal_analysis_id": analysis_id, "type": payload.action_type})
    return action


async def update_action(db, action_id, payload, user):
    action = await db.preventive_actions.find_one({"_id": action_id})
    if not action:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(action["project_id"], user, "preventionaction.manage")
    states = ["OPEN", "IN_PROGRESS", "IMPLEMENTED", "EFFECTIVENESS_REVIEW", "CLOSED"]
    if states.index(payload.status) < states.index(action["status"]) or states.index(payload.status) > states.index(action["status"]) + 1:
        raise HTTPException(status_code=409, detail={"code": "INVALID_CAPA_TRANSITION"})
    changes = {"status": payload.status, "result": payload.result, "updated_at": now()}
    if payload.evidence_refs is not None:
        changes["evidence_refs"] = payload.evidence_refs
    updated = await db.preventive_actions.find_one_and_update({"_id": action_id, "revision": payload.expected_revision, "status": action["status"]}, {"$set": changes, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "capa_action_updated", "PreventionAction", action_id, action["project_id"], {"from": action["status"], "to": payload.status})
    return updated


async def transition_analysis(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.approve" if payload.status == "CLOSED" else "causalanalysis.update")
    states = ["OPEN", "IN_PROGRESS", "IMPLEMENTED", "EFFECTIVENESS_REVIEW", "CLOSED"]
    if states.index(payload.status) != states.index(value["status"]) + 1:
        raise HTTPException(status_code=409, detail={"code": "INVALID_CAUSAL_ANALYSIS_TRANSITION"})
    if payload.status in {"IMPLEMENTED", "EFFECTIVENESS_REVIEW", "CLOSED"} and not value.get("root_cause_approved"):
        raise HTTPException(status_code=409, detail={"code": "ROOT_CAUSE_APPROVAL_REQUIRED"})
    actions = await db.preventive_actions.find({"causal_analysis_id": analysis_id}).to_list(1000)
    if payload.status == "CLOSED" and (not actions or any(item["status"] != "CLOSED" for item in actions)):
        raise HTTPException(status_code=409, detail={"code": "CAPA_ACTIONS_NOT_CLOSED"})
    updated = await db.causal_analyses.find_one_and_update({"_id": analysis_id, "revision": payload.expected_revision, "status": value["status"]}, {"$set": {"status": payload.status, "transition_note": payload.note, "updated_at": now()}, "$inc": {"revision": 1}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "causal_analysis_status_changed", "CausalAnalysis", analysis_id, value["project_id"], {"from": value["status"], "to": payload.status})
    return updated


async def generate_hypotheses(db, analysis_id, payload, user):
    value = await get_analysis(db, analysis_id, user, "causalanalysis.update")
    existing = await db.ai_results.find_one({"project_id": value["project_id"], "idempotency_key": payload.idempotency_key})
    if existing:
        if existing.get("result_type") != "CAUSAL_ANALYSIS_HYPOTHESES" or existing.get("subject_id") != analysis_id:
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
        return existing
    defects = await db.defects.find({"_id": {"$in": value["defect_ids"]}, "project_id": value["project_id"]}).to_list(500)
    historical = await db.defects.find({"project_id": value["project_id"], "_id": {"$nin": value["defect_ids"]}, "root_cause_category": {"$ne": "UNKNOWN"}}, {"_id": 1, "title": 1, "root_cause_category": 1, "root_cause_detail": 1}).limit(100).to_list(100)
    evidence = [{"artifact_type": "defect", "artifact_id": item["_id"], "authority": "PROJECT_RECORD", "text": json.dumps({key: item.get(key) for key in ["title", "severity", "status", "root_cause_category", "root_cause_detail", "injected_phase", "detected_phase", "escape_reason"]}, ensure_ascii=False, default=str)} for item in [*defects, *historical]]
    instruction = json.dumps({"task": "Đề xuất giả thuyết nguyên nhân gốc cụm lỗi, yếu tố đóng góp và TestCondition hoặc TestCase còn thiếu; không xác nhận nguyên nhân và không phê duyệt CAPA", "problem_statement": value["problem_statement"], "user_instruction": payload.instruction}, ensure_ascii=False)
    ai = await request_design_assistance("causal_analysis", value["project_id"], instruction, evidence)
    result = {"_id": new_id("AIR"), "project_id": value["project_id"], "result_type": "CAUSAL_ANALYSIS_HYPOTHESES", "subject_id": analysis_id, "candidate_only": True, "human_confirmation_required": True, "suggestions": ai.get("suggestions", []), "evidence_refs": ai.get("evidence_refs", []), "status": ai.get("status", "DEGRADED"), "confidence": ai.get("confidence", 0), "warnings": ai.get("warnings", []), "model": ai.get("model", {}), "idempotency_key": payload.idempotency_key, "created_by": user.id, "created_at": now()}
    try:
        await db.ai_results.insert_one(result)
    except DuplicateKeyError:
        return await db.ai_results.find_one({"project_id": value["project_id"], "idempotency_key": payload.idempotency_key})
    await audit(user.id, "causal_analysis_ai_hypotheses_generated", "AIResult", result["_id"], value["project_id"], {"analysis_id": analysis_id, "candidate_count": len(result["suggestions"])})
    return result
