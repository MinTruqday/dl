import json

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.repositories.test_design import test_design_repository
from src.services.design_assistance import ai_contract_metadata, request_design_assistance
from src.services.domain_policy import domain_policy
from src.services.generation import PerformanceScenario, SecurityCandidate, validated_suggestions


async def requirement_evidence(project_id, requirement_version_ids):
    policy = domain_policy("design_suggestion")
    query = {"project_id": project_id}
    if requirement_version_ids:
        query["_id"] = {"$in": list(dict.fromkeys(requirement_version_ids))}
    versions = await test_design_repository.list_requirement_evidence(
        query, policy["requirement_limit"]
    )
    if requirement_version_ids and len(versions) != len(set(requirement_version_ids)):
        raise HTTPException(status_code=422, detail={"code": policy["invalid_requirement_code"]})
    return versions, [
        {
            "artifact_type": "requirement_version",
            "artifact_id": item.get("requirement_id"),
            "artifact_version_id": item["_id"],
            "authority": policy["project_baseline_authority"],
            "text": " ".join(
                filter(
                    None,
                    [str(item.get("title") or ""), str(item.get("plain_text_projection") or "")],
                )
            )[: policy["evidence_text_limit"]],
        }
        for item in versions
    ]


class DesignSuggestionService:
    @staticmethod
    async def list_security(project_id, user):
        await get_project(project_id, user, "ai.generate_security_tests")
        return await test_design_repository.list_security_suggestions(
            project_id, domain_policy("design_suggestion")["list_limit"]
        )

    @staticmethod
    async def generate_security(project_id, payload, user):
        policy = domain_policy("design_suggestion")
        await get_project(project_id, user, "ai.generate_security_tests")
        existing = await test_design_repository.find_security_suggestion(
            project_id, payload.idempotency_key
        )
        if existing:
            return existing, {}
        versions, evidence = await requirement_evidence(project_id, payload.requirement_version_ids)
        ai_result = await request_design_assistance(
            "security_test_generation",
            project_id,
            json.dumps({"categories": payload.categories}, ensure_ascii=False),
            evidence
            + [
                {
                    "artifact_type": "design_request",
                    "artifact_id": payload.idempotency_key,
                    "authority": policy["user_request_authority"],
                    "text": json.dumps(
                        {"categories": payload.categories, "context": payload.context},
                        ensure_ascii=False,
                    ),
                }
            ],
        )
        candidates = validated_suggestions(ai_result, SecurityCandidate)
        version_ids = {item["_id"] for item in versions}
        if {item["category"] for item in candidates} != set(payload.categories) or any(
            not set(item["requirement_version_ids"]) <= version_ids for item in candidates
        ):
            raise HTTPException(502, detail={"code": policy["generation_invalid_code"]})
        candidates = [
            {
                **item,
                "candidate_id": f"{policy['security_candidate_prefix']}{index}",
                "status": policy["suggested_status"],
                "origin": policy["ai_origin"],
            }
            for index, item in enumerate(candidates, 1)
        ]
        timestamp = now()
        ai_contract = ai_contract_metadata(ai_result)
        result = {
            "_id": new_id(policy["security_result_prefix"]),
            "project_id": project_id,
            "result_type": policy["security_result_type"],
            "categories": payload.categories,
            "requirement_version_ids": [item["_id"] for item in versions],
            "candidates": candidates,
            "model_suggestions": ai_result.get("suggestions", []),
            **ai_contract,
            "ai_contract": ai_contract,
            "ai_status": ai_contract["status"],
            "latency_ms": ai_result.get("latency_ms"),
            "status": policy["pending_review_status"],
            "generation_status": ai_result.get("status", policy["success_status"]),
            "candidate_only": True,
            "vulnerability_scan_performed": False,
            "human_confirmation_required": True,
            "idempotency_key": payload.idempotency_key,
            "revision": 1,
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await test_design_repository.insert_security_suggestion(result)
        except DuplicateKeyError:
            existing = await test_design_repository.find_security_suggestion(
                project_id, payload.idempotency_key
            )
            if existing:
                return existing, {}
            raise
        await audit(
            user.id,
            "security_test_suggestions_generated",
            "SecurityTestSuggestion",
            result["_id"],
            project_id,
            {"candidate_count": len(result["candidates"])},
        )
        return result, {
            "status": ai_result.get("status", policy["success_status"]),
            "degraded_mode": ai_result.get("degraded_mode"),
        }

    @staticmethod
    async def list_performance(project_id, user):
        await get_project(project_id, user, "ai.generate_performance_plan")
        return await test_design_repository.list_performance_drafts(
            project_id, domain_policy("design_suggestion")["list_limit"]
        )

    @staticmethod
    async def generate_performance(project_id, payload, user):
        policy = domain_policy("design_suggestion")
        await get_project(project_id, user, "ai.generate_performance_plan")
        existing = await test_design_repository.find_performance_draft(
            project_id, payload.idempotency_key
        )
        if existing:
            return existing, {}
        versions, evidence = await requirement_evidence(project_id, payload.requirement_version_ids)
        ai_result = await request_design_assistance(
            "performance_plan_generation",
            project_id,
            json.dumps(
                {
                    "workload_types": payload.workload_types,
                    "target_virtual_users": payload.target_virtual_users,
                    "target_requests_per_second": payload.target_requests_per_second,
                    "duration_minutes": payload.duration_minutes,
                    "objective": payload.objective,
                },
                ensure_ascii=False,
            ),
            evidence
            + [
                {
                    "artifact_type": "design_request",
                    "artifact_id": payload.idempotency_key,
                    "authority": policy["user_request_authority"],
                    "text": json.dumps(
                        {
                            "objective": payload.objective,
                            "workload_types": payload.workload_types,
                            "target_virtual_users": payload.target_virtual_users,
                            "target_requests_per_second": payload.target_requests_per_second,
                            "duration_minutes": payload.duration_minutes,
                            "context": payload.context,
                        },
                        ensure_ascii=False,
                    ),
                }
            ],
        )
        scenarios = validated_suggestions(ai_result, PerformanceScenario)
        if {item["workload_type"] for item in scenarios} != set(payload.workload_types):
            raise HTTPException(502, detail={"code": policy["generation_invalid_code"]})
        scenarios = [
            {**item, "scenario_id": f"{policy['performance_scenario_prefix']}{index}"}
            for index, item in enumerate(scenarios, 1)
        ]
        timestamp = now()
        ai_contract = ai_contract_metadata(ai_result)
        result = {
            "_id": new_id(policy["performance_result_prefix"]),
            "project_id": project_id,
            "name": payload.name,
            "objective": payload.objective,
            "requirement_version_ids": [item["_id"] for item in versions],
            "workload": {
                "target_virtual_users": payload.target_virtual_users,
                "target_requests_per_second": payload.target_requests_per_second,
                "duration_minutes": payload.duration_minutes,
            },
            "scenarios": scenarios,
            "metrics": [
                {"key": policy["metric_keys"]["response_time"], "threshold": payload.response_time_p95_ms},
                {"key": policy["metric_keys"]["error_rate"], "threshold": payload.maximum_error_rate},
                {"key": policy["metric_keys"]["throughput"], "threshold": payload.target_requests_per_second},
            ],
            "model_suggestions": ai_result.get("suggestions", []),
            **ai_contract,
            "ai_contract": ai_contract,
            "ai_status": ai_contract["status"],
            "latency_ms": ai_result.get("latency_ms"),
            "status": policy["draft_status"],
            "generation_status": ai_result.get("status", policy["success_status"]),
            "load_execution_performed": False,
            "human_confirmation_required": True,
            "idempotency_key": payload.idempotency_key,
            "revision": 1,
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await test_design_repository.insert_performance_draft(result)
        except DuplicateKeyError:
            existing = await test_design_repository.find_performance_draft(
                project_id, payload.idempotency_key
            )
            if existing:
                return existing, {}
            raise
        await audit(
            user.id,
            "performance_plan_draft_generated",
            "PerformanceTestPlanDraft",
            result["_id"],
            project_id,
            {"scenario_count": len(result["scenarios"])},
        )
        return result, {
            "status": ai_result.get("status", policy["success_status"]),
            "degraded_mode": ai_result.get("degraded_mode"),
        }
