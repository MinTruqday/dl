from src.services.document.base import can_read_full, is_admin, serialize_document
from src.services.document.bulk import DocumentBulkService
from src.services.document.crud import DocumentCrudService
from src.services.document.hierarchy import DocumentHierarchyService
from src.services.document.metadata import DocumentMetadataService
from src.services.document.tag import DocumentTagService


class DocumentService(
    DocumentCrudService,
    DocumentHierarchyService,
    DocumentMetadataService,
    DocumentTagService,
    DocumentBulkService,
):
    _is_admin = staticmethod(is_admin)
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
