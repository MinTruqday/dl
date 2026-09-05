import pytest
from fastapi import HTTPException

from src.core.auth import CurrentUser
from src.services import execution_context


USER = CurrentUser(_id="user-1", email="user@example.test")


@pytest.mark.asyncio
async def test_resolves_execution_context_ids_to_canonical_labels(monkeypatch):
    entities = {
        ("releases", "release-1"): {
            "_id": "release-1",
            "project_id": "project-1",
            "key": "REL-1",
            "status": "ACTIVE",
        },
        ("builds", "build-1"): {
            "_id": "build-1",
            "project_id": "project-1",
            "identifier": "BUILD-1",
            "release_id": "release-1",
        },
        ("test_environments", "environment-1"): {
            "_id": "environment-1",
            "project_id": "project-1",
            "name": "Staging",
            "status": "ACTIVE",
        },
    }

    async def get_entity(collection, entity_id, user, permission):
        return entities[(collection, entity_id)]

    monkeypatch.setattr(execution_context, "get_project_entity", get_entity)
    value = await execution_context.resolve_execution_context(
        "project-1",
        USER,
        release_id="release-1",
        build_id="build-1",
        environment_id="environment-1",
    )
    assert value == {
        "release_id": "release-1",
        "build_id": "build-1",
        "environment_id": "environment-1",
        "release": "REL-1",
        "build": "BUILD-1",
        "environment": "Staging",
    }


@pytest.mark.asyncio
async def test_rejects_context_from_another_project(monkeypatch):
    async def get_entity(collection, entity_id, user, permission):
        return {"_id": entity_id, "project_id": "project-2", "key": "REL-2"}

    monkeypatch.setattr(execution_context, "get_project_entity", get_entity)
    with pytest.raises(HTTPException) as error:
        await execution_context.resolve_execution_context(
            "project-1", USER, release_id="release-2"
        )
    assert error.value.detail == {"code": "PROJECT_MISMATCH"}


@pytest.mark.asyncio
async def test_rejects_build_release_mismatch(monkeypatch):
    entities = {
        ("releases", "release-1"): {
            "_id": "release-1",
            "project_id": "project-1",
            "key": "REL-1",
            "status": "ACTIVE",
        },
        ("builds", "build-1"): {
            "_id": "build-1",
            "project_id": "project-1",
            "identifier": "BUILD-1",
            "release_id": "release-2",
        },
    }

    async def get_entity(collection, entity_id, user, permission):
        return entities[(collection, entity_id)]

    monkeypatch.setattr(execution_context, "get_project_entity", get_entity)
    with pytest.raises(HTTPException) as error:
        await execution_context.resolve_execution_context(
            "project-1", USER, release_id="release-1", build_id="build-1"
        )
    assert error.value.detail == {"code": "BUILD_RELEASE_MISMATCH"}


@pytest.mark.asyncio
async def test_derives_linked_release_from_build(monkeypatch):
    entities = {
        ("builds", "build-1"): {
            "_id": "build-1",
            "project_id": "project-1",
            "identifier": "BUILD-1",
            "release_id": "release-1",
        },
        ("releases", "release-1"): {
            "_id": "release-1",
            "project_id": "project-1",
            "key": "REL-1",
            "status": "ACTIVE",
        },
    }

    async def get_entity(collection, entity_id, user, permission):
        return entities[(collection, entity_id)]

    monkeypatch.setattr(execution_context, "get_project_entity", get_entity)
    value = await execution_context.resolve_execution_context(
        "project-1", USER, build_id="build-1"
    )
    assert value["release_id"] == "release-1"
    assert value["release"] == "REL-1"


@pytest.mark.asyncio
async def test_preserves_legacy_labels_without_context_ids():
    value = await execution_context.resolve_execution_context(
        "project-1",
        USER,
        release="Legacy release",
        build="Legacy build",
        environment="Legacy environment",
    )
    assert value["release"] == "Legacy release"
    assert value["build"] == "Legacy build"
    assert value["environment"] == "Legacy environment"
