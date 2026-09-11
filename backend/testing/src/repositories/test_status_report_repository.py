from pymongo import ReturnDocument

from src.core.database import database


async def find_report(report_id, project_id=None):
    query = {"_id": report_id}
    if project_id:
        query["project_id"] = project_id
    return await database.value.test_status_reports.find_one(query)


async def list_reports(project_id, test_plan_id=None, release_id=None, status=None, limit=500):
    query = {"project_id": project_id}
    if test_plan_id:
        query["test_plan_id"] = test_plan_id
    if release_id:
        query["release_id"] = release_id
    if status:
        query["status"] = status
    return await database.value.test_status_reports.find(query).sort([("created_at", -1), ("sequence", -1)]).limit(limit).to_list(limit)


async def update_report(report_id, project_id, expected_revision, allowed_statuses, changes):
    return await database.value.test_status_reports.find_one_and_update(
        {
            "_id": report_id,
            "project_id": project_id,
            "revision": expected_revision,
            "status": {"$in": sorted(allowed_statuses)},
        },
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )


async def next_sequence(project_id, test_plan_id, release_id):
    counter = await database.value.counters.find_one_and_update(
        {"_id": f"{project_id}:test-status-report:{test_plan_id}:{release_id or 'none'}"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(counter["value"])
