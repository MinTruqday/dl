from src.core.database import database


async def find_snapshot(snapshot_id, project_id=None):
    query = {"_id": snapshot_id}
    if project_id:
        query["project_id"] = project_id
    return await database.value.test_monitoring_snapshots.find_one(query)


async def list_snapshots(project_id, test_plan_id=None, release_id=None, limit=100):
    query = {"project_id": project_id}
    if test_plan_id:
        query["test_plan_id"] = test_plan_id
    if release_id:
        query["release_id"] = release_id
    return await database.value.test_monitoring_snapshots.find(query).sort("snapshot_at", -1).limit(limit).to_list(limit)


async def list_control_actions(project_id, snapshot_id=None, status=None, limit=500):
    query = {"project_id": project_id}
    if snapshot_id:
        query["snapshot_id"] = snapshot_id
    if status:
        query["status"] = status
    return await database.value.test_control_actions.find(query).sort("updated_at", -1).limit(limit).to_list(limit)
