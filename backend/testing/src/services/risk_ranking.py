from fastapi import HTTPException

from src.core.auth import CurrentUser
from src.core.common import audit, get_project, get_project_entity, new_id, now, optimistic_patch
from src.repositories.analysis import analysis_repository
from src.domain.contracts import RiskRankingApproval, RiskRankingGenerate, RiskRankingPatch
from src.services.domain_policy import domain_policy


RISK_POLICY = domain_policy("risk_scoring")


class RiskRankingService:
    @staticmethod
    async def current(project_id: str, user: CurrentUser):
        policy = RISK_POLICY
        await get_project(project_id, user, "risk.read")
        ranking = await analysis_repository.find_latest_risk_ranking(project_id)
        if ranking:
            return ranking
        return {
            "project_id": project_id,
            "status": policy["derived_status"],
            "items": await RiskRankingService._build_items(project_id),
        }

    @staticmethod
    async def generate(
        project_id: str,
        payload: RiskRankingGenerate,
        user: CurrentUser,
    ):
        await get_project(project_id, user, "risk.generate")
        items = await RiskRankingService._build_items(project_id)
        if payload.max_items:
            items = items[: payload.max_items]
        policy = domain_policy("risk_scoring")
        ranking = {
            "_id": new_id(policy["item_id_prefix"]),
            "project_id": project_id,
            "items": items,
            "status": policy["pending_approval_status"],
            "model_version": policy["model_version"],
            "revision": 1,
            "created_by": user.id,
            "created_at": now(),
            "updated_at": now(),
        }
        await analysis_repository.insert_risk_ranking(ranking)
        await audit(user.id, "risk_ranking_generated", "RiskRanking", ranking["_id"], project_id)
        return ranking

    @staticmethod
    async def review(
        ranking_id: str,
        payload: RiskRankingPatch,
        user: CurrentUser,
    ):
        policy = RISK_POLICY
        ranking = await get_project_entity("risk_rankings", ranking_id, user, "risk.review")
        items = list(ranking.get("items") or [])
        by_version = {item.get("test_case_version_id"): item for item in items}
        target = by_version.get(payload.test_case_version_id)
        if not target:
            raise HTTPException(status_code=404, detail={"code": policy["item_not_found_code"]})
        target.update({"included": payload.included, "review_reason": payload.reason})
        updated = await optimistic_patch(
            "risk_rankings",
            ranking_id,
            ranking["project_id"],
            payload.expected_revision,
            {"items": list(by_version.values())},
        )
        await audit(
            user.id,
            "risk_ranking_reviewed",
            "RiskRanking",
            ranking_id,
            ranking["project_id"],
            {"test_case_version_id": payload.test_case_version_id},
        )
        return updated

    @staticmethod
    async def approve(
        ranking_id: str,
        payload: RiskRankingApproval,
        user: CurrentUser,
    ):
        policy = RISK_POLICY
        ranking = await get_project_entity("risk_rankings", ranking_id, user, "risk.approve")
        if ranking.get("status") == policy["approved_status"]:
            return ranking
        if ranking.get("status") != policy["pending_approval_status"]:
            raise HTTPException(status_code=409, detail={"code": policy["state_invalid_code"]})
        updated = await optimistic_patch(
            "risk_rankings",
            ranking_id,
            ranking["project_id"],
            payload.expected_revision,
            {
                "status": policy["approved_status"],
                "approved_by": user.id,
                "approved_at": now(),
                "review_note": payload.review_note,
            },
        )
        await audit(
            user.id,
            "risk_ranking_approved",
            "RiskRanking",
            ranking_id,
            ranking["project_id"],
        )
        return updated

    @staticmethod
    def _score(test_case: dict, version: dict, failure_count: int):
        policy = domain_policy("risk_scoring")
        levels = policy["levels"]
        default = policy["default_level"]
        risk = levels.get(str(version.get("risk", "medium")).lower(), default)
        priority = levels.get(str(version.get("priority", "medium")).lower(), default)
        stale = (
            policy["stale_increment"]
            if test_case.get("status") == policy["stale_test_case_status"]
            else 0
        )
        failures = min(
            policy["failure_maximum"],
            failure_count * policy["failure_increment"],
        )
        return round(
            min(
                1,
                risk * policy["risk_weight"]
                + priority * policy["priority_weight"]
                + stale
                + failures,
            ),
            4,
        )

    @staticmethod
    async def _build_items(project_id: str):
        policy = domain_policy("risk_scoring")
        reason_codes = policy["reason_codes"]
        cases = await analysis_repository.list_current_test_cases(
            project_id,
            policy["current_test_case_excluded_status"],
            {"_id": 1, "test_case_key": 1, "current_version_id": 1, "status": 1},
        )
        version_ids = [
            item.get("current_version_id") for item in cases if item.get("current_version_id")
        ]
        versions = await analysis_repository.list_test_case_versions(
            project_id,
            version_ids,
            {"_id": 1, "test_case_id": 1, "title": 1, "risk": 1, "priority": 1},
        )
        failures = await analysis_repository.failure_counts(project_id)
        failure_counts = {item["_id"]: item["count"] for item in failures}
        by_case = {item["_id"]: item for item in cases}
        items = []
        for version in versions:
            case = by_case.get(version.get("test_case_id"), {})
            failure_count = failure_counts.get(version["_id"], 0)
            items.append(
                {
                    "test_case_id": version.get("test_case_id"),
                    "test_case_version_id": version["_id"],
                    "test_case_key": case.get("test_case_key"),
                    "title": version.get("title"),
                    "risk": version.get("risk", "medium"),
                    "priority": version.get("priority", "medium"),
                    "failure_count": failure_count,
                    "score": RiskRankingService._score(case, version, failure_count),
                    "included": True,
                    "reason_codes": list(reason_codes["base"])
                    + ([reason_codes["failure"]] if failure_count else [])
                    + (
                        [reason_codes["stale"]]
                        if case.get("status") == policy["stale_test_case_status"]
                        else []
                    ),
                }
            )
        items.sort(key=lambda item: (-item["score"], item.get("test_case_key") or ""))
        for index, item in enumerate(items, 1):
            item["rank"] = index
        return items
