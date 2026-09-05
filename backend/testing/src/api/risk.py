from fastapi import APIRouter, Depends, HTTPException
from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now, optimistic_patch
from src.core.database import database
from src.domain.schemas import RiskRankingGenerate, RiskRankingPatch, RiskRankingApproval


router = APIRouter(prefix="/kiem-thu", tags=["Ưu tiên rủi ro"])


def _score(test_case, version, failure_count):
    risk_weight = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.25}
    priority_weight = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.25}
    risk = risk_weight.get(str(version.get("risk", "medium")).lower(), 0.5)
    priority = priority_weight.get(str(version.get("priority", "medium")).lower(), 0.5)
    stale = 0.2 if test_case.get("status") == "NEEDS_UPDATE" else 0
    failures = min(0.4, failure_count * 0.1)
    return round(min(1.0, risk * 0.45 + priority * 0.25 + stale + failures), 4)


async def _build_items(project_id: str):
    cases = await database.value.test_cases.find(
        {"project_id": project_id, "status": {"$ne": "OBSOLETE"}},
        {"_id": 1, "test_case_key": 1, "current_version_id": 1, "status": 1},
    ).to_list(5000)
    version_ids = [item.get("current_version_id") for item in cases if item.get("current_version_id")]
    versions = await database.value.test_case_versions.find(
        {"project_id": project_id, "_id": {"$in": version_ids}},
        {"_id": 1, "test_case_id": 1, "title": 1, "risk": 1, "priority": 1},
    ).to_list(5000)
    failures = await database.value.test_results.aggregate(
        [
            {"$match": {"project_id": project_id, "status": "FAIL"}},
            {"$group": {"_id": "$test_case_version_id", "count": {"$sum": 1}}},
        ]
    ).to_list(5000)
    failure_counts = {item["_id"]: item["count"] for item in failures}
    by_case = {item["_id"]: item for item in cases}
    items = []
    for version in versions:
        case = by_case.get(version.get("test_case_id"), {})
        score = _score(case, version, failure_counts.get(version["_id"], 0))
        items.append(
            {
                "test_case_id": version.get("test_case_id"),
                "test_case_version_id": version["_id"],
                "test_case_key": case.get("test_case_key"),
                "title": version.get("title"),
                "risk": version.get("risk", "medium"),
                "priority": version.get("priority", "medium"),
                "failure_count": failure_counts.get(version["_id"], 0),
                "score": score,
                "included": True,
                "reason_codes": ["RISK", "PRIORITY"]
                + (["RECENT_FAILURE"] if failure_counts.get(version["_id"], 0) else [])
                + (["NEEDS_UPDATE"] if case.get("status") == "NEEDS_UPDATE" else []),
            }
        )
    items.sort(key=lambda item: (-item["score"], item.get("test_case_key") or ""))
    for index, item in enumerate(items, 1):
        item["rank"] = index
    return items


@router.get("/du-an/{project_id}/uu-tien-rui-ro", openapi_extra={"x-function-ids": ["RISK-01"]})
async def get_risk_ranking(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "risk.read")
    ranking = await database.value.risk_rankings.find_one(
        {"project_id": project_id}, sort=[("created_at", -1)]
    )
    if not ranking:
        return envelope({"project_id": project_id, "status": "DERIVED", "items": await _build_items(project_id)})
    return envelope(ranking, revision=ranking.get("revision", 1))


@router.post("/du-an/{project_id}/uu-tien-rui-ro", status_code=201, openapi_extra={"x-function-ids": ["RISK-02"]})
async def generate_risk_ranking(project_id: str, payload: RiskRankingGenerate, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "risk.generate")
    items = await _build_items(project_id)
    if payload.max_items:
        items = items[: payload.max_items]
    ranking = {"_id": new_id("RISK"), "project_id": project_id, "items": items, "status": "PENDING_APPROVAL", "model_version": "risk-score-v1", "revision": 1, "created_by": user.id, "created_at": now(), "updated_at": now()}
    await database.value.risk_rankings.insert_one(ranking)
    await audit(user.id, "risk_ranking_generated", "RiskRanking", ranking["_id"], project_id)
    return envelope(ranking, revision=1)


@router.patch("/uu-tien-rui-ro/{ranking_id}", openapi_extra={"x-function-ids": ["RISK-03"]})
async def review_risk_ranking(ranking_id: str, payload: RiskRankingPatch, user: CurrentUser = Depends(get_current_user)):
    ranking = await get_project_entity("risk_rankings", ranking_id, user, "risk.review")
    items = list(ranking.get("items") or [])
    by_version = {item.get("test_case_version_id"): item for item in items}
    target = by_version.get(payload.test_case_version_id)
    if not target:
        raise HTTPException(status_code=404, detail={"code": "RISK_ITEM_NOT_FOUND"})
    target.update({"included": payload.included, "review_reason": payload.reason})
    updated = await optimistic_patch("risk_rankings", ranking_id, ranking["project_id"], payload.expected_revision, {"items": list(by_version.values())})
    await audit(user.id, "risk_ranking_reviewed", "RiskRanking", ranking_id, ranking["project_id"], {"test_case_version_id": payload.test_case_version_id})
    return envelope(updated, revision=updated["revision"])


@router.post("/uu-tien-rui-ro/{ranking_id}/phe-duyet", openapi_extra={"x-function-ids": ["RISK-04"]})
async def approve_risk_ranking(ranking_id: str, payload: RiskRankingApproval, user: CurrentUser = Depends(get_current_user)):
    ranking = await get_project_entity("risk_rankings", ranking_id, user, "risk.approve")
    if ranking.get("status") == "APPROVED":
        return envelope(ranking, revision=ranking.get("revision", 1))
    if ranking.get("status") != "PENDING_APPROVAL":
        raise HTTPException(status_code=409, detail={"code": "RISK_RANKING_STATE_INVALID"})
    updated = await optimistic_patch("risk_rankings", ranking_id, ranking["project_id"], payload.expected_revision, {"status": "APPROVED", "approved_by": user.id, "approved_at": now(), "review_note": payload.review_note})
    await audit(user.id, "risk_ranking_approved", "RiskRanking", ranking_id, ranking["project_id"])
    return envelope(updated, revision=updated["revision"])
