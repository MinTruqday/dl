import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from src.repositories.document import DocumentRepository
from src.services.document.crud import DocumentCrudService


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def sort(self, *_args):
        return self

    def limit(self, *_args):
        return self

    async def to_list(self, length):
        return self.rows[:length]


class ProjectDocumentListingTests(unittest.IsolatedAsyncioTestCase):
    async def test_personal_list_keeps_project_artifact_and_indexing_metadata(self):
        rows = [{"_id": "DOC-1", "title": "Profile requirement", "creator_id": "qa-1", "artifact_metadata": {"project_id": "PROJECT-1", "artifact_type": "requirement_version", "artifact_version_id": "REQV-1"}, "is_indexed": True, "indexing_status": "indexed", "chunks_count": 7, "extracted_text": "Indexed project content", "extracted_text_truncated": False, "index_report": {"failed_chunks": [], "quarantined_chunks": []}}]
        with patch.object(DocumentRepository, "find", return_value=FakeCursor(rows)):
            result = await DocumentCrudService.get_my_documents(SimpleNamespace(id="qa-1"), limit=20)
        assert result[0]["artifact_metadata"]["project_id"] == "PROJECT-1"
        assert result[0]["indexing_status"] == "indexed"
        assert result[0]["chunks_count"] == 7
        assert result[0]["extracted_text_available"] is True

    async def test_delete_removes_rag_index_before_soft_delete(self):
        current_user = SimpleNamespace(id="qa-1", role="author")
        update_result = SimpleNamespace(modified_count=1)
        with (patch.object(DocumentRepository, "find_one", AsyncMock(return_value={"_id": "DOC-1", "creator_id": "qa-1", "is_deleted": False})), patch.object(DocumentRepository, "update_one", AsyncMock(return_value=update_result)), patch("src.services.document.crud.knowledge_client.delete_document", AsyncMock()) as deindex):
            result = await DocumentCrudService.soft_delete_document("DOC-1", current_user)
        deindex.assert_awaited_once_with("DOC-1", "qa-1", False)
        assert "thùng rác" in result["message"]


if __name__ == "__main__":
    unittest.main()
