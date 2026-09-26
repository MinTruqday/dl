import hashlib
import hmac

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.clients.worker import WorkerClientError, worker_client
from src.core.common import audit, get_project, get_project_entity, new_id, now
from src.core.configuration import settings
from src.repositories.execution_asset import execution_asset_repository
from src.services.sensitive_data import redact_sensitive_data
from src.services.domain_policy import domain_policy


EXECUTION_ASSET_POLICY = domain_policy("execution_assets")


def public_execution(value, evidence=False):
    excluded = {"runner_payload", "context_signature"}
    if not evidence:
        excluded |= {"results", "logs", "artifact_refs"}
    return redact_sensitive_data({key: item for key, item in value.items() if key not in excluded})


class AutomationExecutionService:
    @staticmethod
    async def list(project_id, user):
        await get_project(project_id, user, EXECUTION_ASSET_POLICY["read_permission"])
        items = await execution_asset_repository.list_executions(project_id)
        return [public_execution(item) for item in items]

    @staticmethod
    async def get(execution_id, user, evidence=False):
        value = await get_project_entity(
            EXECUTION_ASSET_POLICY["execution_collection"],
            execution_id,
            user,
            EXECUTION_ASSET_POLICY["read_permission"],
        )
        return public_execution(value, evidence=evidence)

    @staticmethod
    async def create(project_id, payload, user):
        await get_project(project_id, user, EXECUTION_ASSET_POLICY["create_permission"])
        existing = await execution_asset_repository.find_execution_by_idempotency_key(
            project_id, payload.idempotency_key
        )
        if existing:
            return public_execution(existing)
        artifact = None
        script = None
        if payload.runner == EXECUTION_ASSET_POLICY["postman_runner"]:
            artifact = await execution_asset_repository.find_confirmed_postman_import(
                project_id,
                payload.postman_artifact_id,
                EXECUTION_ASSET_POLICY["postman_format"],
                EXECUTION_ASSET_POLICY["confirmed_status"],
            )
            if not artifact or not artifact.get("raw_content"):
                raise HTTPException(
                    status_code=422,
                    detail={"code": EXECUTION_ASSET_POLICY["postman_collection_required_code"]},
                )
        else:
            script = await execution_asset_repository.find_approved_playwright_script(
                project_id,
                payload.automation_script_id,
                EXECUTION_ASSET_POLICY["playwright_framework"],
                EXECUTION_ASSET_POLICY["approved_status"],
            )
            if not script or not str(script.get("source") or "").strip():
                raise HTTPException(
                    status_code=422,
                    detail={"code": EXECUTION_ASSET_POLICY["playwright_script_required_code"]},
                )
        environment = None
        if payload.environment_id:
            environment = await execution_asset_repository.find_active_environment(
                project_id,
                payload.environment_id,
                EXECUTION_ASSET_POLICY["archived_status"],
            )
            if not environment:
                raise HTTPException(
                    status_code=422,
                    detail={"code": EXECUTION_ASSET_POLICY["invalid_environment_code"]},
                )
        timestamp = now()
        value = {
            "_id": new_id(EXECUTION_ASSET_POLICY["execution_id_prefix"]),
            "project_id": project_id,
            "name": payload.name,
            "runner": payload.runner,
            "postman_artifact_id": artifact["_id"] if artifact else None,
            "automation_script_id": script["_id"] if script else None,
            "environment_id": payload.environment_id,
            "environment_snapshot": {
                "name": environment.get("name"),
                "base_url_configured": bool(environment.get("base_url")),
                "secret_reference_names": sorted((environment.get("secret_refs") or {}).keys()),
            }
            if environment
            else None,
            "runner_payload": {
                **({"collection": artifact["raw_content"]} if artifact else {}),
                **(
                    {"source": script["source"], "filename": script["filename"], "language": script["language"]}
                    if script
                    else {}
                ),
                "environment": {
                    key: environment.get("base_url")
                    for key in EXECUTION_ASSET_POLICY["base_url_environment_keys"]
                }
                if environment and environment.get("base_url")
                else {},
            },
            "status": EXECUTION_ASSET_POLICY["created_status"],
            "summary": {},
            "results": [],
            "logs": [],
            "artifact_refs": [],
            "idempotency_key": payload.idempotency_key,
            "revision": EXECUTION_ASSET_POLICY["initial_revision"],
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await execution_asset_repository.insert_execution(value)
        except DuplicateKeyError:
            existing = await execution_asset_repository.find_execution_by_idempotency_key(
                project_id, payload.idempotency_key
            )
            if existing:
                return public_execution(existing)
            raise
        await audit(
            user.id,
            EXECUTION_ASSET_POLICY["created_event"],
            EXECUTION_ASSET_POLICY["execution_entity"],
            value["_id"],
            project_id,
            {
                "postman_artifact_id": artifact["_id"] if artifact else None,
                "automation_script_id": script["_id"] if script else None,
                "runner": payload.runner,
            },
        )
        return public_execution(value)

    @staticmethod
    async def start(execution_id, payload, user):
        execution = await get_project_entity(
            EXECUTION_ASSET_POLICY["execution_collection"],
            execution_id,
            user,
            EXECUTION_ASSET_POLICY["execute_permission"],
        )
        if execution.get("status") == EXECUTION_ASSET_POLICY["queued_status"] and execution.get(
            "start_idempotency_key"
        ) == payload.idempotency_key:
            return public_execution(execution), execution.get("operation_id")
        if execution.get("status") != EXECUTION_ASSET_POLICY["created_status"] or execution.get(
            "revision"
        ) != payload.expected_revision:
            raise HTTPException(
                status_code=409,
                detail={"code": EXECUTION_ASSET_POLICY["state_conflict_code"]},
            )
        runner = execution.get("runner")
        if runner not in set(EXECUTION_ASSET_POLICY["supported_runners"]):
            raise HTTPException(
                status_code=422,
                detail={"code": EXECUTION_ASSET_POLICY["unsupported_runner_code"]},
            )
        request = {
            "event": f"automation.{runner}.requested",
            "project_id": execution["project_id"],
            "artifact_version_id": execution_id,
            "model_version": runner,
            "requester_id": user.id,
            "requester_email": user.email,
            "payload": {"execution_id": execution_id, **execution["runner_payload"]},
        }
        idempotency_value = ":".join(
            [request["project_id"], request["artifact_version_id"], request["event"], request["model_version"]]
        )
        operation_id = f"qa-{hashlib.sha256(idempotency_value.encode()).hexdigest()[:40]}"
        timestamp = now()
        updated = await execution_asset_repository.transition_execution(
            execution_id,
            payload.expected_revision,
            EXECUTION_ASSET_POLICY["created_status"],
            {
                "status": EXECUTION_ASSET_POLICY["queued_status"],
                "operation_id": operation_id,
                "start_idempotency_key": payload.idempotency_key,
                "queued_at": timestamp,
                "updated_at": timestamp,
            },
        )
        if not updated:
            raise HTTPException(
                status_code=409,
                detail={"code": EXECUTION_ASSET_POLICY["state_conflict_code"]},
            )
        try:
            job = await worker_client.enqueue(request)
            if job.get("job_id") != operation_id:
                raise WorkerClientError()
        except WorkerClientError as error:
            await execution_asset_repository.rollback_queued_execution(
                execution_id,
                payload.expected_revision,
                operation_id,
                EXECUTION_ASSET_POLICY["queued_status"],
                EXECUTION_ASSET_POLICY["created_status"],
                now(),
            )
            raise HTTPException(
                status_code=503,
                detail={"code": EXECUTION_ASSET_POLICY["worker_unavailable_code"]},
            ) from error
        await audit(
            user.id,
            EXECUTION_ASSET_POLICY["queued_event"],
            EXECUTION_ASSET_POLICY["execution_entity"],
            execution_id,
            execution["project_id"],
            {"operation_id": operation_id},
        )
        return public_execution(updated), operation_id

    @staticmethod
    async def cancel(execution_id, payload, user):
        execution = await get_project_entity(
            EXECUTION_ASSET_POLICY["execution_collection"],
            execution_id,
            user,
            EXECUTION_ASSET_POLICY["execute_permission"],
        )
        if execution.get("status") == EXECUTION_ASSET_POLICY["cancelled_status"]:
            return public_execution(execution)
        if execution.get("status") != EXECUTION_ASSET_POLICY["queued_status"] or execution.get(
            "revision"
        ) != payload.expected_revision:
            raise HTTPException(
                status_code=409,
                detail={"code": EXECUTION_ASSET_POLICY["not_cancellable_code"]},
            )
        try:
            await worker_client.cancel(execution["operation_id"])
        except WorkerClientError as error:
            raise HTTPException(
                status_code=503,
                detail={"code": EXECUTION_ASSET_POLICY["worker_unavailable_code"]},
            ) from error
        timestamp = now()
        updated = await execution_asset_repository.transition_execution(
            execution_id,
            payload.expected_revision,
            EXECUTION_ASSET_POLICY["queued_status"],
            {
                "status": EXECUTION_ASSET_POLICY["cancelled_status"],
                "cancelled_by": user.id,
                "cancelled_at": timestamp,
                "updated_at": timestamp,
            },
        )
        await audit(
            user.id,
            EXECUTION_ASSET_POLICY["cancelled_event"],
            EXECUTION_ASSET_POLICY["execution_entity"],
            execution_id,
            execution["project_id"],
        )
        return public_execution(updated)

    @staticmethod
    async def ingest_result(payload, internal_token):
        if not hmac.compare_digest(internal_token, settings.SECRET_KEY):
            raise HTTPException(
                status_code=403,
                detail={"code": EXECUTION_ASSET_POLICY["invalid_internal_token_code"]},
            )
        signature_value = f"{payload.execution_id}:{payload.operation_id}:{payload.status}"
        expected = hmac.new(settings.SECRET_KEY.encode(), signature_value.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, payload.context_signature):
            raise HTTPException(
                status_code=403,
                detail={"code": EXECUTION_ASSET_POLICY["invalid_context_signature_code"]},
            )
        execution = await execution_asset_repository.find_execution_operation(
            payload.execution_id, payload.operation_id
        )
        if not execution:
            raise HTTPException(
                status_code=404,
                detail={"code": EXECUTION_ASSET_POLICY["execution_not_found_code"]},
            )
        if execution.get("status") in set(
            EXECUTION_ASSET_POLICY["terminal_execution_statuses"]
        ):
            return public_execution(execution, evidence=True)
        timestamp = now()
        updated = await execution_asset_repository.ingest_execution_result(
            payload.execution_id,
            payload.operation_id,
            EXECUTION_ASSET_POLICY["result_ingest_source_statuses"],
            {
                "status": payload.status,
                "summary": redact_sensitive_data(payload.summary),
                "results": redact_sensitive_data(payload.results),
                "logs": redact_sensitive_data(payload.logs),
                "artifact_refs": payload.artifact_refs,
                "completed_at": timestamp,
                "updated_at": timestamp,
            },
        )
        if not updated:
            raise HTTPException(
                status_code=409,
                detail={"code": EXECUTION_ASSET_POLICY["state_conflict_code"]},
            )
        await audit(
            EXECUTION_ASSET_POLICY["worker_actor"],
            EXECUTION_ASSET_POLICY["result_ingested_event"],
            EXECUTION_ASSET_POLICY["execution_entity"],
            payload.execution_id,
            updated["project_id"],
            {"operation_id": payload.operation_id, "status": payload.status},
        )
        return public_execution(updated, evidence=True)
