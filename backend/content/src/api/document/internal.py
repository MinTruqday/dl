from fastapi import APIRouter, Depends

from src.core.dependency import verify_internal_token
from src.services.document.internal import (
    exchange_internal_document,
    get_internal_document,
    get_internal_document_stats,
    internal_document_data,
)

router = APIRouter(dependencies=[Depends(verify_internal_token)])


router.add_api_route(
    "/noi-bo/tai-lieu",
    internal_document_data,
    methods=["POST"],
    include_in_schema=False,
)
router.add_api_route(
    "/noi-bo/truy-cap",
    get_internal_document,
    methods=["POST"],
    include_in_schema=False,
)
router.add_api_route(
    "/noi-bo/thong-ke",
    get_internal_document_stats,
    methods=["POST"],
    include_in_schema=False,
)
router.add_api_route(
    "/noi-bo/trao-doi",
    exchange_internal_document,
    methods=["POST"],
    include_in_schema=False,
)
