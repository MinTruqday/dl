from src.services.document.base import (
    serialize_document,
    is_admin,
    get_effective_collaboration_status,
    can_read_full,
)
from src.services.document.crud import DocumentCrudService
from src.services.document.hierarchy import DocumentHierarchyService
from src.services.document.metadata import DocumentMetadataService
from src.services.document.tag import DocumentTagService
from src.services.document.bulk import DocumentBulkService

class DocumentService(
    DocumentCrudService,
    DocumentHierarchyService,
    DocumentMetadataService,
    DocumentTagService,
    DocumentBulkService,
):
    _is_admin = staticmethod(is_admin)
    _get_effective_collaboration_status = staticmethod(get_effective_collaboration_status)
    _can_read_full = staticmethod(can_read_full)

__all__ = [
    "DocumentService",
    "DocumentCrudService",
    "DocumentHierarchyService",
    "DocumentMetadataService",
    "DocumentTagService",
    "DocumentBulkService",
    "serialize_document",
]
