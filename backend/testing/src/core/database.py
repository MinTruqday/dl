from motor.motor_asyncio import AsyncIOMotorClient

from src.core.configuration import settings


class Database:
    client: AsyncIOMotorClient | None = None

    @property
    def value(self):
        if self.client is None:
            raise RuntimeError("Cơ sở dữ liệu chưa sẵn sàng")
        return self.client[settings.TESTING_DB_NAME]


database = Database()


async def ensure_unique_index(collection, keys):
    target = dict(keys)
    indexes = await collection.list_indexes().to_list(length=1000)
    for index in indexes:
        if dict(index["key"]) != target:
            continue
        if index.get("unique"):
            return index["name"]
        group_id = {field: f"${field}" for field, _ in keys}
        duplicate = await collection.aggregate(
            [
                {"$group": {"_id": group_id, "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}},
                {"$limit": 1},
            ]
        ).to_list(length=1)
        if duplicate:
            raise RuntimeError(f"Không thể tạo unique index cho {collection.name}")
        await collection.drop_index(index["name"])
        break
    return await collection.create_index(keys, unique=True)


async def ensure_partial_unique_index(collection, keys, partial_filter):
    target = dict(keys)
    replacement = None
    indexes = await collection.list_indexes().to_list(length=1000)
    for index in indexes:
        if dict(index["key"]) != target:
            continue
        if index.get("unique") and dict(index.get("partialFilterExpression") or {}) == partial_filter:
            return index["name"]
        replacement = index["name"]
        break
    group_id = {field: f"${field}" for field, _ in keys}
    duplicate = await collection.aggregate(
        [
            {"$match": partial_filter},
            {"$group": {"_id": group_id, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$limit": 1},
        ]
    ).to_list(length=1)
    if duplicate:
        raise RuntimeError(f"Không thể tạo partial unique index cho {collection.name}")
    if replacement:
        await collection.drop_index(replacement)
    return await collection.create_index(
        keys,
        unique=True,
        partialFilterExpression=partial_filter,
    )


async def connect_database():
    database.client = AsyncIOMotorClient(settings.MONGODB_URI, tz_aware=True)
    await database.client.admin.command("ping")
    await create_indexes()


async def close_database():
    if database.client is not None:
        database.client.close()
        database.client = None


async def create_indexes():
    db = database.value
    await db.requirement_change_sets.update_many(
        {"revision": {"$exists": False}}, {"$set": {"revision": 1}}
    )
    await db.import_jobs.update_many(
        {"revision": {"$exists": False}}, {"$set": {"revision": 1}}
    )
    await db.trace_links.update_many(
        {"revision": {"$exists": False}}, {"$set": {"revision": 1}}
    )
    await db.projects.create_index("key", unique=True)
    await db.projects.create_index([("created_by", 1), ("updated_at", -1)])
    await db.project_members.create_index([("project_id", 1), ("user_id", 1)], unique=True)
    await db.project_members.create_index([("user_id", 1), ("status", 1)])
    await db.requirements.create_index([("project_id", 1), ("requirement_key", 1)], unique=True)
    await ensure_unique_index(db.requirement_documents, [("project_id", 1), ("content_hash", 1)])
    await db.requirement_documents.create_index([("project_id", 1), ("created_at", -1)])
    await db.requirement_versions.create_index([("requirement_id", 1), ("version", 1)], unique=True)
    await db.acceptance_criteria.create_index([("requirement_version_id", 1), ("key", 1)], unique=True)
    await db.requirement_transformations.create_index(
        [("project_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.requirement_transformations.create_index(
        [("project_id", 1), ("source_requirement_ids", 1), ("created_at", -1)]
    )
    await db.requirement_duplicate_scans.create_index(
        [("project_id", 1), ("created_at", -1)]
    )
    await db.test_scenarios.create_index([("project_id", 1), ("scenario_key", 1)], unique=True)
    await db.data_sets.create_index([("project_id", 1), ("name", 1)], unique=True)
    await db.data_set_versions.create_index([("data_set_id", 1), ("version", 1)], unique=True)
    await db.data_set_versions.create_index([("project_id", 1), ("created_at", -1)])
    await db.test_case_templates.create_index([("project_id", 1), ("name", 1)], unique=True)
    await db.test_case_templates.create_index([("project_id", 1), ("status", 1), ("updated_at", -1)])
    await db.test_case_drafts.create_index([("project_id", 1), ("updated_at", -1)])
    await db.test_cases.create_index([("project_id", 1), ("test_case_key", 1)], unique=True)
    await db.test_case_versions.create_index([("test_case_id", 1), ("version", 1)], unique=True)
    await db.trace_links.create_index([("project_id", 1), ("source_type", 1), ("source_id", 1)])
    await db.trace_links.create_index([("project_id", 1), ("target_type", 1), ("target_id", 1)])
    await db.trace_links.create_index(
        [("project_id", 1), ("source_type", 1), ("source_id", 1), ("target_type", 1), ("target_id", 1), ("link_type", 1)],
        unique=True,
    )
    await db.ai_results.create_index([("project_id", 1), ("created_at", -1)])
    await ensure_partial_unique_index(
        db.ai_results,
        [("project_id", 1), ("idempotency_key", 1)],
        {"idempotency_key": {"$type": "string"}},
    )
    await db.coverage_snapshots.create_index([("project_id", 1), ("created_at", -1)])
    await ensure_partial_unique_index(
        db.coverage_snapshots,
        [("project_id", 1), ("idempotency_key", 1)],
        {"idempotency_key": {"$type": "string"}},
    )
    await db.requirement_change_sets.create_index([("requirement_id", 1), ("to_version_id", 1)], unique=True)
    await db.impact_analyses.create_index([("project_id", 1), ("change_set_id", 1), ("created_at", -1)])
    await ensure_partial_unique_index(
        db.impact_analyses,
        [("change_set_id", 1), ("snapshot_number", 1)],
        {
            "change_set_id": {"$type": "string"},
            "snapshot_number": {"$type": "number"},
        },
    )
    await db.impact_analyses.create_index(
        [("project_id", 1), ("source_type", 1), ("from_artifact_id", 1), ("to_artifact_id", 1)],
        unique=True,
        partialFilterExpression={"source_type": "api_artifact_diff"},
    )
    await db.maintenance_proposals.create_index([("project_id", 1), ("status", 1)])
    await db.regression_recommendations.create_index([("change_set_id", 1)], unique=True)
    await db.test_plans.create_index([("project_id", 1), ("updated_at", -1)])
    await db.test_suites.create_index([("project_id", 1), ("updated_at", -1)])
    await db.test_runs.create_index([("project_id", 1), ("status", 1), ("updated_at", -1)])
    await db.device_matrices.create_index([("project_id", 1), ("name", 1)], unique=True)
    await db.device_matrices.create_index([("project_id", 1), ("status", 1), ("updated_at", -1)])
    await db.notification_subscriptions.create_index(
        [("project_id", 1), ("user_id", 1), ("artifact_type", 1), ("artifact_id", 1)],
        unique=True,
    )
    await db.notification_subscriptions.create_index(
        [("project_id", 1), ("user_id", 1), ("updated_at", -1)]
    )
    await db.project_notification_rules.create_index("project_id", unique=True)
    await db.project_notification_preferences.create_index(
        [("project_id", 1), ("user_id", 1)], unique=True
    )
    await db.security_test_suggestions.create_index(
        [("project_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.security_test_suggestions.create_index(
        [("project_id", 1), ("created_at", -1)]
    )
    await db.performance_plan_drafts.create_index(
        [("project_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.performance_plan_drafts.create_index(
        [("project_id", 1), ("created_at", -1)]
    )
    await db.webhook_subscriptions.create_index(
        [("project_id", 1), ("name", 1)], unique=True
    )
    await db.webhook_subscriptions.create_index(
        [("project_id", 1), ("enabled", 1), ("updated_at", -1)]
    )
    await db.webhook_deliveries.create_index(
        [("project_id", 1), ("created_at", -1)]
    )
    await db.webhook_deliveries.create_index(
        [("project_id", 1), ("subscription_id", 1), ("status", 1)]
    )
    await db.webhook_replay_jobs.create_index(
        [("project_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.automation_script_drafts.create_index(
        [("project_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.automation_script_drafts.create_index(
        [("project_id", 1), ("status", 1), ("updated_at", -1)]
    )
    await db.project_connectors.create_index(
        [("project_id", 1), ("provider", 1)], unique=True
    )
    await db.connector_sync_jobs.create_index(
        [("project_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.connector_sync_jobs.create_index(
        [("project_id", 1), ("created_at", -1)]
    )
    await db.connector_sync_conflicts.create_index(
        [("project_id", 1), ("status", 1), ("created_at", -1)]
    )
    await db.automation_executions.create_index(
        [("project_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.automation_executions.create_index(
        [("project_id", 1), ("status", 1), ("created_at", -1)]
    )
    await db.cicd_bindings.create_index(
        [("project_id", 1), ("pipeline_reference", 1)], unique=True
    )
    await db.pipeline_runs.create_index(
        [("project_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.cicd_reconciliation_jobs.create_index(
        [("project_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.collaboration_sessions.create_index(
        [("project_id", 1), ("artifact_type", 1), ("artifact_id", 1), ("user_id", 1), ("client_id", 1)],
        unique=True,
    )
    await db.collaboration_sessions.create_index("expires_at", expireAfterSeconds=0)
    await db.collaboration_operations.create_index(
        [("project_id", 1), ("operation_id", 1)], unique=True
    )
    await db.draft_conflicts.create_index(
        [("project_id", 1), ("status", 1), ("created_at", -1)]
    )
    await ensure_partial_unique_index(
        db.bulk_operations,
        [("project_id", 1), ("idempotency_key", 1)],
        {"idempotency_key": {"$type": "string"}},
    )
    await db.test_run_resume_events.create_index(
        [("test_run_id", 1), ("idempotency_key", 1)], unique=True
    )
    await db.releases.create_index([("project_id", 1), ("key", 1)], unique=True)
    await db.releases.create_index([("project_id", 1), ("status", 1), ("updated_at", -1)])
    await db.builds.create_index([("project_id", 1), ("identifier", 1)], unique=True)
    await db.builds.create_index([("project_id", 1), ("release_id", 1), ("created_at", -1)])
    await db.test_environments.create_index([("project_id", 1), ("name", 1)], unique=True)
    await db.test_environments.create_index([("project_id", 1), ("status", 1), ("updated_at", -1)])
    await db.risk_rankings.create_index([("project_id", 1), ("created_at", -1)])
    await db.test_results.create_index([("test_run_id", 1), ("test_case_version_id", 1)], unique=True)
    await db.test_result_corrections.create_index([("test_result_id", 1), ("idempotency_key", 1)], unique=True)
    await db.defects.create_index([("project_id", 1), ("defect_key", 1)], unique=True)
    await db.defect_retests.create_index([("defect_id", 1), ("idempotency_key", 1)], unique=True)
    await db.test_execution_updates.create_index([("test_result_id", 1), ("idempotency_key", 1)], unique=True)
    await db.audit_events.create_index([("project_id", 1), ("created_at", -1)])
    await db.review_comments.create_index([("project_id", 1), ("artifact_type", 1), ("artifact_id", 1), ("created_at", 1)])
    await db.attachments.create_index([("project_id", 1), ("status", 1), ("created_at", -1)])
    await db.attachments.create_index([("project_id", 1), ("owner_id", 1), ("url", 1), ("status", 1)])
    await db.break_glass_grants.create_index(
        [("project_id", 1), ("user_id", 1), ("status", 1), ("expires_at", 1)]
    )
    await db.import_jobs.create_index([("project_id", 1), ("created_at", -1)])
    await ensure_partial_unique_index(
        db.import_jobs,
        [("source_document_id", 1), ("idempotency_key", 1)],
        {"idempotency_key": {"$type": "string"}},
    )
    await db.import_jobs.create_index([("source_document_id", 1)], unique=True, sparse=True)
    await db.api_imports.create_index([("project_id", 1), ("created_at", -1)])
    await ensure_partial_unique_index(
        db.api_imports,
        [("project_id", 1), ("idempotency_key", 1)],
        {"idempotency_key": {"$type": "string"}},
    )
    await db.api_operations.create_index([("project_id", 1), ("method", 1), ("path", 1)])
    await db.api_operations.create_index(
        [("import_id", 1), ("source_index", 1)], unique=True, sparse=True
    )
    await db.test_imports.create_index([("project_id", 1), ("created_at", -1)])
    await db.worker_events.create_index([("project_id", 1), ("event", 1), ("completed_at", -1)])
    await db.bulk_operations.create_index([("project_id", 1), ("created_at", -1)])
