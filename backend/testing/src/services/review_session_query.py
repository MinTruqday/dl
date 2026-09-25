from fastapi import HTTPException

from src.core.common import get_project
from src.repositories.review import review_repository
from src.services.domain_policy import domain_policy


REVIEW_POLICY = domain_policy("review_session")


async def validate_members(project_id, user_ids):
    policy = REVIEW_POLICY
    values = list(dict.fromkeys(item for item in user_ids if item))
    count = await review_repository.count_active_members(
        project_id, values, policy["active_member_status"]
    )
    if count != len(values):
        raise HTTPException(
            status_code=422,
            detail={"code": policy["participant_not_member_code"]},
        )


async def get_review(review_id, user, permission=None):
    policy = REVIEW_POLICY
    value = await review_repository.find_review(review_id)
    if not value:
        raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
    await get_project(value["project_id"], user, permission or policy["read_permission"])
    return value


async def list_reviews(project_id, user, status, artifact_type):
    policy = REVIEW_POLICY
    await get_project(project_id, user, policy["read_permission"])
    query = {"project_id": project_id}
    if status:
        query["status"] = status
    if artifact_type:
        query["artifact_type"] = artifact_type
    items = await review_repository.list_reviews(query, policy["list_limit"])
    return {"items": items, "total": len(items)}
