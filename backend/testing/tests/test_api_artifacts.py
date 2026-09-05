from src.api.api_artifacts import operation_fingerprint, operation_identity, public_api_import


def test_public_api_import_does_not_return_raw_preview_by_default():
    value = public_api_import(
        {
            "_id": "artifact-1",
            "raw_content": {"secret": "value"},
            "preview": [{"method": "GET", "path": "/users"}],
            "status": "PREVIEW_READY",
        }
    )
    assert "raw_content" not in value
    assert "preview" not in value
    assert value["preview_count"] == 1


def test_operation_identity_and_fingerprint_ignore_storage_metadata():
    before = {
        "_id": "operation-1",
        "project_id": "project-1",
        "import_id": "artifact-1",
        "method": "get",
        "path": "/users",
        "responses": [200],
    }
    after = {**before, "_id": "operation-2", "import_id": "artifact-2"}
    assert operation_identity(before) == "GET /users"
    assert operation_fingerprint(before) == operation_fingerprint(after)
    assert operation_fingerprint(before) != operation_fingerprint({**after, "responses": [201]})
