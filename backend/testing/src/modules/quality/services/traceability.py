import csv
import io

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, get_project_entity, get_project_role, new_id, now, visible_defect
from src.core.metrics import STALE, TRACE_ACCEPTANCE_RATE, UNCOVERED
from src.repositories.traceability import traceability_repository
from src.services.domain_policy import domain_policy

TRACE_POLICY = domain_policy("traceability")


def percent(value, total):
    return round(value * 100 / total, 2) if total else 0


class TraceabilityService:
    @staticmethod
    async def validate_artifact(artifact_type, artifact_id, project_id):
        mapping = TRACE_POLICY["artifact_collections"]
        if not await traceability_repository.artifact_exists(
            mapping[artifact_type], artifact_id, project_id
        ):
            raise HTTPException(status_code=422, detail={"code": TRACE_POLICY["missing_artifact_code"]})

    @classmethod
    async def create_link(cls, payload, project_id, user):
        if project_id is not None and payload.project_id != project_id:
            raise HTTPException(status_code=422, detail={"code": TRACE_POLICY["project_mismatch_code"]})
        await get_project(payload.project_id, user, "trace.create")
        await cls.validate_artifact(payload.source_type, payload.source_id, payload.project_id)
        await cls.validate_artifact(payload.target_type, payload.target_id, payload.project_id)
        query = {
            "project_id": payload.project_id,
            "source_type": payload.source_type,
            "source_id": payload.source_id,
            "target_type": payload.target_type,
            "target_id": payload.target_id,
            "link_type": payload.link_type,
        }
        existing = await traceability_repository.find_link(query)
        if existing:
            return existing
        link = {
            "_id": new_id(TRACE_POLICY["link_id_prefix"]),
            **payload.model_dump(),
            "status": TRACE_POLICY["confirmed_status"]
            if payload.origin == TRACE_POLICY["manual_origin"]
            else TRACE_POLICY["suggested_status"],
            "revision": 1,
            "created_by": user.id,
            "created_at": now(),
            "updated_at": now(),
        }
        try:
            await traceability_repository.insert_link(link)
        except DuplicateKeyError:
            return await traceability_repository.find_link(query)
        await audit(user.id, "trace_link_created", "TraceLink", link["_id"], payload.project_id)
        return link

    @staticmethod
    async def get_link(link_id, user):
        return await get_project_entity("trace_links", link_id, user, "trace.read")

    @classmethod
    async def confirm_link(cls, link_id, user, project_id=None):
        return await cls.review_link(
            link_id, TRACE_POLICY["confirmed_status"], user, project_id
        )

    @classmethod
    async def reject_link(cls, link_id, user, project_id=None):
        return await cls.review_link(
            link_id, TRACE_POLICY["rejected_status"], user, project_id
        )

    @staticmethod
    async def review_link(link_id, status, user, project_id=None):
        permission = (
            "trace.confirm"
            if status == TRACE_POLICY["confirmed_status"]
            else "trace.review"
        )
        link = await get_project_entity("trace_links", link_id, user, permission)
        if project_id is not None and link["project_id"] != project_id:
            raise HTTPException(status_code=422, detail={"code": TRACE_POLICY["project_mismatch_code"]})
        if link.get("status") == status:
            return link
        if link.get("status") != TRACE_POLICY["suggested_status"]:
            raise HTTPException(status_code=409, detail={"code": TRACE_POLICY["invalid_transition_code"]})
        timestamp = now()
        updated = await traceability_repository.transition_link(
            link_id,
            link["project_id"],
            TRACE_POLICY["suggested_status"],
            {
                "status": status,
                "reviewed_by": user.id,
                "reviewed_at": timestamp,
                "updated_at": timestamp,
            },
        )
        if not updated:
            raise HTTPException(status_code=409, detail={"code": TRACE_POLICY["decision_conflict_code"]})
        reviewed = await traceability_repository.count_links(
            {
                "project_id": updated["project_id"],
                "status": {"$in": TRACE_POLICY["reviewed_statuses"]},
            }
        )
        confirmed = await traceability_repository.count_links(
            {"project_id": updated["project_id"], "status": TRACE_POLICY["confirmed_status"]}
        )
        TRACE_ACCEPTANCE_RATE.set(confirmed / reviewed if reviewed else 0)
        await audit(user.id, f"trace_link_{status.lower()}", "TraceLink", link_id, updated["project_id"])
        return updated

    @staticmethod
    async def revoke_link(link_id, project_id, user):
        link = await get_project_entity("trace_links", link_id, user, "trace.revoke")
        if project_id is not None and link["project_id"] != project_id:
            raise HTTPException(status_code=422, detail={"code": TRACE_POLICY["project_mismatch_code"]})
        if link.get("status") == TRACE_POLICY["revoked_status"]:
            return link
        if link.get("status") not in set(TRACE_POLICY["revocable_statuses"]):
            raise HTTPException(status_code=409, detail={"code": TRACE_POLICY["invalid_transition_code"]})
        timestamp = now()
        updated = await traceability_repository.transition_link(
            link_id,
            link["project_id"],
            link["status"],
            {
                "status": TRACE_POLICY["revoked_status"],
                "revoked_by": user.id,
                "revoked_at": timestamp,
                "updated_at": timestamp,
            },
        )
        if not updated:
            raise HTTPException(status_code=409, detail={"code": TRACE_POLICY["decision_conflict_code"]})
        await audit(user.id, "trace_link_revoked", "TraceLink", link_id, updated["project_id"])
        return updated

    @staticmethod
    async def matrix(project_id, user):
        await get_project(project_id, user, "trace.read")
        role = await get_project_role(project_id, user.id)
        requirements = await traceability_repository.list_records(
            "requirements",
            {"project_id": project_id},
            TRACE_POLICY["matrix_requirement_limit"],
            ("requirement_key", 1),
        )
        versions = await traceability_repository.list_records(
            "requirement_versions",
            {"_id": {"$in": [item["current_version_id"] for item in requirements]}},
            TRACE_POLICY["matrix_requirement_limit"],
        )
        criteria = await traceability_repository.list_records(
            "acceptance_criteria",
            {"project_id": project_id},
            TRACE_POLICY["matrix_criterion_limit"],
        )
        tests = await traceability_repository.list_records(
            "test_cases",
            {"project_id": project_id},
            TRACE_POLICY["matrix_test_limit"],
            ("test_case_key", 1),
        )
        test_versions = await traceability_repository.list_records(
            "test_case_versions",
            {
                "_id": {
                    "$in": [
                        item["current_version_id"]
                        for item in tests
                        if item.get("current_version_id")
                    ]
                }
            },
            TRACE_POLICY["matrix_test_limit"],
        )
        defects = await traceability_repository.list_records(
            "defects",
            {
                "project_id": project_id,
                "status": {"$nin": TRACE_POLICY["open_defect_excluded_statuses"]},
            },
            TRACE_POLICY["defect_limit"],
        )
        defects = [visible_defect(item, role) for item in defects]
        links = await traceability_repository.list_records(
            "trace_links", {"project_id": project_id}, TRACE_POLICY["link_limit"]
        )
        linked_requirement_version_ids = {
            item.get("source_id")
            for item in links
            if item.get("source_type") == TRACE_POLICY["requirement_source_type"]
            and item.get("source_id")
        }
        linked_test_case_version_ids = {
            item.get("target_id")
            for item in links
            if item.get("target_type") == TRACE_POLICY["test_version_target_type"]
            and item.get("target_id")
        }
        missing_requirement_versions = linked_requirement_version_ids - {item["_id"] for item in versions}
        missing_test_case_versions = linked_test_case_version_ids - {item["_id"] for item in test_versions}
        if missing_requirement_versions:
            versions.extend(
                await traceability_repository.list_records(
                    "requirement_versions",
                    {"project_id": project_id, "_id": {"$in": list(missing_requirement_versions)}},
                    TRACE_POLICY["matrix_requirement_limit"],
                )
            )
        if missing_test_case_versions:
            test_versions.extend(
                await traceability_repository.list_records(
                    "test_case_versions",
                    {"project_id": project_id, "_id": {"$in": list(missing_test_case_versions)}},
                    TRACE_POLICY["matrix_test_limit"],
                )
            )
        requirement_versions_by_id = {item["_id"]: item for item in versions}
        criteria_by_id = {item["_id"]: item for item in criteria}
        test_versions_by_id = {item["_id"]: item for item in test_versions}
        obsolete_requirement_ids = {
            item["_id"]
            for item in requirements
            if item.get("status") == TRACE_POLICY["obsolete_status"]
        }
        obsolete_requirement_versions = await traceability_repository.list_records(
            "requirement_versions",
            {"project_id": project_id, "requirement_id": {"$in": list(obsolete_requirement_ids)}},
            TRACE_POLICY["matrix_criterion_limit"],
        )
        obsolete_requirement_version_ids = {item["_id"] for item in obsolete_requirement_versions}
        obsolete_criterion_ids = {
            item["_id"] for item in criteria if item.get("requirement_version_id") in obsolete_requirement_version_ids
        }
        obsolete_test_ids = {
            item["_id"]
            for item in tests
            if item.get("status") == TRACE_POLICY["obsolete_status"]
        }
        obsolete_test_versions = await traceability_repository.list_records(
            "test_case_versions",
            {"project_id": project_id, "test_case_id": {"$in": list(obsolete_test_ids)}},
            TRACE_POLICY["test_limit"],
        )
        obsolete_test_version_ids = {item["_id"] for item in obsolete_test_versions}
        enriched_links = []
        for link in links:
            reasons = []
            if link.get("source_id") in obsolete_requirement_version_ids | obsolete_criterion_ids:
                reasons.append(TRACE_POLICY["obsolete_source_reason"])
            if link.get("target_id") in obsolete_test_version_ids:
                reasons.append(TRACE_POLICY["obsolete_target_reason"])
            source = (
                requirement_versions_by_id.get(link.get("source_id"))
                if link.get("source_type") == TRACE_POLICY["requirement_source_type"]
                else criteria_by_id.get(link.get("source_id"))
            )
            target = test_versions_by_id.get(link.get("target_id"))
            source_label = (
                f"{source.get('requirement_key', '')} v{source.get('version', '')} {source.get('title', '')}".strip()
                if link.get("source_type") == TRACE_POLICY["requirement_source_type"] and source
                else source.get("key", link.get("source_id")) if source else link.get("source_id")
            )
            target_label = f"{target.get('test_case_key', '')} v{target.get('version', '')} {target.get('title', '')}".strip() if target else link.get("target_id")
            enriched_links.append({**link, "source_label": source_label, "target_label": target_label, "obsolete": bool(reasons), "obsolete_reasons": reasons})
        return {
            "requirements": requirements,
            "requirement_versions": versions,
            "acceptance_criteria": criteria,
            "test_cases": tests,
            "test_case_versions": test_versions,
            "trace_links": enriched_links,
            "defects": defects,
        }

    @staticmethod
    async def coverage(project_id, build, build_id, release, release_id, user):
        await get_project(project_id, user, "coverage.read")
        requirements = await traceability_repository.list_records(
            "requirements",
            {"project_id": project_id, "status": TRACE_POLICY["baselined_status"]},
            TRACE_POLICY["requirement_limit"],
        )
        requirement_versions = {item["current_version_id"] for item in requirements}
        criteria = await traceability_repository.list_records(
            "acceptance_criteria",
            {
                "project_id": project_id,
                "requirement_version_id": {"$in": list(requirement_versions)},
                "status": {"$ne": TRACE_POLICY["criterion_obsolete_status"]},
            },
            TRACE_POLICY["criterion_limit"],
        )
        links = await traceability_repository.list_records(
            "trace_links",
            {"project_id": project_id, "status": TRACE_POLICY["confirmed_status"]},
            TRACE_POLICY["link_limit"],
        )
        test_version_ids = {
            link["target_id"]
            for link in links
            if link["target_type"] == TRACE_POLICY["test_version_target_type"]
        }
        test_versions = await traceability_repository.list_records(
            "test_case_versions",
            {"_id": {"$in": list(test_version_ids)}},
            TRACE_POLICY["link_limit"],
        )
        linked_requirements = {
            link["source_id"]
            for link in links
            if link["source_type"] == TRACE_POLICY["requirement_source_type"]
        }
        linked_criteria = {
            link["source_id"]
            for link in links
            if link["source_type"] == TRACE_POLICY["criterion_source_type"]
        }
        criterion_ids = {item["_id"] for item in criteria}
        categories = {}
        for category in TRACE_POLICY["coverage_categories"]:
            category_versions = {item["_id"] for item in test_versions if item.get("type") == category}
            covered_sources = {link["source_id"] for link in links if link["target_id"] in category_versions}
            categories[category] = percent(len(requirement_versions & covered_sources), len(requirement_versions))
        uncovered = [item for item in requirements if item["current_version_id"] not in linked_requirements]
        unlinked_tests = await traceability_repository.list_records(
            "test_cases",
            {"project_id": project_id, "current_version_id": {"$nin": list(test_version_ids)}},
            TRACE_POLICY["requirement_limit"],
        )
        stale_tests = await traceability_repository.count_records(
            "test_cases",
            {"project_id": project_id, "status": TRACE_POLICY["needs_update_status"]},
        )
        active_tests = await traceability_repository.list_records(
            "test_cases",
            {"project_id": project_id, "status": TRACE_POLICY["active_status"]},
            TRACE_POLICY["test_limit"],
        )
        active_version_ids = {item.get("current_version_id") for item in active_tests if item.get("current_version_id")}
        fresh_requirement_ids = {
            link["source_id"] for link in links
            if link.get("source_type") == TRACE_POLICY["requirement_source_type"]
            and link.get("target_id") in active_version_ids
        }
        run_query = {"project_id": project_id}
        if build_id:
            run_query["build_id"] = build_id
        elif build:
            run_query["build"] = build
        if release_id:
            plans = await traceability_repository.list_records(
                "test_plans",
                {"project_id": project_id, "release_id": release_id},
                TRACE_POLICY["plan_limit"],
                projection={"_id": 1},
            )
            run_query["test_plan_id"] = {"$in": [item["_id"] for item in plans]}
        elif release:
            plans = await traceability_repository.list_records(
                "test_plans",
                {"project_id": project_id, "release": release},
                TRACE_POLICY["plan_limit"],
                projection={"_id": 1},
            )
            run_query["test_plan_id"] = {"$in": [item["_id"] for item in plans]}
        runs = await traceability_repository.list_records(
            "test_runs", run_query, TRACE_POLICY["run_limit"]
        )
        run_ids = [item["_id"] for item in runs]
        execution_scope_ids = {version_id for item in runs for version_id in item.get("test_case_version_ids", [])}
        terminal_results = await traceability_repository.list_records(
            "test_results",
            {
                "project_id": project_id,
                "test_run_id": {"$in": run_ids},
                "status": {"$in": TRACE_POLICY["terminal_result_statuses"]},
            },
            TRACE_POLICY["link_limit"],
            ("completed_at", -1),
        )
        executed_version_ids = {item["test_case_version_id"] for item in terminal_results}
        latest_execution = {}
        for item in terminal_results:
            latest_execution.setdefault(item["test_case_version_id"], item)
        UNCOVERED.set(len(uncovered))
        STALE.set(stale_tests)
        return {
            "requirement_coverage": percent(len(requirement_versions & linked_requirements), len(requirement_versions)),
            "acceptance_criterion_coverage": percent(len(criterion_ids & linked_criteria), len(criterion_ids)),
            "fresh_coverage": percent(len(requirement_versions & fresh_requirement_ids), len(requirement_versions)),
            "execution_coverage": percent(len(execution_scope_ids & executed_version_ids), len(execution_scope_ids)),
            "category_coverage": categories,
            "uncovered_requirements": uncovered,
            "unlinked_tests": unlinked_tests,
            "stale_tests": stale_tests,
            "latest_execution": latest_execution,
            "scope": {"build": build or None, "build_id": build_id or None, "release": release or None, "release_id": release_id or None, "test_case_version_ids": sorted(execution_scope_ids)},
        }

    @staticmethod
    async def requirement_coverage(requirement_id, user):
        requirement = await get_project_entity("requirements", requirement_id, user, "coverage.read")
        versions = await traceability_repository.list_records(
            "requirement_versions",
            {"requirement_id": requirement_id, "project_id": requirement["project_id"]},
            TRACE_POLICY["version_history_limit"],
            ("version", 1),
        )
        links = await traceability_repository.list_records(
            "trace_links",
            {
                "project_id": requirement["project_id"],
                "source_type": TRACE_POLICY["requirement_source_type"],
                "source_id": {"$in": [item["_id"] for item in versions]},
            },
            TRACE_POLICY["artifact_trace_limit"],
        )
        return {
            "requirement_id": requirement_id,
            "versions": versions,
            "trace_links": links,
            "covered": any(
                item.get("status") == TRACE_POLICY["confirmed_status"] for item in links
            ),
        }

    @staticmethod
    async def list_snapshots(project_id, limit, user):
        await get_project(project_id, user, "coverage.read")
        return await traceability_repository.list_records(
            "coverage_snapshots", {"project_id": project_id}, limit, ("created_at", -1)
        )

    @classmethod
    async def create_snapshot(cls, project_id, payload, user):
        await get_project(project_id, user, "coverage.snapshot.create")
        idempotency_key = str(payload.get("idempotency_key") or "").strip() or None
        if idempotency_key:
            existing = await traceability_repository.find_snapshot(project_id, idempotency_key)
            if existing:
                return existing
        metrics = await cls.coverage(
            project_id,
            str(payload.get("build") or ""),
            str(payload.get("build_id") or ""),
            str(payload.get("release") or ""),
            str(payload.get("release_id") or ""),
            user,
        )
        snapshot = {
            "_id": new_id(TRACE_POLICY["coverage_id_prefix"]),
            "project_id": project_id,
            "label": str(payload.get("label") or ""),
            "release_id": str(payload.get("release_id") or "") or None,
            "build_id": str(payload.get("build_id") or "") or None,
            "idempotency_key": idempotency_key,
            "metrics": metrics,
            "created_by": user.id,
            "created_at": now(),
        }
        try:
            await traceability_repository.insert_snapshot(snapshot)
        except Exception:
            if idempotency_key:
                existing = await traceability_repository.find_snapshot(
                    project_id, idempotency_key
                )
                if existing:
                    return existing
            raise
        await audit(user.id, "coverage_snapshot_created", "CoverageSnapshot", snapshot["_id"], project_id)
        return snapshot

    @staticmethod
    async def test_case_trace(test_case_id, user):
        test_case = await get_project_entity("test_cases", test_case_id, user, "trace.read")
        links = await traceability_repository.list_records(
            "trace_links",
            {
                "project_id": test_case["project_id"],
                "target_type": TRACE_POLICY["test_version_target_type"],
                "target_id": {"$in": [test_case.get("current_version_id")]},
            },
            TRACE_POLICY["artifact_trace_limit"],
        )
        return {"test_case": test_case, "trace_links": links}

    @staticmethod
    async def export(project_id, user):
        await get_project(project_id, user, "report.export")
        links = await traceability_repository.list_records(
            "trace_links", {"project_id": project_id}, TRACE_POLICY["link_limit"]
        )
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=["source_type", "source_id", "target_type", "target_id", "link_type", "status", "confidence", "origin"])
        writer.writeheader()
        for link in links:
            writer.writerow({key: link.get(key) for key in writer.fieldnames})
        return (
            stream.getvalue(),
            f"{TRACE_POLICY['export_filename_prefix']}-{project_id}.csv",
        )
