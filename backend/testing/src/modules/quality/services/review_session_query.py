from fastapi import HTTPException

from src.core.common import get_project
from src.repositories.review import review_repository





async def validate_members(project_id, user_ids):
    
    values = list(dict.fromkeys(item for item in user_ids if item))
    count = await review_repository.count_active_members(
        project_id, values, 'ACTIVE'
    )
    if count != len(values):
        raise HTTPException(
            status_code=422,
            detail={"code": 'REVIEW_PARTICIPANT_NOT_PROJECT_MEMBER'},
        )


async def get_review(review_id, user, permission=None):
    
    value = await review_repository.find_review(review_id)
    if not value:
        raise HTTPException(status_code=404, detail={"code": 'ENTITY_NOT_FOUND'})
    await get_project(value["project_id"], user, permission or 'reviewsession.read')
    return value


async def list_reviews(project_id, user, status, artifact_type):
    
    await get_project(project_id, user, 'reviewsession.read')
    query = {"project_id": project_id}
    if status:
        query["status"] = status
    if artifact_type:
        query["artifact_type"] = artifact_type
    items = await review_repository.list_reviews(query, 500)
    return {"items": items, "total": len(items)}
