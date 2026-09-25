from fastapi import HTTPException

from src.repositories.test_completion import (
    find_build,
    find_release,
    find_strategy,
    list_active_data_sets,
    list_approved_automation,
    list_approved_status_reports,
    list_archived_requirement_documents,
    list_archived_test_cases,
    list_defects,
    list_environments,
    list_results,
    list_runs,
)
from src.services.domain_policy import domain_policy


COMPLETION_POLICY = domain_policy("completion")


async def completion_sources(project_id, snapshot, plan, build_id):
    policy = COMPLETION_POLICY
    codes = policy["error_codes"]
    source_filters = policy["source_filters"]
    release_id = snapshot.get("release_id") or plan.get("release_id")
    if not release_id:
        raise HTTPException(status_code=409, detail={"code": codes["release_required"]})
    release = await find_release(project_id, release_id)
    if not release:
        raise HTTPException(status_code=422, detail={"code": codes["invalid_release"]})
    build = await find_build(project_id, build_id)
    if not build:
        raise HTTPException(status_code=422, detail={"code": codes["invalid_build"]})
    if build.get("release_id") and build["release_id"] != release_id:
        raise HTTPException(status_code=422, detail={"code": codes["build_release_mismatch"]})
    strategy_version_id = plan.get("strategy_version_id")
    if not strategy_version_id:
        raise HTTPException(
            status_code=409, detail={"code": codes["strategy_version_required"]}
        )
    strategy = await find_strategy(project_id, strategy_version_id)
    if (
        not strategy
        or not strategy.get("snapshot_hash")
        or strategy.get("snapshot_hash") != plan.get("strategy_snapshot_hash")
    ):
        raise HTTPException(
            status_code=409, detail={"code": codes["strategy_snapshot_invalid"]}
        )
    source_state = snapshot.get("source_state") or {}
    run_states = [item for item in source_state.get("runs", []) if item.get("id")]
    run_ids = [item["id"] for item in run_states]
    run_records = await list_runs(project_id, run_ids)
    runs_by_id = {item["_id"]: item for item in run_records}
    runs = [
        {
            **runs_by_id.get(item["id"], {}),
            "_id": item["id"],
            "revision": item.get("revision"),
            "status": item.get("status"),
            "frozen_scope_hash": item.get("scope_hash"),
            "test_case_version_ids": item.get(
                "test_case_version_ids",
                runs_by_id.get(item["id"], {}).get("test_case_version_ids", []),
            ),
            "release_id": item.get("release_id", runs_by_id.get(item["id"], {}).get("release_id")),
            "build_id": item.get("build_id", runs_by_id.get(item["id"], {}).get("build_id")),
            "environment_id": item.get(
                "environment_id", runs_by_id.get(item["id"], {}).get("environment_id")
            ),
        }
        for item in run_states
    ]
    result_states = [item for item in source_state.get("results", []) if item.get("id")]
    result_ids = [item["id"] for item in result_states]
    result_records = await list_results(project_id, result_ids)
    results_by_id = {item["_id"]: item for item in result_records}
    results = [
        {
            **results_by_id.get(item["id"], {}),
            "_id": item["id"],
            "revision": item.get("revision"),
            "status": item.get("status"),
        }
        for item in result_states
    ]
    defect_states = [item for item in source_state.get("defects", []) if item.get("id")]
    defect_ids = [item["id"] for item in defect_states]
    defect_records = await list_defects(project_id, defect_ids)
    defects_by_id = {item["_id"]: item for item in defect_records}
    defects = [
        {
            **defects_by_id.get(item["id"], {}),
            "_id": item["id"],
            "revision": item.get("revision"),
            "status": item.get("status"),
            "severity": item.get("severity"),
        }
        for item in defect_states
    ]
    environment_ids = sorted(
        {item.get("environment_id") for item in runs if item.get("environment_id")}
    )
    environments = await list_environments(project_id, environment_ids)
    data_sets = await list_active_data_sets(
        project_id, source_filters["data_set_excluded_status"]
    )
    automation = await list_approved_automation(
        project_id, source_filters["automation_statuses"]
    )
    status_reports = await list_approved_status_reports(
        project_id, release_id, source_filters["status_report_statuses"]
    )
    archived_testcases = await list_archived_test_cases(
        project_id, source_filters["archived_test_case_statuses"]
    )
    archived_documents = await list_archived_requirement_documents(
        project_id, source_filters["archived_requirement_document_status"]
    )
    return (
        release,
        build,
        strategy,
        runs,
        results,
        defects,
        environments,
        data_sets,
        automation,
        status_reports,
        archived_testcases,
        archived_documents,
    )


def handover_records(artifact_type, items, storage_prefix):
    handover_policy = COMPLETION_POLICY["handover"]
    records = []
    for raw_item in items:
        item = raw_item if isinstance(raw_item, dict) else {"id": raw_item}
        artifact_id = str(item.get("_id") or item.get("id") or "")
        if not artifact_id:
            continue
        records.append(
            {
                "artifact_type": artifact_type,
                "artifact_id": artifact_id,
                "artifact_version_id": artifact_id
                if artifact_type in set(handover_policy["versioned_artifact_types"])
                else None,
                "handover_to": handover_policy["destination"],
                "storage_location": f"{storage_prefix}/{artifact_id}",
                "status": handover_policy["ready_status"],
                "note": "",
            }
        )
    return records
