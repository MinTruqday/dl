from collections import defaultdict
from datetime import timedelta, timezone
import asyncio
import math

import httpx
from fastapi import APIRouter, Depends

from src.core.auth import CurrentUser, get_current_user, require_admin, require_author
from src.api.common import audit, now
from src.core.configuration import settings
from src.core.database import database
from src.domain.models import PrivacyPurgeInput
from src.services.privacy import participant_id
from src.services.research import calibration_stability, evaluation_metrics, leakage_checks


router = APIRouter(tags=["operations"])


@router.get("/operations/health")
async def platform_health(user: CurrentUser = Depends(require_admin)):
    service_urls = {
        "authentication": settings.AUTHENTICATION_URL,
        "cloud": settings.CLOUD_URL,
        "content": settings.CONTENT_URL,
        "rag": settings.RAG_URL,
        "ai": settings.AI_URL,
        "worker": settings.WORKER_URL,
        "compilation": settings.COMPILATION_URL,
        "collection": settings.COLLECTION_URL,
    }

    async def probe(name, url):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{url}/ready")
            body = (
                response.json()
                if response.headers.get("content-type", "").startswith("application/json")
                else {}
            )
            return name, {
                "status": "ready" if response.status_code == 200 else "degraded",
                "http_status": response.status_code,
                "checks": body.get("checks", {}),
            }
        except (httpx.HTTPError, ValueError):
            return name, {"status": "unavailable", "http_status": None, "checks": {}}

    results = await asyncio.gather(*(probe(name, url) for name, url in service_urls.items()))
    services = {"assessment": {"status": "ready", "http_status": 200, "checks": {}}}
    services.update(dict(results))
    return {
        "services": services,
        "ready_count": sum(1 for value in services.values() if value["status"] == "ready"),
        "unavailable_count": sum(1 for value in services.values() if value["status"] != "ready"),
        "checked_at": now(),
    }


@router.get("/dashboard/teacher")
async def teacher_dashboard(user: CurrentUser = Depends(require_author)):
    drafts = (
        await database.value.assessment_drafts.find({"owner_id": user.id})
        .sort("updated_at", -1)
        .limit(10)
        .to_list(10)
    )
    assessments = (
        await database.value.assessments.find(
            {"owner_id": user.id, "status": {"$in": ["published", "scheduled"]}}
        )
        .sort("updated_at", -1)
        .limit(10)
        .to_list(10)
    )
    review_count = await database.value.question_drafts.count_documents(
        {
            "owner_id": user.id,
            "$or": [
                {"needs_teacher_review": True},
                {"status": {"$in": ["needs_revision", "prevalidated"]}},
            ],
        }
    )
    flagged_count = await database.value.calibrations.count_documents(
        {"owner_id": user.id, "$or": [{"drift_flag": True}, {"status": "insufficient_evidence"}]}
    )
    owned_version_ids = await database.value.question_versions.distinct(
        "_id", {"owner_id": user.id}
    )
    calibrated_ids = await database.value.calibrations.distinct(
        "question_version_id",
        {"question_version_id": {"$in": owned_version_ids}, "status": "calibrated"},
    )
    response_counts = await database.value.responses.aggregate(
        [
            {
                "$match": {
                    "question_version_id": {
                        "$in": [
                            version_id
                            for version_id in owned_version_ids
                            if version_id not in set(calibrated_ids)
                        ]
                    },
                    "evidence_eligibility": "eligible",
                }
            },
            {"$group": {"_id": "$question_version_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gte": 20}}},
        ]
    ).to_list(1000)
    calibration_rows = (
        await database.value.calibrations.find(
            {"question_version_id": {"$in": owned_version_ids}, "status": "calibrated"}
        )
        .sort("created_at", -1)
        .to_list(5000)
    )
    latest_calibration = {}
    for calibration in calibration_rows:
        latest_calibration.setdefault(calibration["question_version_id"], calibration)
    prediction_rows = (
        await database.value.difficulty_estimates.find(
            {
                "question_version_id": {"$in": list(latest_calibration)},
                "$or": [{"predictor_kind": "structured"}, {"predictor_kind": {"$exists": False}}],
            }
        )
        .sort("created_at", -1)
        .to_list(5000)
    )
    latest_prediction = {}
    for prediction in prediction_rows:
        latest_prediction.setdefault(prediction["question_version_id"], prediction)
    discrepancy_alerts = []
    for version_id, calibration in latest_calibration.items():
        prediction = latest_prediction.get(version_id)
        if (
            not prediction
            or prediction.get("predicted_difficulty") is None
            or calibration.get("difficulty") is None
        ):
            continue
        gap = abs(float(prediction["predicted_difficulty"]) - float(calibration["difficulty"]))
        if gap >= 0.75 or calibration.get("drift_flag"):
            discrepancy_alerts.append(
                {
                    "question_version_id": version_id,
                    "predicted_difficulty": prediction["predicted_difficulty"],
                    "empirical_difficulty": calibration["difficulty"],
                    "gap": round(gap, 3),
                    "drift_flag": bool(calibration.get("drift_flag")),
                    "sample_size": calibration.get("sample_size", 0),
                }
            )
    return {
        "recent_drafts": drafts,
        "published_assessments": assessments,
        "review_queue_count": review_count,
        "flagged_item_count": flagged_count,
        "calibration_ready_count": len(response_counts),
        "predicted_empirical_alerts": sorted(
            discrepancy_alerts, key=lambda row: row["gap"], reverse=True
        )[:20],
    }


@router.get("/audit")
async def list_audit_events(
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor_id: str | None = None,
    user: CurrentUser = Depends(require_admin),
):
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id
    if actor_id:
        query["actor_id"] = actor_id
    events = (
        await database.value.audit_events.find(query)
        .sort("created_at", -1)
        .limit(5000)
        .to_list(5000)
    )
    if not entity_type or entity_type == "TeacherMaterialRetrieval":
        params = {"limit": 5000}
        if actor_id:
            params["requester_id"] = actor_id
        if entity_id:
            params["document_id"] = entity_id
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{settings.RAG_URL}/rag/audit/material-access",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                    params=params,
                )
            response.raise_for_status()
            for row in response.json():
                document_ids = row.get("document_ids", [])
                events.append(
                    {
                        "_id": row.get("_id"),
                        "actor_id": row.get("requester_id"),
                        "action": "teacher_material_accessed",
                        "entity_type": "TeacherMaterialRetrieval",
                        "entity_id": document_ids[0] if len(document_ids) == 1 else row.get("_id"),
                        "details": {
                            "operation": row.get("operation"),
                            "document_ids": document_ids,
                            "chunk_count": row.get("chunk_count", 0),
                            "query_sha256": row.get("query_sha256"),
                        },
                        "created_at": row.get("created_at"),
                    }
                )
        except httpx.HTTPError:
            pass
    return sorted(events, key=lambda event: str(event.get("created_at", "")), reverse=True)[:5000]


@router.get("/entities/{entity_type}/{entity_id}/history")
async def entity_history(
    entity_type: str, entity_id: str, user: CurrentUser = Depends(get_current_user)
):
    events = (
        await database.value.audit_events.find({"entity_type": entity_type, "entity_id": entity_id})
        .sort("created_at", 1)
        .to_list(1000)
    )
    if not user.is_admin and any(event.get("actor_id") != user.id for event in events):
        events = [event for event in events if event.get("actor_id") == user.id]
    return events


@router.get("/operations/models")
async def model_monitoring(user: CurrentUser = Depends(require_admin)):
    prediction_versions = await database.value.difficulty_estimates.aggregate(
        [
            {
                "$group": {
                    "_id": "$model_version",
                    "count": {"$sum": 1},
                    "average_confidence": {"$avg": "$confidence"},
                }
            }
        ]
    ).to_list(1000)
    calibration_jobs = (
        await database.value.calibration_runs.find().sort("created_at", -1).limit(100).to_list(100)
    )
    drift_alerts = (
        await database.value.calibrations.find({"drift_flag": True})
        .sort("created_at", -1)
        .limit(100)
        .to_list(100)
    )
    low_confidence = await database.value.difficulty_estimates.count_documents(
        {"confidence": {"$lt": 0.5}}
    )
    calibration_rows = (
        await database.value.calibrations.find(
            {"status": "calibrated", "difficulty": {"$ne": None}}
        )
        .sort("created_at", -1)
        .to_list(100000)
    )
    latest_calibration = {}
    for calibration in calibration_rows:
        latest_calibration.setdefault(calibration["question_version_id"], calibration)
    current_version_ids = await database.value.questions.distinct(
        "current_version_id", {"status": {"$ne": "archived"}}
    )
    monitored_version_ids = list(set(latest_calibration) | set(current_version_ids))
    estimate_rows = (
        await database.value.difficulty_estimates.find(
            {
                "question_version_id": {"$in": monitored_version_ids},
                "predicted_difficulty": {"$ne": None},
            }
        )
        .sort("created_at", -1)
        .to_list(100000)
    )
    latest_estimate = {}
    errors_by_model = defaultdict(list)
    seen_estimate_models = set()
    for estimate in estimate_rows:
        version_id = estimate["question_version_id"]
        latest_estimate.setdefault(version_id, estimate)
        calibration = latest_calibration.get(version_id)
        model_version = str(estimate.get("model_version", "unknown"))
        model_key = (version_id, model_version)
        if calibration and model_key not in seen_estimate_models:
            seen_estimate_models.add(model_key)
            errors_by_model[model_version].append(
                float(estimate["predicted_difficulty"]) - float(calibration["difficulty"])
            )
    prediction_error_metrics = [
        {
            "model_version": model_version,
            "count": len(errors),
            "mae": round(sum(abs(error) for error in errors) / len(errors), 4),
            "rmse": round(math.sqrt(sum(error * error for error in errors) / len(errors)), 4),
        }
        for model_version, errors in sorted(errors_by_model.items())
        if errors
    ]
    failed_jobs = [job for job in calibration_jobs if job.get("status") == "failed"]
    version_rows = await database.value.question_versions.find(
        {"_id": {"$in": current_version_ids}}
    ).to_list(100000)
    coverage = defaultdict(int)
    for version in version_rows:
        version_id = version["_id"]
        curriculum = (version.get("curriculum_links") or [{}])[0]
        subject = str(curriculum.get("subject") or "unmapped")
        calibration = latest_calibration.get(version_id)
        estimate = latest_estimate.get(version_id)
        difficulty = (
            calibration.get("difficulty")
            if calibration
            else estimate.get("predicted_difficulty")
            if estimate
            else None
        )
        level = (
            str(max(1, min(5, round(float(difficulty))))) if difficulty is not None else "unknown"
        )
        coverage[(subject, level)] += 1
    return {
        "prediction_versions": prediction_versions,
        "calibration_jobs": calibration_jobs,
        "drift_alerts": drift_alerts,
        "low_confidence_prediction_count": low_confidence,
        "prediction_error_metrics": prediction_error_metrics,
        "failed_jobs": failed_jobs,
        "bank_coverage": [
            {"subject": subject, "difficulty_level": level, "count": count}
            for (subject, level), count in sorted(coverage.items())
        ],
    }


@router.get("/operations/privacy-policy")
async def privacy_policy(user: CurrentUser = Depends(require_admin)):
    return {
        "pii_retention_days": settings.ASSESSMENT_PII_RETENTION_DAYS,
        "research_response_identity": "hmac_pseudonymous_participant_id",
        "response_contains_raw_student_id": False,
        "completed_attempt_action": "remove_direct_student_identifier_after_retention",
    }


@router.post("/operations/privacy/purge")
async def purge_expired_pii(payload: PrivacyPurgeInput, user: CurrentUser = Depends(require_admin)):
    cutoff = now() - timedelta(days=payload.older_than_days)
    attempts = await database.value.attempts.find(
        {
            "status": {"$in": ["completed", "submitted", "timed_out"]},
            "submitted_at": {"$lt": cutoff},
            "student_id": {"$type": "string"},
            "pii_purged_at": {"$exists": False},
        },
        {"_id": 1, "assignment_id": 1, "student_id": 1},
    ).to_list(100000)
    assignment_ids = set()
    responses_pseudonymized = 0
    for attempt in attempts:
        pseudonym = participant_id(attempt["student_id"])
        await database.value.attempts.update_one(
            {"_id": attempt["_id"], "student_id": attempt["student_id"]},
            {
                "$set": {
                    "student_id": f"anon:{pseudonym}",
                    "participant_id": pseudonym,
                    "pii_purged_at": now(),
                }
            },
        )
        if attempt.get("assignment_id"):
            assignment_ids.add(attempt["assignment_id"])
        response_result = await database.value.responses.update_many(
            {
                "attempt_id": attempt["_id"],
                "$or": [{"student_id": {"$exists": True}}, {"participant_id": {"$exists": False}}],
            },
            {
                "$set": {"participant_id": pseudonym, "pii_purged_at": now()},
                "$unset": {"student_id": ""},
            },
        )
        responses_pseudonymized += response_result.modified_count
    assignments = await database.value.assignments.find(
        {
            "_id": {"$in": list(assignment_ids)},
            "student_id": {"$type": "string"},
            "pii_purged_at": {"$exists": False},
        },
        {"_id": 1, "student_id": 1},
    ).to_list(100000)
    for assignment in assignments:
        await database.value.assignments.update_one(
            {"_id": assignment["_id"], "student_id": assignment["student_id"]},
            {
                "$set": {
                    "student_id": f"anon:{participant_id(assignment['student_id'])}",
                    "participant_id": participant_id(assignment["student_id"]),
                    "pii_purged_at": now(),
                }
            },
        )
    await audit(
        user.id,
        "assessment_pii_retention_applied",
        "PrivacyRetentionRun",
        f"retention-{int(cutoff.timestamp())}",
        {
            "attempt_count": len(attempts),
            "assignment_count": len(assignments),
            "response_count": responses_pseudonymized,
            "older_than_days": payload.older_than_days,
        },
    )
    return {
        "cutoff": cutoff,
        "attempts_pseudonymized": len(attempts),
        "assignments_pseudonymized": len(assignments),
        "responses_pseudonymized": responses_pseudonymized,
    }


def utc_value(value):
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@router.get("/research/evaluation")
async def research_evaluation(user: CurrentUser = Depends(require_author)):
    versions = await database.value.question_versions.find({"owner_id": user.id}).to_list(10000)
    version_ids = [version["_id"] for version in versions]
    calibration_snapshots = (
        await database.value.calibrations.find(
            {"owner_id": user.id, "question_version_id": {"$in": version_ids}}
        )
        .sort("created_at", 1)
        .to_list(100000)
    )
    calibrations = [
        calibration
        for calibration in calibration_snapshots
        if calibration.get("status") == "calibrated"
    ]
    latest_calibration = {}
    for calibration in calibrations:
        latest_calibration[calibration["question_version_id"]] = calibration
    predictions = (
        await database.value.difficulty_estimates.find(
            {"owner_id": user.id, "question_version_id": {"$in": list(latest_calibration)}}
        )
        .sort("created_at", 1)
        .to_list(100000)
    )
    judgments = (
        await database.value.teacher_judgments.find(
            {
                "teacher_id": user.id,
                "question_version_id": {"$in": list(latest_calibration)},
                "research_eligible": True,
            }
        )
        .sort("created_at", 1)
        .to_list(100000)
    )
    predictions_by_version = defaultdict(list)
    judgments_by_version = defaultdict(list)
    for prediction in predictions:
        predictions_by_version[prediction["question_version_id"]].append(prediction)
    for judgment in judgments:
        judgments_by_version[judgment["question_version_id"]].append(judgment)
    versions_by_id = {version["_id"]: version for version in versions}
    rows = []
    for version_id, calibration in latest_calibration.items():
        calibration_time = utc_value(calibration.get("created_at"))
        cold_start_predictions = [
            prediction
            for prediction in predictions_by_version[version_id]
            if calibration_time
            and utc_value(prediction.get("created_at"))
            and utc_value(prediction.get("created_at")) < calibration_time
        ]
        blind_judgments = [
            judgment
            for judgment in judgments_by_version[version_id]
            if calibration_time
            and utc_value(judgment.get("created_at"))
            and utc_value(judgment.get("created_at")) < calibration_time
        ]
        structured_predictions = [
            prediction
            for prediction in cold_start_predictions
            if prediction.get("predictor_kind", "structured") == "structured"
        ]
        direct_predictions = [
            prediction
            for prediction in cold_start_predictions
            if prediction.get("predictor_kind") == "llm_direct"
        ]
        prediction = structured_predictions[-1] if structured_predictions else None
        direct_prediction = direct_predictions[-1] if direct_predictions else None
        teacher = blind_judgments[-1] if blind_judgments else None
        version = versions_by_id[version_id]
        curriculum = (version.get("curriculum_links") or [{}])[0]
        ai_value = prediction.get("predicted_difficulty") if prediction else None
        direct_value = direct_prediction.get("predicted_difficulty") if direct_prediction else None
        teacher_value = teacher.get("estimated_difficulty") if teacher else None
        rows.append(
            {
                "question_id": version.get("question_id"),
                "question_version_id": version_id,
                "subject": curriculum.get("subject"),
                "target_program": curriculum.get("target_program"),
                "ai": ai_value,
                "ai_confidence": prediction.get("confidence") if prediction else None,
                "structured": ai_value,
                "structured_confidence": prediction.get("confidence") if prediction else None,
                "llm_direct": direct_value,
                "llm_direct_confidence": direct_prediction.get("confidence")
                if direct_prediction
                else None,
                "heuristic": prediction.get("heuristic_difficulty") if prediction else None,
                "nearest_historical": prediction.get("nearest_historical_difficulty")
                if prediction
                else None,
                "teacher": teacher_value,
                "teacher_confidence": {"low": 0.33, "medium": 0.66, "high": 1.0}.get(
                    teacher.get("self_confidence")
                )
                if teacher
                else None,
                "hybrid": (ai_value + teacher_value) / 2
                if ai_value is not None and teacher_value is not None
                else None,
                "empirical": calibration.get("difficulty"),
                "sample_size": calibration.get("sample_size", 0),
                "model_version": prediction.get("model_version") if prediction else None,
                "llm_direct_model_version": direct_prediction.get("provider_model_version")
                or direct_prediction.get("model_version")
                if direct_prediction
                else None,
                "feature_schema_version": prediction.get("feature_schema_version")
                if prediction
                else None,
                "training_data_window": prediction.get("training_data_window")
                if prediction
                else None,
                "curriculum_version": prediction.get("curriculum_version") if prediction else None,
                "normalization_version": prediction.get("normalization_version")
                if prediction
                else None,
                "feature_snapshot": prediction.get("feature_snapshot") if prediction else {},
                "prediction_created_at": utc_value(prediction.get("created_at"))
                if prediction
                else None,
                "calibration_created_at": calibration_time,
                "is_first_exposure_only": True,
            }
        )
    subgroup_rows = defaultdict(list)
    for row in rows:
        subgroup_rows[(row.get("subject"), row.get("target_program"))].append(row)
    model_rows = defaultdict(list)
    for row in rows:
        if row.get("model_version"):
            model_rows[f"structured:{row['model_version']}"].append(row)
        if row.get("llm_direct_model_version"):
            model_rows[f"llm_direct:{row['llm_direct_model_version']}"].append(row)
    calibration_history = defaultdict(list)
    for calibration in calibration_snapshots:
        calibration_history[calibration["question_version_id"]].append(calibration)
    return {
        "item_count": len(rows),
        "ai": evaluation_metrics(rows, "ai"),
        "structured": evaluation_metrics(rows, "structured"),
        "llm_direct": evaluation_metrics(rows, "llm_direct"),
        "heuristic": evaluation_metrics(rows, "heuristic"),
        "nearest_historical": evaluation_metrics(rows, "nearest_historical"),
        "teacher": evaluation_metrics(rows, "teacher"),
        "hybrid": evaluation_metrics(rows, "hybrid"),
        "subgroups": [
            {
                "subject": key[0],
                "target_program": key[1],
                "ai": evaluation_metrics(values, "ai"),
                "structured": evaluation_metrics(values, "structured"),
                "llm_direct": evaluation_metrics(values, "llm_direct"),
                "teacher": evaluation_metrics(values, "teacher"),
            }
            for key, values in sorted(subgroup_rows.items(), key=lambda item: str(item[0]))
        ],
        "model_versions": [
            {
                "model": key,
                "metrics": evaluation_metrics(
                    values, "llm_direct" if key.startswith("llm_direct:") else "structured"
                ),
            }
            for key, values in sorted(model_rows.items())
        ],
        "calibration_stability": [
            {"question_version_id": version_id, **calibration_stability(values)}
            for version_id, values in sorted(calibration_history.items())
        ],
        "leakage": leakage_checks(rows),
        "rows": rows,
    }
