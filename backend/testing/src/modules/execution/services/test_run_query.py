import csv
import io
import re

from fastapi import HTTPException

from src.core.common import (
    get_project,
    get_project_entity,
    load_user_identities,
    page_payload,
    sort_spec,
)
from src.repositories.test_run import test_run_repository
from src.services.domain_policy import domain_policy


async def list_test_run_records(
    project_id,
    user,
    name="",
    release="",
    release_id="",
    build="",
    build_id="",
    environment="",
    environment_id="",
    status="",
    created_by="",
    page=1,
    page_size=50,
    sort="-updated_at",
):
    policy = domain_policy("test_run")
    await get_project(project_id, user, "testrun.read")
    query = {"project_id": project_id}
    if name:
        query["name"] = {"$regex": re.escape(name), "$options": "i"}
    if status:
        query["status"] = status
    for field, value in {
        "release": release,
        "release_id": release_id,
        "build": build,
        "build_id": build_id,
        "environment": environment,
        "environment_id": environment_id,
        "created_by": created_by,
    }.items():
        if value:
            query[field] = value
    sort_field, direction = sort_spec(
        sort,
        set(policy["sort_fields"]),
    )
    total = await test_run_repository.count_runs(query)
    items = await test_run_repository.list_runs(
        query, sort_field, direction, (page - 1) * page_size, page_size
    )
    return page_payload(items, page, page_size, total)


async def list_test_result_records(project_id, user, status=""):
    policy = domain_policy("test_run")
    await get_project(project_id, user, "testrun.read")
    query = {"project_id": project_id}
    statuses = [value.strip() for value in status.split(",") if value.strip()]
    if statuses:
        allowed = set(policy["result_statuses"])
        if not set(statuses) <= allowed:
            raise HTTPException(
                status_code=422, detail={"code": policy["invalid_result_status_code"]}
            )
        query["status"] = {"$in": statuses}
    return await test_run_repository.list_results(
        query, policy["result_list_limit"], "updated_at", -1
    )


async def get_test_run_record(run_id, user):
    policy = domain_policy("test_run")
    run = await get_project_entity("test_runs", run_id, user, "testrun.read")
    versions = await test_run_repository.list_versions(
        run["test_case_version_ids"], policy["detail_limit"]
    )
    results = await test_run_repository.list_results(
        {"test_run_id": run_id}, policy["detail_limit"]
    )
    defects = await test_run_repository.list_defects_for_results(
        run["project_id"], [item["_id"] for item in results], policy["detail_limit"]
    )
    return {**run, "test_case_versions": versions, "results": results, "defects": defects}


async def build_test_run_report(run_id, user):
    policy = domain_policy("test_run")
    run = await get_project_entity("test_runs", run_id, user, "report.export")
    versions = await test_run_repository.list_versions(
        run["test_case_version_ids"], policy["detail_limit"]
    )
    results = await test_run_repository.list_results(
        {"test_run_id": run_id}, policy["detail_limit"]
    )
    by_result = {item["test_case_version_id"]: item for item in results}
    identities = await load_user_identities(item.get("executed_by") for item in results)
    fields = policy["report_fields"]
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for version in versions:
        result = by_result.get(version["_id"], {})
        identity = identities.get(result.get("executed_by"), {})
        writer.writerow(
            {
                "run_id": run_id,
                "run_name": run["name"],
                "environment": run.get("environment"),
                "build": run.get("build"),
                "test_case_key": version.get("test_case_key"),
                "test_case_version": version.get("version"),
                "title": version.get("title"),
                "result": result.get("status", policy["not_run_status"]),
                "executed_by": result.get("executed_by"),
                "executed_by_name": identity.get("full_name"),
                "executed_by_email": identity.get("email"),
                "executed_at": result.get("executed_at")
                or result.get("completed_at")
                or result.get("updated_at"),
                "note": result.get("note"),
            }
        )
    return stream.getvalue()
