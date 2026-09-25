import json
import re

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, get_project_entity, new_id, now, optimistic_patch
from src.repositories.execution_asset import execution_asset_repository
from src.services.design_assistance import ai_contract_metadata, request_design_assistance
from src.services.domain_policy import domain_policy


SECRET_POLICY = domain_policy("secret_detection")
EXECUTION_ASSET_POLICY = domain_policy("execution_assets")


def validate_source(source):
    if re.search(SECRET_POLICY["raw_assignment_pattern"], source, re.I):
        raise HTTPException(
            status_code=422,
            detail={"code": EXECUTION_ASSET_POLICY["raw_secret_code"]},
        )
    return source


def generated_script(result):
    if result.get("status") != EXECUTION_ASSET_POLICY["success_status"] or result.get(
        "degraded_mode"
    ):
        raise HTTPException(
            503,
            detail={
                "code": EXECUTION_ASSET_POLICY["ai_provider_unavailable_code"],
                "retryable": True,
            },
        )
    suggestions = result.get("suggestions")
    if (
        not isinstance(suggestions, list)
        or len(suggestions) != 1
        or not isinstance(suggestions[0], dict)
    ):
        raise HTTPException(
            502,
            detail={"code": EXECUTION_ASSET_POLICY["ai_script_invalid_code"]},
        )
    source = suggestions[0].get("source")
    placeholders = suggestions[0].get("secret_placeholders", [])
    if (
        not isinstance(source, str)
        or not source.strip()
        or len(source) > int(EXECUTION_ASSET_POLICY["maximum_generated_script_characters"])
        or source.lstrip().startswith(EXECUTION_ASSET_POLICY["generated_code_fence_prefix"])
    ):
        raise HTTPException(
            502,
            detail={"code": EXECUTION_ASSET_POLICY["ai_script_invalid_code"]},
        )
    if not isinstance(placeholders, list) or any(
        not isinstance(item, str)
        or not re.fullmatch(SECRET_POLICY["placeholder_pattern"], item)
        for item in placeholders
    ):
        raise HTTPException(
            502,
            detail={"code": EXECUTION_ASSET_POLICY["ai_script_placeholders_invalid_code"]},
        )
    return validate_source(source), list(dict.fromkeys(placeholders))


def default_filename(framework, language, version):
    key = re.sub(
        EXECUTION_ASSET_POLICY["filename_invalid_character_pattern"],
        "-",
        str(version.get("test_case_key") or EXECUTION_ASSET_POLICY["default_test_case_key"]),
    )
    suffix = EXECUTION_ASSET_POLICY["language_suffixes"][language]
    return f"{key.lower()}.{framework}.{suffix}"


class AutomationScriptService:
    @staticmethod
    async def list(project_id, user):
        await get_project(project_id, user, EXECUTION_ASSET_POLICY["script_export_permission"])
        return await execution_asset_repository.list_script_drafts(project_id)

    @staticmethod
    async def get(draft_id, user):
        return await get_project_entity(
            EXECUTION_ASSET_POLICY["script_collection"],
            draft_id,
            user,
            EXECUTION_ASSET_POLICY["script_export_permission"],
        )

    @staticmethod
    async def generate(project_id, payload, user):
        await get_project(project_id, user, EXECUTION_ASSET_POLICY["script_generate_permission"])
        existing = await execution_asset_repository.find_script_by_idempotency_key(
            project_id, payload.idempotency_key
        )
        if existing:
            return existing, {}
        version = await execution_asset_repository.find_test_case_version(
            project_id, payload.test_case_version_id
        )
        if not version:
            raise HTTPException(
                status_code=422,
                detail={"code": EXECUTION_ASSET_POLICY["invalid_test_case_version_code"]},
            )
        evidence = [
            {
                "artifact_type": EXECUTION_ASSET_POLICY["test_case_evidence_type"],
                "artifact_id": version.get("test_case_id"),
                "artifact_version_id": version["_id"],
                "authority": EXECUTION_ASSET_POLICY["project_approved_test_authority"],
                "text": " ".join(
                    [str(version.get("title") or ""), str(version.get("plain_text_projection") or "")]
                )[: int(EXECUTION_ASSET_POLICY["maximum_evidence_characters"])],
            }
        ]
        ai_result = await request_design_assistance(
            EXECUTION_ASSET_POLICY["script_generation_assistance_type"],
            project_id,
            json.dumps(
                {"framework": payload.framework, "language": payload.language},
                ensure_ascii=False,
            ),
            evidence
            + (
                [
                    {
                        "artifact_type": EXECUTION_ASSET_POLICY["user_context_evidence_type"],
                        "text": payload.context,
                    }
                ]
                if payload.context
                else []
            ),
        )
        source, placeholders = generated_script(ai_result)
        timestamp = now()
        ai_contract = ai_contract_metadata(ai_result)
        value = {
            "_id": new_id(EXECUTION_ASSET_POLICY["script_id_prefix"]),
            "project_id": project_id,
            "test_case_version_id": version["_id"],
            "test_case_id": version.get("test_case_id"),
            "test_case_key": version.get("test_case_key"),
            "framework": payload.framework,
            "language": payload.language,
            "filename": default_filename(payload.framework, payload.language, version),
            "source": source,
            "secret_placeholders": placeholders,
            "model_suggestions": ai_result.get("suggestions", []),
            **ai_contract,
            "ai_contract": ai_contract,
            "ai_status": ai_contract["status"],
            "generation_status": ai_result.get(
                "status", EXECUTION_ASSET_POLICY["success_status"]
            ),
            "status": EXECUTION_ASSET_POLICY["draft_status"],
            "candidate_only": True,
            "repository_write_performed": False,
            "human_confirmation_required": True,
            "idempotency_key": payload.idempotency_key,
            "revision": EXECUTION_ASSET_POLICY["initial_revision"],
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await execution_asset_repository.insert_script_draft(value)
        except DuplicateKeyError:
            existing = await execution_asset_repository.find_script_by_idempotency_key(
                project_id, payload.idempotency_key
            )
            if existing:
                return existing, {}
            raise
        await audit(
            user.id,
            EXECUTION_ASSET_POLICY["script_generated_event"],
            EXECUTION_ASSET_POLICY["script_entity"],
            value["_id"],
            project_id,
            {"framework": payload.framework, "test_case_version_id": version["_id"]},
        )
        return value, {
            "status": ai_result.get("status", EXECUTION_ASSET_POLICY["success_status"]),
            "degraded_mode": ai_result.get("degraded_mode"),
        }

    @staticmethod
    async def update(draft_id, payload, user):
        draft = await get_project_entity(
            EXECUTION_ASSET_POLICY["script_collection"],
            draft_id,
            user,
            EXECUTION_ASSET_POLICY["script_update_permission"],
        )
        if draft.get("status") != EXECUTION_ASSET_POLICY["draft_status"]:
            raise HTTPException(
                status_code=409,
                detail={"code": EXECUTION_ASSET_POLICY["script_not_draft_code"]},
            )
        changes = payload.model_dump(exclude_unset=True)
        if payload.source is not None:
            changes["source"] = validate_source(payload.source)
        updated = await optimistic_patch(
            EXECUTION_ASSET_POLICY["script_collection"],
            draft_id,
            draft["project_id"],
            payload.expected_revision,
            changes,
        )
        await audit(
            user.id,
            EXECUTION_ASSET_POLICY["script_updated_event"],
            EXECUTION_ASSET_POLICY["script_entity"],
            draft_id,
            draft["project_id"],
        )
        return updated

    @staticmethod
    async def approve(draft_id, payload, user):
        draft = await get_project_entity(
            EXECUTION_ASSET_POLICY["script_collection"],
            draft_id,
            user,
            EXECUTION_ASSET_POLICY["script_approve_permission"],
        )
        if draft.get("status") != EXECUTION_ASSET_POLICY["draft_status"]:
            raise HTTPException(
                status_code=409,
                detail={"code": EXECUTION_ASSET_POLICY["script_not_draft_code"]},
            )
        validate_source(draft["source"])
        updated = await optimistic_patch(
            EXECUTION_ASSET_POLICY["script_collection"],
            draft_id,
            draft["project_id"],
            payload.expected_revision,
            {
                "status": EXECUTION_ASSET_POLICY["approved_status"],
                "review_note": payload.review_note,
                "approved_by": user.id,
                "approved_at": now(),
                "human_confirmation_required": False,
            },
        )
        await audit(
            user.id,
            EXECUTION_ASSET_POLICY["script_approved_event"],
            EXECUTION_ASSET_POLICY["script_entity"],
            draft_id,
            draft["project_id"],
            {"review_note": payload.review_note},
        )
        return updated

    @staticmethod
    async def export(draft_id, user):
        draft = await get_project_entity(
            EXECUTION_ASSET_POLICY["script_collection"],
            draft_id,
            user,
            EXECUTION_ASSET_POLICY["script_export_permission"],
        )
        if draft.get("status") != EXECUTION_ASSET_POLICY["approved_status"]:
            raise HTTPException(
                status_code=409,
                detail={"code": EXECUTION_ASSET_POLICY["script_not_approved_code"]},
            )
        source = validate_source(draft["source"])
        await audit(
            user.id,
            EXECUTION_ASSET_POLICY["script_exported_event"],
            EXECUTION_ASSET_POLICY["script_entity"],
            draft_id,
            draft["project_id"],
            {"filename": draft["filename"]},
        )
        return source, draft["filename"]
