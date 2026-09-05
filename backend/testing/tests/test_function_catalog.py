import re

from src.core.function_ids import FUNCTION_IDS
from src.main import app


ALLOWED_UNMAPPED_ENDPOINTS = {
    "process_job",
    "enqueue_job",
    "get_job",
    "operations",
    "retry_failed_job",
}


def test_testing_routes_have_canonical_function_metadata():
    routes = [route for route in app.routes if getattr(route, "path", "").startswith("/kiem-thu")]
    missing = {
        route.endpoint.__name__
        for route in routes
        if "x-function-ids" not in (getattr(route, "openapi_extra", None) or {})
    }
    assert missing <= ALLOWED_UNMAPPED_ENDPOINTS
    assert len(routes) >= 240


def test_function_catalog_ids_are_well_formed():
    values = {value for ids in FUNCTION_IDS.values() for value in ids}
    assert values
    assert all(re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+", value) for value in values)
