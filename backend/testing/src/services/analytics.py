import re

from src.core.common import get_project, load_user_identities, now
from src.domain.contracts import SearchInput
from src.repositories.analytics import analytics_repository
from src.services.design_assistance import ai_contract_metadata, request_design_assistance
from src.services.domain_policy import domain_policy
from src.clients.project_knowledge import search_project_with_status

ANALYTICS_POLICY = domain_policy("analytics")


def percentage(value, total):
    return (
        round(
            value * ANALYTICS_POLICY["percentage_multiplier"] / total,
            ANALYTICS_POLICY["percentage_precision"],
        )
        if total
        else 0
    )


def lexical_score(query, text):
    pattern = domain_policy("text_processing")["token_pattern"]
    terms = set(re.findall(pattern, query.lower()))
    words = set(re.findall(pattern, text.lower()))
    return round(
        len(terms & words) / max(1, len(terms)),
        ANALYTICS_POLICY["score_precision"],
    )


class AnalyticsService:
    @staticmethod
    async def search(project_id, query_text, limit, user):
        await get_project(project_id, user, "project.read")
        pattern = re.escape(query_text)
        sources = ANALYTICS_POLICY["search_sources"]
        items = []
        per_source = max(1, limit // len(sources))
        for artifact_type, collection, fields in sources:
            query = {"project_id": project_id, "$or": [{field: {"$regex": pattern, "$options": "i"}} for field in fields]}
            rows = await analytics_repository.list_records(
                collection, query, per_source, ("updated_at", -1)
            )
            items.extend(
                {
                    "artifact_type": artifact_type,
                    "artifact_id": row["_id"],
                    "title": row.get("title") or row.get("name") or row.get("defect_key") or row.get("requirement_key") or row.get("test_case_key"),
                    "status": row.get("status"),
                    "project_id": project_id,
                }
                for row in rows
            )
        return {"items": items[:limit], "query": query_text, "project_id": project_id}

    @classmethod
    async def dashboard(cls, project_id, user):
        await get_project(project_id, user, "analytics.read")
        requirements = await analytics_repository.count_records("requirements", {"project_id": project_id, "status": ANALYTICS_POLICY["baselined_status"]})
        active_tests = await analytics_repository.count_records("test_cases", {"project_id": project_id, "status": ANALYTICS_POLICY["active_status"]})
        stale_tests = await analytics_repository.count_records("test_cases", {"project_id": project_id, "status": ANALYTICS_POLICY["needs_update_status"]})
        pending_proposals = await analytics_repository.count_records("maintenance_proposals", {"project_id": project_id, "status": ANALYTICS_POLICY["pending_status"]})
        current_runs = await analytics_repository.count_records("test_runs", {"project_id": project_id, "status": {"$in": ANALYTICS_POLICY["current_run_statuses"]}})
        open_defects = await analytics_repository.count_records("defects", {"project_id": project_id, "status": {"$nin": ANALYTICS_POLICY["open_defect_excluded_statuses"]}})
        defect_severity_rows = await analytics_repository.group_counts(
            "defects",
            {"project_id": project_id, "status": {"$nin": ANALYTICS_POLICY["open_defect_excluded_statuses"]}},
            "severity",
            ANALYTICS_POLICY["group_limit"],
        )
        open_defects_by_severity = {
            severity: next((item["count"] for item in defect_severity_rows if item["_id"] == severity), 0)
            for severity in ANALYTICS_POLICY["defect_severities"]
        }
        latest_run = await analytics_repository.find_latest("test_runs", {"project_id": project_id})
        latest_run_summary = None
        if latest_run:
            result_rows = await analytics_repository.group_counts(
                "test_results",
                {"project_id": project_id, "test_run_id": latest_run["_id"]},
                "status",
                ANALYTICS_POLICY["group_limit"],
            )
            latest_run_summary = {
                "_id": latest_run["_id"],
                "name": latest_run["name"],
                "status": latest_run["status"],
                "environment": latest_run.get("environment"),
                "build": latest_run.get("build"),
                "result_counts": {item["_id"]: item["count"] for item in result_rows},
                "updated_at": latest_run.get("updated_at"),
            }
        changes_waiting_impact = await analytics_repository.count_records(
            "requirement_change_sets",
            {"project_id": project_id, "status": {"$in": ANALYTICS_POLICY["impact_waiting_change_statuses"]}},
        )
        changes_waiting_impact += await analytics_repository.count_records(
            "impact_analyses", {"project_id": project_id, "status": ANALYTICS_POLICY["impact_review_status"]}
        )
        coverage = await cls.coverage_snapshot(project_id)
        recent_changes = await analytics_repository.list_records(
            "requirement_change_sets",
            {"project_id": project_id},
            ANALYTICS_POLICY["recent_change_limit"],
            ("created_at", -1),
        )
        requirement_ids = [item.get("requirement_id") for item in recent_changes if item.get("requirement_id")]
        recent_requirements = await analytics_repository.list_records(
            "requirements",
            {"project_id": project_id, "_id": {"$in": requirement_ids}},
            len(requirement_ids),
            projection={"_id": 1, "requirement_key": 1, "title": 1},
        )
        labels = {item["_id"]: item.get("requirement_key") or item.get("title") for item in recent_requirements}
        for item in recent_changes:
            item["requirement_label"] = labels.get(item.get("requirement_id")) or item.get("requirement_id")
        return {
            "requirements": requirements,
            "active_tests": active_tests,
            "tests_needing_update": stale_tests,
            "pending_proposals": pending_proposals,
            "current_runs": current_runs,
            "open_defects": open_defects,
            "open_defects_by_severity": open_defects_by_severity,
            "latest_run": latest_run_summary,
            "changes_waiting_impact": changes_waiting_impact,
            **coverage,
            "recent_changes": recent_changes,
        }

    @staticmethod
    async def search_knowledge(project_id, payload, user):
        project = await get_project(project_id, user, "knowledge.read")
        dense_result = await search_project_with_status(project_id, payload.query, payload.artifact_types, payload.limit)
        dense = dense_result["items"]
        retrieval_policy = domain_policy("knowledge_retrieval")
        pattern = re.escape(payload.query)
        requested = set(payload.artifact_types)
        results = []
        sources = ANALYTICS_POLICY["knowledge_sources"]
        for artifact_type, collection, text_field in sources:
            if requested and artifact_type not in requested:
                continue
            source_query = {
                "project_id": project_id,
                "$or": [{text_field: {"$regex": pattern, "$options": "i"}}, {"title": {"$regex": pattern, "$options": "i"}}],
            }
            if collection == "requirement_documents":
                source_query["status"] = {"$ne": ANALYTICS_POLICY["archived_status"]}
            documents = await analytics_repository.list_records(
                collection, source_query, payload.limit
            )
            for item in documents:
                authority = item.get("authority") or (
                    ANALYTICS_POLICY["approved_authority"]
                    if item.get("status") == ANALYTICS_POLICY["baselined_status"]
                    else ANALYTICS_POLICY["draft_authority"]
                )
                results.append({
                    "artifact_type": artifact_type,
                    "artifact_id": item.get("requirement_id") or item.get("test_case_id") or item["_id"],
                    "artifact_version_id": item["_id"],
                    "title": item.get("title") or item.get("name") or item.get("filename"),
                    "text": str(item.get(text_field, ""))[:retrieval_policy["snippet_character_limit"]],
                    "status": item.get("status"),
                    "authority": authority,
                    "source_type": item.get("source_type"),
                    "owner_id": item.get("owner_id"),
                    "module": item.get("module"),
                    "component": item.get("component"),
                    "product_area": item.get("product_area"),
                    "release_id": item.get("release_id"),
                    "external_source_id": item.get("external_source_id"),
                    "approval_status": item.get("approval_status"),
                    "approved_by": item.get("approved_by"),
                    "approved_at": item.get("approved_at"),
                    "source_version": item.get("source_version"),
                    "effective_from": item.get("effective_from"),
                    "tags": item.get("tags", []),
                    "project_id": project_id,
                    "score": lexical_score(payload.query, str(item.get(text_field, "")) + " " + str(item.get("title", "")) + " " + str(item.get("filename", ""))),
                })
        dense_ids_by_type = {}
        for item in dense:
            reference = item.get("artifact_version_id") or item.get("artifact_id")
            if reference:
                dense_ids_by_type.setdefault(item.get("artifact_type"), set()).add(reference)
        valid_dense_ids = set()
        for artifact_type, collection, _ in sources:
            if requested and artifact_type not in requested:
                continue
            references = dense_ids_by_type.get(artifact_type, set())
            if not references:
                continue
            documents = await analytics_repository.list_records(
                collection,
                {"project_id": project_id, "_id": {"$in": list(references)}},
                len(references),
                projection={"_id": 1},
            )
            valid_dense_ids.update(item["_id"] for item in documents)
        dense = [item for item in dense if (item.get("artifact_version_id") or item.get("artifact_id")) in valid_dense_ids]
        by_version = {item.get("artifact_version_id"): item for item in results}
        for item in dense:
            version_id = item.get("artifact_version_id")
            if version_id in by_version:
                by_version[version_id]["score"] = round(
                    retrieval_policy["lexical_weight"] * by_version[version_id]["score"]
                    + retrieval_policy["semantic_weight"] * item["score"],
                    ANALYTICS_POLICY["score_precision"],
                )
                by_version[version_id]["retrieval_source"] = "hybrid_fusion"
            else:
                by_version[version_id] = item
        results = list(by_version.values())
        authority_order = (project.get("settings") or {}).get(
            "knowledge_authority_order",
            ANALYTICS_POLICY["default_authority_order"],
        )
        authority_rank = {value: index for index, value in enumerate(authority_order)}
        results.sort(key=lambda item: (authority_rank.get(item.get("authority"), len(authority_rank)), -item.get("score", 0)))
        data = {
            "items": results[:payload.limit],
            "filters": {"project_id": project_id, "artifact_types": list(requested)},
            "retrieval_version": ANALYTICS_POLICY["retrieval_version"],
            "degraded_mode": dense_result["degraded_mode"],
            "fallback": dense_result["degraded_mode"] != ANALYTICS_POLICY["normal_mode"],
            "error_code": dense_result["error_code"],
        }
        metadata = {
            "degraded_mode": dense_result["degraded_mode"]
            if dense_result["degraded_mode"] != ANALYTICS_POLICY["normal_mode"]
            else None
        }
        return data, metadata

    @classmethod
    async def ask_project(cls, project_id, payload, user, trace_id):
        await get_project(project_id, user, "ai.ask_project")
        await get_project(project_id, user, "knowledge.read")
        search_result, _ = await cls.search_knowledge(
            project_id,
            SearchInput(query=payload.question, artifact_types=payload.artifact_types, limit=payload.evidence_limit),
            user,
        )
        evidence = search_result["items"]
        if not evidence:
            missing = ai_contract_metadata({
                "capability": "project_question",
                "status": ANALYTICS_POLICY["degraded_status"],
                "degraded_mode": ANALYTICS_POLICY["degraded_knowledge_mode"],
                "provider": "none",
                "model": {"provider": "none", "model": "none", "retrieval_version": search_result["retrieval_version"]},
                "warnings": [ANALYTICS_POLICY["evidence_not_found_code"]],
                "reason_codes": [ANALYTICS_POLICY["evidence_not_found_code"]],
            })
            return {"answer": "Không có đủ bằng chứng trong dự án để trả lời câu hỏi này", "evidence": [], **missing}, {"status": missing["status"], "degraded_mode": missing["degraded_mode"]}
        result = await request_design_assistance("project_question", project_id, payload.question, evidence)
        contract = ai_contract_metadata(result)
        await analytics_repository.insert_ai_audit({
            "_id": f"{ANALYTICS_POLICY['question_id_prefix']}{trace_id}",
            "project_id": project_id,
            "requested_by": user.id,
            **contract,
            "created_at": now(),
        })
        return {"answer": result.get("answer") or "Không có câu trả lời có căn cứ", "evidence": evidence, **contract}, {"status": contract["status"], "degraded_mode": contract["degraded_mode"]}

    @staticmethod
    async def project_audit(project_id, limit, user):
        await get_project(project_id, user, "project.audit.read")
        events = await analytics_repository.list_records(
            "audit_events", {"project_id": project_id}, limit, ("created_at", -1)
        )
        identities = await load_user_identities(item.get("actor_id") for item in events)
        return [{**event, "actor": identities.get(event.get("actor_id")), "actor_label": (identities.get(event.get("actor_id")) or {}).get("label") or event.get("actor_id")} for event in events]

    @staticmethod
    async def maintenance(project_id, user):
        await get_project(project_id, user, "analytics.read")
        return {
            "impact_analysis_count": await analytics_repository.count_records(
                "impact_analyses", {"project_id": project_id}
            ),
            "tests_stale": await analytics_repository.count_records(
                "test_cases",
                {"project_id": project_id, "status": ANALYTICS_POLICY["needs_update_status"]},
            ),
        }

    @staticmethod
    async def ai(project_id, user):
        await get_project(project_id, user, "analytics.ai.read")
        proposal_status = await analytics_repository.group_counts(
            "maintenance_proposals",
            {"project_id": project_id},
            "status",
            ANALYTICS_POLICY["status_group_limit"],
        )
        accepted = sum(
            item["count"]
            for item in proposal_status
            if item["_id"] in set(ANALYTICS_POLICY["accepted_proposal_statuses"])
        )
        reviewed = sum(
            item["count"]
            for item in proposal_status
            if item["_id"] != ANALYTICS_POLICY["pending_status"]
        )
        impact_rows = await analytics_repository.list_records(
            "impact_analyses",
            {"project_id": project_id},
            ANALYTICS_POLICY["impact_limit"],
            projection={"ai_result": 1, "review_overrides": 1, "model_version": 1},
        )
        measured = [item for item in impact_rows if isinstance(item.get("ai_result"), dict)]
        degraded = sum(
            1
            for item in measured
            if item["ai_result"].get("status") != ANALYTICS_POLICY["successful_ai_status"]
            or item["ai_result"].get("degraded_mode")
        )
        latencies = [item["ai_result"].get("latency_ms") for item in measured if isinstance(item["ai_result"].get("latency_ms"), (int, float))]
        model_versions = {}
        for item in impact_rows:
            ai_result = item.get("ai_result") or {}
            model = ai_result.get("model") if isinstance(ai_result.get("model"), dict) else {}
            model_version = (
                item.get("model_version")
                or model.get("version")
                or ANALYTICS_POLICY["unknown_model_version"]
            )
            model_versions[model_version] = model_versions.get(model_version, 0) + 1
        return {
            "proposal_status": proposal_status,
            "proposal_acceptance_rate": round(
                accepted / reviewed, ANALYTICS_POLICY["score_precision"]
            )
            if reviewed
            else None,
            "override_count": sum(len(item.get("review_overrides") or []) for item in impact_rows),
            "degraded_count": degraded,
            "degraded_rate": round(
                degraded / len(measured), ANALYTICS_POLICY["score_precision"]
            )
            if measured
            else 0,
            "average_latency_ms": round(
                sum(latencies) / len(latencies), ANALYTICS_POLICY["latency_precision"]
            )
            if latencies
            else 0,
            "model_versions": model_versions,
        }

    @staticmethod
    async def execution_report(project_id, release, release_id, environment, environment_id, build, build_id, user):
        await get_project(project_id, user, "report.read")
        run_query = {"project_id": project_id}
        for key, value in (("environment", environment), ("environment_id", environment_id), ("build", build), ("build_id", build_id), ("release_id", release_id)):
            if value:
                run_query[key] = value
        if not release_id and release:
            plans = await analytics_repository.list_records(
                "test_plans",
                {"project_id": project_id, "release": release},
                ANALYTICS_POLICY["plan_limit"],
                projection={"_id": 1},
            )
            run_query["test_plan_id"] = {"$in": [item["_id"] for item in plans]}
        runs = await analytics_repository.list_records(
            "test_runs",
            run_query,
            ANALYTICS_POLICY["run_limit"],
            projection={"_id": 1, "status": 1},
        )
        run_ids = [item["_id"] for item in runs]
        result_rows = await analytics_repository.group_counts(
            "test_results",
            {"project_id": project_id, "test_run_id": {"$in": run_ids}},
            "status",
            ANALYTICS_POLICY["group_limit"],
        )
        run_status_rows = {}
        for item in runs:
            status = item.get("status", ANALYTICS_POLICY["unknown_status"])
            run_status_rows[status] = run_status_rows.get(status, 0) + 1
        result_counts = {item["_id"]: item["count"] for item in result_rows}
        terminal_count = sum(
            result_counts.get(status, 0)
            for status in ANALYTICS_POLICY["terminal_result_statuses"]
        )
        return {
            "run_count": len(runs),
            "run_status_counts": run_status_rows,
            "result_counts": result_counts,
            "terminal_result_count": terminal_count,
            "pass_rate": round(
                result_counts.get(ANALYTICS_POLICY["pass_status"], 0) / terminal_count,
                ANALYTICS_POLICY["score_precision"],
            )
            if terminal_count
            else None,
            "scope": {"release": release or None, "release_id": release_id or None, "environment": environment or None, "environment_id": environment_id or None, "build": build or None, "build_id": build_id or None},
        }

    @staticmethod
    async def defect_report(project_id, release, release_id, environment, environment_id, build, build_id, user):
        await get_project(project_id, user, "report.read")
        query = {"project_id": project_id}
        for key, value in (("release", release), ("release_id", release_id), ("environment", environment), ("environment_id", environment_id), ("build", build), ("build_id", build_id)):
            if value:
                query[key] = value
        defects = await analytics_repository.list_records(
            "defects",
            query,
            ANALYTICS_POLICY["defect_limit"],
            projection={"status": 1, "severity": 1, "created_at": 1},
        )
        status_counts = {}
        severity_counts = {}
        open_ages = []
        timestamp = now()
        terminal_statuses = set(ANALYTICS_POLICY["open_defect_excluded_statuses"])
        for item in defects:
            status_value = item.get("status", ANALYTICS_POLICY["unknown_status"])
            severity_value = item.get(
                "severity", ANALYTICS_POLICY["unknown_model_version"]
            )
            status_counts[status_value] = status_counts.get(status_value, 0) + 1
            severity_counts[severity_value] = severity_counts.get(severity_value, 0) + 1
            if status_value not in terminal_statuses and item.get("created_at"):
                open_ages.append(
                    max(
                        0,
                        (timestamp - item["created_at"]).total_seconds()
                        / ANALYTICS_POLICY["seconds_per_day"],
                    )
                )
        reopened_count = await analytics_repository.count_records(
            "defect_retests",
            {
                "project_id": project_id,
                "outcome": ANALYTICS_POLICY["failed_retest_outcome"],
                "application_status": ANALYTICS_POLICY["applied_status"],
            },
        )
        return {
            "defect_count": len(defects),
            "open_count": sum(count for status_value, count in status_counts.items() if status_value not in terminal_statuses),
            "status_counts": status_counts,
            "severity_counts": severity_counts,
            "reopened_count": reopened_count,
            "average_open_age_days": round(
                sum(open_ages) / len(open_ages),
                ANALYTICS_POLICY["percentage_precision"],
            )
            if open_ages
            else 0,
            "scope": {"release": release or None, "release_id": release_id or None, "environment": environment or None, "environment_id": environment_id or None, "build": build or None, "build_id": build_id or None},
        }

    @staticmethod
    async def activity(project_id, limit, user):
        await get_project(project_id, user, "analytics.read")
        excluded_actions = set(ANALYTICS_POLICY["excluded_activity_actions"])
        return await analytics_repository.list_records(
            "audit_events",
            {"project_id": project_id, "action": {"$nin": sorted(excluded_actions)}},
            limit,
            ("created_at", -1),
            {"action": 1, "entity_type": 1, "entity_id": 1, "created_at": 1},
        )

    @staticmethod
    async def coverage_snapshot(project_id):
        requirements = await analytics_repository.list_records(
            "requirements",
            {"project_id": project_id, "status": ANALYTICS_POLICY["baselined_status"]},
            ANALYTICS_POLICY["requirement_limit"],
        )
        requirement_versions = {item["current_version_id"] for item in requirements}
        criteria = await analytics_repository.list_records(
            "acceptance_criteria",
            {
                "project_id": project_id,
                "requirement_version_id": {"$in": list(requirement_versions)},
                "status": {"$ne": ANALYTICS_POLICY["criterion_obsolete_status"]},
            },
            ANALYTICS_POLICY["criterion_limit"],
        )
        links = await analytics_repository.list_records(
            "trace_links",
            {"project_id": project_id, "status": ANALYTICS_POLICY["confirmed_status"]},
            ANALYTICS_POLICY["link_limit"],
        )
        covered_requirements = {
            item["source_id"]
            for item in links
            if item["source_type"] == ANALYTICS_POLICY["requirement_source_type"]
        }
        covered_criteria = {
            item["source_id"]
            for item in links
            if item["source_type"] == ANALYTICS_POLICY["criterion_source_type"]
        }
        return {
            "requirement_coverage": percentage(len(requirement_versions & covered_requirements), len(requirement_versions)),
            "acceptance_criterion_coverage": percentage(len({item["_id"] for item in criteria} & covered_criteria), len(criteria)),
            "unlinked_tests": await analytics_repository.count_records(
                "test_cases",
                {"project_id": project_id, "current_version_id": {"$nin": [item["target_id"] for item in links]}},
            ),
        }
