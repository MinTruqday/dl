import hashlib
import hmac

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, get_project_entity, new_id, now
from src.core.configuration import settings
from src.repositories.cicd import cicd_repository
from src.services.domain_policy import domain_policy
from src.services.sensitive_data import redact_sensitive_data


def verify_signature(value, signature):
    policy = domain_policy("cicd")
    expected = hmac.new(settings.SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(
            status_code=403, detail={"code": policy["invalid_signature_code"]}
        )


def require_internal_token(value):
    policy = domain_policy("cicd")
    if not hmac.compare_digest(value, settings.SECRET_KEY):
        raise HTTPException(
            status_code=403, detail={"code": policy["invalid_internal_token_code"]}
        )


def public_binding(value):
    policy = domain_policy("cicd")
    result = dict(value)
    result["pipeline_reference"] = policy["configured_reference_label"]
    return result


class CiCdService:
    @staticmethod
    async def list_state(project_id, user):
        policy = domain_policy("cicd")
        await get_project(project_id, user, policy["read_permission"])
        bindings = await cicd_repository.list_bindings(project_id, policy["binding_limit"])
        runs = await cicd_repository.list_runs(project_id, policy["run_limit"])
        reconciliations = await cicd_repository.list_reconciliations(
            project_id, policy["reconciliation_limit"]
        )
        return {
            "bindings": [public_binding(item) for item in bindings],
            "runs": redact_sensitive_data(runs),
            "reconciliations": reconciliations,
        }

    @staticmethod
    async def create_binding(project_id, payload, user):
        policy = domain_policy("cicd")
        await get_project(project_id, user, policy["manage_permission"])
        connector = await cicd_repository.find_active_connector(
            payload.connector_id, project_id, policy["bound_status"]
        )
        if not connector:
            raise HTTPException(
                status_code=422, detail={"code": policy["active_connector_required_code"]}
            )
        if payload.postman_artifact_id:
            artifact = await cicd_repository.find_api_artifact(
                payload.postman_artifact_id,
                project_id,
                policy["postman_format"],
                policy["confirmed_status"],
            )
            if not artifact:
                raise HTTPException(
                    status_code=422,
                    detail={"code": policy["confirmed_postman_required_code"]},
                )
        timestamp = now()
        value = {
            "_id": new_id(policy["binding_id_prefix"]),
            "project_id": project_id,
            **payload.model_dump(),
            "enabled": True,
            "revision": policy["initial_revision"],
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await cicd_repository.insert_binding(value)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=409, detail={"code": policy["pipeline_already_bound_code"]}
            )
        await audit(
            user.id,
            policy["binding_created_event"],
            policy["binding_entity_type"],
            value["_id"],
            project_id,
            {"connector_id": payload.connector_id},
        )
        return public_binding(value)

    @staticmethod
    async def update_binding(project_id, binding_id, payload, user):
        policy = domain_policy("cicd")
        binding = await get_project_entity(
            "cicd_bindings", binding_id, user, policy["manage_permission"]
        )
        if binding["project_id"] != project_id:
            raise HTTPException(
                status_code=422, detail={"code": policy["project_mismatch_code"]}
            )
        changes = payload.model_dump(exclude_unset=True)
        changes.pop("expected_revision", None)
        updated = await cicd_repository.update_binding(
            binding_id,
            project_id,
            payload.expected_revision,
            {**changes, "updated_at": now()},
        )
        if not updated:
            raise HTTPException(
                status_code=409, detail={"code": policy["revision_conflict_code"]}
            )
        await audit(
            user.id,
            policy["binding_updated_event"],
            policy["binding_entity_type"],
            binding_id,
            project_id,
        )
        return public_binding(updated)

    @staticmethod
    async def trigger(payload, internal_token):
        policy = domain_policy("cicd")
        require_internal_token(internal_token)
        verify_signature(
            f"{payload.project_id}:{payload.binding_id}:{payload.external_run_id}:{payload.idempotency_key}",
            payload.context_signature,
        )
        existing = await cicd_repository.find_run_by_idempotency(
            payload.project_id, payload.idempotency_key
        )
        if existing:
            return existing
        binding = await cicd_repository.find_active_binding(
            payload.binding_id, payload.project_id
        )
        if not binding:
            raise HTTPException(
                status_code=422,
                detail={"code": policy["active_pipeline_binding_required_code"]},
            )
        timestamp = now()
        automation = {
            "_id": new_id(policy["execution_id_prefix"]),
            "project_id": payload.project_id,
            "name": policy["execution_name_template"].format(
                binding_name=binding["name"], external_run_id=payload.external_run_id
            ),
            "runner": policy["external_runner"],
            "postman_artifact_id": binding.get("postman_artifact_id"),
            "release_id": binding.get("release_id"),
            "test_case_version_ids": binding.get("test_case_version_ids", []),
            "status": policy["running_status"],
            "summary": {},
            "results": [],
            "logs": [],
            "artifact_refs": [],
            "idempotency_key": f"{policy['execution_idempotency_prefix']}:{payload.idempotency_key}",
            "revision": policy["initial_revision"],
            "created_by": policy["service_actor"],
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        run = {
            "_id": new_id(policy["run_id_prefix"]),
            "project_id": payload.project_id,
            "binding_id": payload.binding_id,
            "automation_execution_id": automation["_id"],
            "external_run_id": payload.external_run_id,
            "commit_reference": payload.commit_reference,
            "status": policy["running_status"],
            "attempt": policy["initial_attempt"],
            "idempotency_key": payload.idempotency_key,
            "revision": policy["initial_revision"],
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await cicd_repository.insert_execution(automation)
            await cicd_repository.insert_run(run)
        except DuplicateKeyError:
            await cicd_repository.delete_execution(automation["_id"], payload.project_id)
            existing = await cicd_repository.find_run_by_idempotency(
                payload.project_id, payload.idempotency_key
            )
            if existing:
                return existing
            raise
        except Exception:
            await cicd_repository.delete_execution(automation["_id"], payload.project_id)
            raise
        await audit(
            policy["service_actor"],
            policy["run_triggered_event"],
            policy["run_entity_type"],
            run["_id"],
            payload.project_id,
            {"external_run_id": payload.external_run_id},
        )
        return run

    @staticmethod
    async def ingest_result(payload, internal_token):
        policy = domain_policy("cicd")
        require_internal_token(internal_token)
        verify_signature(
            f"{payload.project_id}:{payload.pipeline_run_id}:{payload.status}",
            payload.context_signature,
        )
        run = await cicd_repository.find_run(
            payload.pipeline_run_id, payload.project_id
        )
        if not run:
            raise HTTPException(
                status_code=404, detail={"code": policy["pipeline_run_not_found_code"]}
            )
        if run.get("status") in policy["terminal_statuses"]:
            return run
        timestamp = now()
        run_changes = {
            "status": payload.status,
            "summary": redact_sensitive_data(payload.summary),
            "logs": redact_sensitive_data(payload.logs),
            "completed_at": timestamp,
            "updated_at": timestamp,
        }
        updated = await cicd_repository.complete_run(
            payload.pipeline_run_id,
            payload.project_id,
            policy["running_status"],
            run_changes,
        )
        if not updated:
            updated = await cicd_repository.find_run(
                payload.pipeline_run_id, payload.project_id
            )
        execution_changes = {
            "status": payload.status,
            "summary": redact_sensitive_data(payload.summary),
            "results": redact_sensitive_data(payload.results),
            "logs": redact_sensitive_data(payload.logs),
            "completed_at": timestamp,
            "updated_at": timestamp,
        }
        await cicd_repository.complete_execution(
            run["automation_execution_id"],
            payload.project_id,
            policy["running_status"],
            execution_changes,
        )
        await audit(
            policy["service_actor"],
            policy["result_ingested_event"],
            policy["run_entity_type"],
            run["_id"],
            payload.project_id,
            {"status": payload.status},
        )
        return updated

    @staticmethod
    async def retry(project_id, run_id, payload, user):
        policy = domain_policy("cicd")
        run = await get_project_entity(
            "pipeline_runs", run_id, user, policy["retry_permission"]
        )
        if run["project_id"] != project_id:
            raise HTTPException(
                status_code=422, detail={"code": policy["project_mismatch_code"]}
            )
        existing = await cicd_repository.find_reconciliation(
            project_id, payload.idempotency_key
        )
        if existing:
            return existing
        if (
            run.get("status") != policy["failed_status"]
            or run.get("revision") != payload.expected_revision
        ):
            raise HTTPException(
                status_code=409, detail={"code": policy["pipeline_not_retryable_code"]}
            )
        timestamp = now()
        value = {
            "_id": new_id(policy["reconciliation_id_prefix"]),
            "project_id": project_id,
            "pipeline_run_id": run_id,
            "binding_id": run["binding_id"],
            "status": policy["queued_status"],
            "reason": payload.reason,
            "idempotency_key": payload.idempotency_key,
            "requested_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await cicd_repository.insert_reconciliation(value)
        except DuplicateKeyError:
            existing = await cicd_repository.find_reconciliation(
                project_id, payload.idempotency_key
            )
            if existing:
                return existing
            raise
        await audit(
            user.id,
            policy["reconciliation_queued_event"],
            policy["run_entity_type"],
            run_id,
            project_id,
            {"operation_id": value["_id"], "reason": payload.reason},
        )
        return value
