import json

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.core.database import database
from src.domain.test_completion import completion_hash, completion_snapshot
from src.repositories.test_completion import find_completion, list_completions, next_completion_sequence, update_completion
from src.services.exit_criteria import evaluate_exit_criteria, quality_gate_status
from src.services.design_assistance import request_design_assistance


OPEN_DEFECT_STATUSES = {"NEW", "CONFIRMED", "IN_PROGRESS", "READY_FOR_RETEST", "REOPENED"}


async def validate_people(project_id, user_ids):
    values = {value for value in user_ids if value}
    if not values:
        return
    count = await database.value.project_members.count_documents({"project_id": project_id, "user_id": {"$in": sorted(values)}, "status": "ACTIVE"})
    if count != len(values):
        raise HTTPException(status_code=422, detail={"code": "COMPLETION_OWNER_INVALID"})


def default_completion_recommendation(gate, unresolved_items, residual_risks):
    if gate == "FAIL" or any(item.get("severity") in {"blocker", "critical", "BLOCKER", "CRITICAL"} for item in unresolved_items if isinstance(item, dict)):
        return "NOT_READY"
    if gate != "PASS":
        return "CONTINUE_TESTING"
    if residual_risks:
        return "READY_WITH_RISK"
    return "READY_FOR_RELEASE"


async def reevaluate_completion_exit_criteria(plan, snapshot, completed_run_ids):
    evaluations = evaluate_exit_criteria(plan.get("quality_targets", []), snapshot.get("metrics") or {}, completed_run_ids)
    criterion_ids = {item["criterion_id"] for item in evaluations}
    evaluations.extend(
        dict(item)
        for item in snapshot.get("exit_criteria_evaluation", [])
        if item.get("criterion_id") not in criterion_ids
    )
    overrides = await database.value.test_monitoring_overrides.find({"snapshot_id": snapshot["_id"]}).sort("created_at", 1).to_list(1000)
    latest = {item["criterion_id"]: item for item in overrides}
    for item in evaluations:
        override = latest.get(item["criterion_id"])
        if override:
            item.update({"status": override["status"], "overridden": True, "override": override})
    return evaluations


async def get_completion_for_user(report_id, user, permission="testcompletion.read"):
    report = await find_completion(report_id)
    if not report:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(report["project_id"], user, permission)
    return report


async def list_completion_reports(project_id, release_id, status, limit, user):
    await get_project(project_id, user, "testcompletion.read")
    return await list_completions(project_id, release_id, status, limit)


async def completion_sources(project_id, snapshot, plan, build_id):
    release_id = snapshot.get("release_id") or plan.get("release_id")
    if not release_id:
        raise HTTPException(status_code=409, detail={"code": "COMPLETION_RELEASE_REQUIRED"})
    release = await database.value.releases.find_one({"_id": release_id, "project_id": project_id})
    if not release:
        raise HTTPException(status_code=422, detail={"code": "INVALID_RELEASE"})
    build = await database.value.builds.find_one({"_id": build_id, "project_id": project_id})
    if not build:
        raise HTTPException(status_code=422, detail={"code": "INVALID_BUILD"})
    if build.get("release_id") and build["release_id"] != release_id:
        raise HTTPException(status_code=422, detail={"code": "BUILD_RELEASE_MISMATCH"})
    strategy_version_id = plan.get("strategy_version_id")
    if not strategy_version_id:
        raise HTTPException(status_code=409, detail={"code": "COMPLETION_STRATEGY_VERSION_REQUIRED"})
    strategy = await database.value.test_strategies.find_one({"_id": strategy_version_id, "project_id": project_id})
    if not strategy or not strategy.get("snapshot_hash") or strategy.get("snapshot_hash") != plan.get("strategy_snapshot_hash"):
        raise HTTPException(status_code=409, detail={"code": "COMPLETION_STRATEGY_SNAPSHOT_INVALID"})
    source_state = snapshot.get("source_state") or {}
    run_states = [item for item in source_state.get("runs", []) if item.get("id")]
    run_ids = [item["id"] for item in run_states]
    run_records = await database.value.test_runs.find({"_id": {"$in": run_ids}, "project_id": project_id}).to_list(10000) if run_ids else []
    runs_by_id = {item["_id"]: item for item in run_records}
    runs = [
        {
            **runs_by_id.get(item["id"], {}),
            "_id": item["id"],
            "revision": item.get("revision"),
            "status": item.get("status"),
            "frozen_scope_hash": item.get("scope_hash"),
            "test_case_version_ids": item.get("test_case_version_ids", runs_by_id.get(item["id"], {}).get("test_case_version_ids", [])),
            "release_id": item.get("release_id", runs_by_id.get(item["id"], {}).get("release_id")),
            "build_id": item.get("build_id", runs_by_id.get(item["id"], {}).get("build_id")),
            "environment_id": item.get("environment_id", runs_by_id.get(item["id"], {}).get("environment_id")),
        }
        for item in run_states
    ]
    result_states = [item for item in source_state.get("results", []) if item.get("id")]
    result_ids = [item["id"] for item in result_states]
    result_records = await database.value.test_results.find({"_id": {"$in": result_ids}, "project_id": project_id}).to_list(50000) if result_ids else []
    results_by_id = {item["_id"]: item for item in result_records}
    results = [{**results_by_id.get(item["id"], {}), "_id": item["id"], "revision": item.get("revision"), "status": item.get("status")} for item in result_states]
    defect_states = [item for item in source_state.get("defects", []) if item.get("id")]
    defect_ids = [item["id"] for item in defect_states]
    defect_records = await database.value.defects.find({"_id": {"$in": defect_ids}, "project_id": project_id}).to_list(10000) if defect_ids else []
    defects_by_id = {item["_id"]: item for item in defect_records}
    defects = [{**defects_by_id.get(item["id"], {}), "_id": item["id"], "revision": item.get("revision"), "status": item.get("status"), "severity": item.get("severity")} for item in defect_states]
    environment_ids = sorted({item.get("environment_id") for item in runs if item.get("environment_id")})
    environments = await database.value.test_environments.find({"_id": {"$in": environment_ids}, "project_id": project_id}).to_list(1000) if environment_ids else []
    data_sets = await database.value.data_sets.find({"project_id": project_id, "status": {"$ne": "ARCHIVED"}}, {"_id": 1, "name": 1, "revision": 1, "status": 1}).to_list(5000)
    automation = await database.value.automation_script_drafts.find({"project_id": project_id, "status": {"$in": ["APPROVED", "EXPORTED"]}}, {"_id": 1, "status": 1, "revision": 1, "framework": 1, "language": 1}).to_list(5000)
    status_reports = await database.value.test_status_reports.find({"project_id": project_id, "release_id": release_id, "status": {"$in": ["APPROVED", "PUBLISHED"]}}, {"_id": 1, "status": 1, "approved_snapshot_hash": 1}).to_list(5000)
    archived_testcases = await database.value.test_cases.find({"project_id": project_id, "status": {"$in": ["ARCHIVED", "OBSOLETE"]}}, {"_id": 1, "status": 1, "current_version_id": 1}).to_list(5000)
    archived_documents = await database.value.requirement_documents.find({"project_id": project_id, "status": "ARCHIVED"}, {"_id": 1, "content_hash": 1}).to_list(5000)
    return release, build, strategy, runs, results, defects, environments, data_sets, automation, status_reports, archived_testcases, archived_documents


async def create_completion_report(project_id, payload, user):
    await get_project(project_id, user, "testcompletion.create")
    if payload.idempotency_key:
        existing = await database.value.test_completion_reports.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
        if existing:
            if existing.get("monitoring_snapshot_id") != payload.snapshot_id or existing.get("build_id") != payload.build_id:
                raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
            return existing
    snapshot = await database.value.test_monitoring_snapshots.find_one({"_id": payload.snapshot_id, "project_id": project_id})
    if not snapshot:
        raise HTTPException(status_code=422, detail={"code": "INVALID_MONITORING_SNAPSHOT"})
    plan = await database.value.test_plans.find_one({"_id": snapshot["test_plan_id"], "project_id": project_id})
    if not plan or plan.get("status") != "APPROVED" or plan.get("approved_snapshot_hash") != snapshot.get("plan_snapshot_hash"):
        raise HTTPException(status_code=409, detail={"code": "COMPLETION_PLAN_SNAPSHOT_INVALID"})
    sources = await completion_sources(project_id, snapshot, plan, payload.build_id)
    release, build, strategy, runs, results, defects, environments, data_sets, automation, status_reports, archived_testcases, archived_documents = sources
    residual_risks = [item.model_dump() for item in payload.residual_risks]
    improvement_actions = [item.model_dump() for item in payload.improvement_actions]
    await validate_people(project_id, [*[item["owner_id"] for item in residual_risks], *[item.get("accepted_by") for item in residual_risks], *[item["owner_id"] for item in improvement_actions]])
    if any(item.get("acceptance") != "PENDING" for item in residual_risks):
        raise HTTPException(status_code=422, detail={"code": "RESIDUAL_RISK_DECISION_ENDPOINT_REQUIRED"})
    completed_run_ids = sorted(item["_id"] for item in runs if item.get("status") == "COMPLETED")
    metrics = snapshot.get("metrics") or {}
    exit_evaluation = await reevaluate_completion_exit_criteria(plan, snapshot, completed_run_ids)
    gate = quality_gate_status(exit_evaluation)
    open_defects = [item for item in defects if item.get("status") in OPEN_DEFECT_STATUSES]
    generated_unresolved = [
        {"type": "DEFECT", "defect_id": item["_id"], "title": item.get("title"), "severity": item.get("severity"), "status": item.get("status"), "owner_id": item.get("assignee")}
        for item in open_defects
    ]
    omitted = [
        {"type": "OMITTED_TEST", "test_result_id": result["_id"], "test_run_id": result.get("test_run_id"), "test_case_version_id": result.get("test_case_version_id"), "status": result.get("status"), "reason": result.get("reason") or result.get("notes") or "Chưa hoàn tất"}
        for result in results
        if result.get("status") in {"NOT_RUN", "IN_PROGRESS", "SKIPPED"}
    ]
    unresolved_items = [*generated_unresolved, *omitted, *payload.unresolved_items]
    scope_runs = [
        {"run_id": item["_id"], "revision": item.get("revision"), "status": item.get("status"), "frozen_scope_hash": item.get("frozen_scope_hash"), "test_case_version_ids": item.get("test_case_version_ids", []), "release_id": item.get("release_id"), "build_id": item.get("build_id"), "environment_id": item.get("environment_id")}
        for item in runs
    ]
    testware = [
        {"type": "TEST_CASE_VERSION", "items": (snapshot.get("source_state") or {}).get("test_case_versions", [])},
        {"type": "DATA_SET", "items": data_sets},
        {"type": "AUTOMATION_SCRIPT", "items": automation},
        {"type": "STATUS_REPORT", "items": status_reports},
        *payload.testware_handover,
    ]
    archived = [{"type": "TEST_CASE", "items": archived_testcases}, {"type": "REQUIREMENT_DOCUMENT", "items": archived_documents}, *payload.archived_artifacts]
    environment_closure = [
        {"environment_id": item["_id"], "name": item.get("name"), "availability": item.get("availability"), "status": item.get("status"), "revision": item.get("revision")}
        for item in environments
    ] + payload.environment_closure
    recommendation = payload.recommendation or default_completion_recommendation(gate, unresolved_items, residual_risks)
    timestamp = now()
    report = {
        "_id": new_id("TCP"), "project_id": project_id, "idempotency_key": payload.idempotency_key, "test_plan_id": plan["_id"], "release_id": release["_id"], "build_id": build["_id"],
        "strategy_version_id": strategy["_id"], "strategy_snapshot_hash": strategy["snapshot_hash"], "monitoring_snapshot_id": snapshot["_id"],
        "scope_snapshot": {"plan_revision": snapshot.get("plan_revision"), "plan_snapshot_hash": snapshot.get("plan_snapshot_hash"), "scope_in": (plan.get("approved_snapshot") or {}).get("scope_in", []), "scope_out": (plan.get("approved_snapshot") or {}).get("scope_out", []), "runs": scope_runs, "source_fingerprint": snapshot.get("source_fingerprint")},
        "completed_run_ids": completed_run_ids,
        "execution_summary": {key: metrics.get(key) for key in ("planned_test_count", "executed_test_count", "execution_percent", "pass", "fail", "blocked", "skipped", "not_applicable", "pass_rate")},
        "coverage_summary": {key: metrics.get(key) for key in ("requirement_coverage", "acceptance_criteria_coverage", "test_condition_coverage", "risk_coverage", "api_coverage", "nfr_coverage")},
        "defect_summary": {"total": len(defects), "open": len(open_defects), "open_blocker": metrics.get("open_blocker", 0), "open_critical": metrics.get("open_critical", 0), "resolved": metrics.get("resolved", 0), "reopened": metrics.get("reopened", 0)},
        "unresolved_items": unresolved_items, "residual_risks": residual_risks, "exit_criteria_evaluation": exit_evaluation,
        "quality_gate_status": gate, "deviations": [*snapshot.get("deviations", []), *payload.deviations], "testware_handover": testware,
        "archived_artifacts": archived, "environment_closure": environment_closure, "lessons_learned": payload.lessons_learned,
        "improvement_actions": improvement_actions, "recommendation": recommendation, "executive_summary": "", "closure_summary": "", "residual_risk_summary": "", "recommendation_rationale": "", "sign_offs": [], "status": "DRAFT",
        "sequence": await next_completion_sequence(project_id, release["_id"]), "revision": 1, "review_history": [], "approval_history": [],
        "created_by": user.id, "created_at": timestamp, "updated_at": timestamp,
    }
    try:
        await database.value.test_completion_reports.insert_one(report)
    except DuplicateKeyError:
        existing = await database.value.test_completion_reports.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key}) if payload.idempotency_key else None
        if not existing:
            raise
        if existing.get("monitoring_snapshot_id") != payload.snapshot_id or existing.get("build_id") != payload.build_id:
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
        return existing
    await audit(user.id, "test_completion_report_created", "TestCompletionReport", report["_id"], project_id, {"release_id": release["_id"], "snapshot_id": snapshot["_id"], "quality_gate_status": gate})
    return report


async def update_completion_report(report_id, payload, user):
    report = await get_completion_for_user(report_id, user, "testcompletion.update")
    if report["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "COMPLETION_REPORT_IMMUTABLE"})
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    changes.pop("expected_revision", None)
    if "residual_risks" in changes or "improvement_actions" in changes:
        await validate_people(report["project_id"], [*[item["owner_id"] for item in changes.get("residual_risks", [])], *[item.get("accepted_by") for item in changes.get("residual_risks", [])], *[item["owner_id"] for item in changes.get("improvement_actions", [])]])
    if "residual_risks" in changes:
        existing_risks = {item.get("risk_id"): item for item in report.get("residual_risks", [])}
        for item in changes["residual_risks"]:
            previous = existing_risks.get(item.get("risk_id")) or {}
            decision = (item.get("acceptance"), item.get("acceptance_reason"), item.get("accepted_by"))
            previous_decision = (previous.get("acceptance"), previous.get("acceptance_reason"), previous.get("accepted_by"))
            if item.get("acceptance") != "PENDING" and decision != previous_decision:
                raise HTTPException(status_code=422, detail={"code": "RESIDUAL_RISK_DECISION_ENDPOINT_REQUIRED", "risk_id": item.get("risk_id")})
    changes["updated_at"] = now()
    updated = await update_completion(report_id, report["project_id"], payload.expected_revision, {"DRAFT"}, changes)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "COMPLETION_REPORT_REVISION_CONFLICT"})
    await audit(user.id, "test_completion_report_updated", "TestCompletionReport", report_id, report["project_id"], {"fields": sorted(changes)})
    return updated


async def completion_ai_result(report, payload, user, capability, result_type, task):
    if report["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "COMPLETION_REPORT_IMMUTABLE"})
    existing = await database.value.ai_results.find_one({"project_id": report["project_id"], "idempotency_key": payload.idempotency_key})
    if existing:
        if existing.get("result_type") != result_type or existing.get("subject_id") != report["_id"]:
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
        return existing
    evidence = [{"artifact_type": "test_completion_report", "artifact_id": report["_id"], "authority": "PROJECT_RECORD", "text": json.dumps({key: report.get(key) for key in ("execution_summary", "coverage_summary", "defect_summary", "unresolved_items", "residual_risks", "exit_criteria_evaluation", "quality_gate_status", "deviations", "environment_closure", "lessons_learned", "improvement_actions", "recommendation")}, ensure_ascii=False, default=str)}]
    instruction = json.dumps({"task": task, "user_instruction": payload.instruction}, ensure_ascii=False)
    ai = await request_design_assistance(capability, report["project_id"], instruction, evidence)
    result = {"_id": new_id("AIR"), "project_id": report["project_id"], "result_type": result_type, "subject_id": report["_id"], "candidate_only": True, "human_confirmation_required": True, "suggestions": ai.get("suggestions", []), "evidence_refs": ai.get("evidence_refs", []), "status": ai.get("status", "DEGRADED"), "confidence": ai.get("confidence", 0), "warnings": ai.get("warnings", []), "model": ai.get("model", {}), "idempotency_key": payload.idempotency_key, "created_by": user.id, "created_at": now()}
    try:
        await database.value.ai_results.insert_one(result)
    except DuplicateKeyError:
        return await database.value.ai_results.find_one({"project_id": report["project_id"], "idempotency_key": payload.idempotency_key})
    await audit(user.id, f"{capability}_generated", "AIResult", result["_id"], report["project_id"], {"report_id": report["_id"], "candidate_count": len(result["suggestions"])})
    return result


async def generate_completion_narrative(report_id, payload, user):
    report = await get_completion_for_user(report_id, user, "testcompletion.update")
    return await completion_ai_result(report, payload, user, "completion_report_narrative", "COMPLETION_REPORT_NARRATIVE", "Soạn bản nháp diễn giải hoàn tất kiểm thử chỉ từ số liệu và bằng chứng không tự đổi quality gate recommendation hay phê duyệt báo cáo")


async def cluster_completion_lessons(report_id, payload, user):
    report = await get_completion_for_user(report_id, user, "testcompletion.update")
    if not report.get("lessons_learned"):
        raise HTTPException(status_code=422, detail={"code": "LESSONS_LEARNED_REQUIRED"})
    return await completion_ai_result(report, payload, user, "lessons_learned_clustering", "LESSONS_LEARNED_CLUSTERS", "Gom nhóm bài học kinh nghiệm theo chủ đề giữ nguyên căn cứ bằng source_indices và chỉ đề xuất ứng viên cải tiến không tự áp dụng")


async def decide_residual_risk(report_id, risk_id, payload, user):
    report = await get_completion_for_user(report_id, user, "testcompletion.review")
    if report["status"] not in {"DRAFT", "IN_REVIEW"}:
        raise HTTPException(status_code=409, detail={"code": "COMPLETION_REPORT_IMMUTABLE"})
    membership = await database.value.project_members.find_one({"project_id": report["project_id"], "user_id": user.id, "status": "ACTIVE"})
    risks = [dict(item) for item in report.get("residual_risks", [])]
    risk = next((item for item in risks if item.get("risk_id") == risk_id), None)
    if not risk:
        raise HTTPException(status_code=404, detail={"code": "RESIDUAL_RISK_NOT_FOUND"})
    if risk.get("owner_id") != user.id and (membership or {}).get("project_role") not in {"QA_LEAD", "BA"}:
        raise HTTPException(status_code=403, detail={"code": "RESIDUAL_RISK_DECISION_DENIED"})
    risk.update({"acceptance": payload.acceptance, "acceptance_reason": payload.reason, "accepted_by": user.id, "accepted_at": now()})
    updated = await update_completion(report_id, report["project_id"], payload.expected_revision, {"DRAFT", "IN_REVIEW"}, {"residual_risks": risks, "updated_at": now()})
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "COMPLETION_REPORT_REVISION_CONFLICT"})
    await audit(user.id, "test_completion_residual_risk_decided", "TestCompletionReport", report_id, report["project_id"], {"risk_id": risk_id, "acceptance": payload.acceptance, "reason": payload.reason})
    return updated


async def sign_off_completion(report_id, payload, user):
    report = await get_completion_for_user(report_id, user, "testcompletion.review")
    if report["status"] != "IN_REVIEW":
        raise HTTPException(status_code=409, detail={"code": "COMPLETION_SIGN_OFF_STATE_INVALID"})
    membership = await database.value.project_members.find_one({"project_id": report["project_id"], "user_id": user.id, "status": "ACTIVE"})
    if not membership:
        raise HTTPException(status_code=403, detail={"code": "PROJECT_MEMBERSHIP_REQUIRED"})
    sign_offs = [item for item in report.get("sign_offs", []) if item.get("user_id") != user.id]
    sign_offs.append({"user_id": user.id, "role": membership.get("project_role"), "decision": payload.decision, "note": payload.note, "at": now()})
    updated = await update_completion(report_id, report["project_id"], payload.expected_revision, {"IN_REVIEW"}, {"sign_offs": sign_offs, "updated_at": now()})
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "COMPLETION_REPORT_REVISION_CONFLICT"})
    await audit(user.id, "test_completion_signed_off", "TestCompletionReport", report_id, report["project_id"], {"decision": payload.decision, "role": membership.get("project_role")})
    return updated


async def transition_completion(report_id, payload, user, source, target, permission, action):
    report = await get_completion_for_user(report_id, user, permission)
    if target == "APPROVED":
        qa_approved = any(item.get("role") == "QA_LEAD" and item.get("decision") == "APPROVE" for item in report.get("sign_offs", []))
        if not qa_approved:
            raise HTTPException(status_code=409, detail={"code": "QA_LEAD_SIGN_OFF_REQUIRED"})
        if any(item.get("acceptance") == "PENDING" for item in report.get("residual_risks", [])):
            raise HTTPException(status_code=409, detail={"code": "RESIDUAL_RISK_ACCEPTANCE_REQUIRED"})
        if any(item.get("decision") == "REJECT" for item in report.get("sign_offs", [])):
            raise HTTPException(status_code=409, detail={"code": "COMPLETION_REJECTION_UNRESOLVED"})
    timestamp = now()
    event = {"actor_id": user.id, "action": target, "note": payload.note, "at": timestamp}
    history_field = "approval_history" if target in {"APPROVED", "CLOSED"} else "review_history"
    changes = {"status": target, "updated_at": timestamp, history_field: [*report.get(history_field, []), event]}
    if target == "IN_REVIEW":
        changes.update({"submitted_by": user.id, "submitted_at": timestamp})
    elif target == "DRAFT":
        changes.update({"reviewed_by": user.id, "reviewed_at": timestamp, "change_request": payload.note, "sign_offs": []})
    elif target == "APPROVED":
        changes.update({"approved_by": user.id, "approved_at": timestamp, "approved_snapshot": completion_snapshot(report), "approved_snapshot_hash": completion_hash(report)})
    elif target == "CLOSED":
        changes.update({"closed_by": user.id, "closed_at": timestamp})
    updated = await update_completion(report_id, report["project_id"], payload.expected_revision, {source}, changes)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "COMPLETION_TRANSITION_CONFLICT", "expected_status": source})
    await audit(user.id, action, "TestCompletionReport", report_id, report["project_id"], {"from": source, "to": target, "note": payload.note})
    return updated
