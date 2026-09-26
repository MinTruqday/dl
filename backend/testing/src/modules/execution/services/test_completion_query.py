from fastapi import HTTPException

from src.core.common import get_project
from src.repositories.test_completion import (
    count_active_members,
    find_completion,
    list_completions,
)
from src.services.domain_policy import domain_policy


COMPLETION_POLICY = domain_policy("completion")


async def validate_people(project_id, user_ids):
    values = {value for value in user_ids if value}
    if not values:
        return
    count = await count_active_members(
        project_id,
        values,
        COMPLETION_POLICY["source_filters"]["active_membership_status"],
    )
    if count != len(values):
        raise HTTPException(
            status_code=422,
            detail={"code": COMPLETION_POLICY["error_codes"]["owner_invalid"]},
        )


async def get_completion_for_user(report_id, user, permission=None):
    report = await find_completion(report_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail={"code": COMPLETION_POLICY["error_codes"]["report_not_found"]},
        )
    await get_project(
        report["project_id"],
        user,
        permission or COMPLETION_POLICY["permissions"]["read"],
    )
    return report


async def list_completion_reports(project_id, release_id, status, limit, user):
    await get_project(project_id, user, COMPLETION_POLICY["permissions"]["read"])
    return await list_completions(project_id, release_id, status, limit)
