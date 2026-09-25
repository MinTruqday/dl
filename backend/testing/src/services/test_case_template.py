from collections.abc import Sequence

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser
from src.core.common import (
    audit,
    get_project,
    get_project_entity,
    load_user_identities,
    new_id,
    now,
    require_action_policy,
)
from src.repositories.test_design import test_design_repository
from src.domain.test_case_template import (
    TemplateType,
    TestCaseTemplateArchive,
    TestCaseTemplateCreate,
    TestCaseTemplatePatch,
)
from src.services.domain_policy import domain_policy


TEMPLATE_POLICY = domain_policy("test_case_template")


class TestCaseTemplateService:
    @staticmethod
    async def list(project_id: str, template_type: TemplateType | None, user: CurrentUser):
        await get_project(project_id, user, TEMPLATE_POLICY["read_permission"])
        query = {"project_id": project_id, "status": TEMPLATE_POLICY["active_status"]}
        if template_type:
            query["template_type"] = template_type
        items = await test_design_repository.list_templates(query)
        await TestCaseTemplateService._add_creator_labels(items)
        return items

    @staticmethod
    async def get(template_id: str, user: CurrentUser):
        item = await get_project_entity(
            TEMPLATE_POLICY["collection"],
            template_id,
            user,
            TEMPLATE_POLICY["read_permission"],
        )
        await TestCaseTemplateService._add_creator_labels([item])
        return item

    @staticmethod
    async def create(
        project_id: str,
        payload: TestCaseTemplateCreate,
        user: CurrentUser,
    ):
        await get_project(project_id, user, TEMPLATE_POLICY["manage_permission"])
        timestamp = now()
        template = {
            "_id": new_id(TEMPLATE_POLICY["id_prefix"]),
            "project_id": project_id,
            **payload.model_dump(),
            "status": TEMPLATE_POLICY["active_status"],
            "revision": TEMPLATE_POLICY["initial_revision"],
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await test_design_repository.insert_template(template)
        except DuplicateKeyError as error:
            raise HTTPException(
                status_code=409, detail={"code": TEMPLATE_POLICY["name_exists_code"]}
            ) from error
        await audit(
            user.id,
            TEMPLATE_POLICY["created_event"],
            TEMPLATE_POLICY["entity"],
            template["_id"],
            project_id,
        )
        return template

    @staticmethod
    async def update(
        template_id: str,
        payload: TestCaseTemplatePatch,
        user: CurrentUser,
    ):
        template = await get_project_entity(
            TEMPLATE_POLICY["collection"],
            template_id,
            user,
            TEMPLATE_POLICY["manage_permission"],
        )
        if template.get("status") != TEMPLATE_POLICY["active_status"]:
            raise HTTPException(
                status_code=409, detail={"code": TEMPLATE_POLICY["archived_code"]}
            )
        changes = payload.model_dump(exclude={"expected_revision"}, exclude_none=True)
        updated = await test_design_repository.update_template(
            template_id,
            template["project_id"],
            payload.expected_revision,
            TEMPLATE_POLICY["active_status"],
            {**changes, "updated_at": now()},
        )
        if not updated:
            raise HTTPException(
                status_code=409, detail={"code": TEMPLATE_POLICY["revision_conflict_code"]}
            )
        await audit(
            user.id,
            TEMPLATE_POLICY["updated_event"],
            TEMPLATE_POLICY["entity"],
            template_id,
            template["project_id"],
        )
        return updated

    @staticmethod
    async def archive(
        template_id: str,
        payload: TestCaseTemplateArchive,
        user: CurrentUser,
    ):
        template = await get_project_entity(
            TEMPLATE_POLICY["collection"],
            template_id,
            user,
            TEMPLATE_POLICY["manage_permission"],
        )
        await require_action_policy(
            template["project_id"],
            user,
            TEMPLATE_POLICY["archive_permission"],
            set(TEMPLATE_POLICY["archive_roles"]),
        )
        if template.get("status") == TEMPLATE_POLICY["archived_status"]:
            return template
        updated = await test_design_repository.update_template(
            template_id,
            template["project_id"],
            payload.expected_revision,
            TEMPLATE_POLICY["active_status"],
            {
                "status": TEMPLATE_POLICY["archived_status"],
                "archive_reason": payload.reason,
                "updated_at": now(),
            },
        )
        if not updated:
            raise HTTPException(
                status_code=409, detail={"code": TEMPLATE_POLICY["revision_conflict_code"]}
            )
        await audit(
            user.id,
            TEMPLATE_POLICY["archived_event"],
            TEMPLATE_POLICY["entity"],
            template_id,
            template["project_id"],
            {"reason": payload.reason},
        )
        return updated

    @staticmethod
    async def _add_creator_labels(items: Sequence[dict]):
        identities = await load_user_identities(item.get("created_by") for item in items)
        for item in items:
            identity = identities.get(str(item.get("created_by")))
            item["created_by_label"] = identity.get("label") if identity else item.get("created_by")
