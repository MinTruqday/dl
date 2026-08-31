import unittest

from pydantic import ValidationError

from src.schemas.document import DocumentCreate, DocumentUpdate


class ProjectArtifactSchemaTests(unittest.TestCase):
    def test_project_artifact_metadata_is_supported_on_create_and_file_update(self):
        metadata = {"project_id": "PROJECT-1", "artifact_type": "requirement_version", "artifact_id": "REQ-1", "artifact_version_id": "REQV-1", "authority": "baseline", "source_version": "a" * 64}
        created = DocumentCreate(title="Project requirement", artifact_metadata=metadata)
        updated = DocumentUpdate(file_url="s3://projects/requirement.pdf", content_format="pdf", artifact_metadata=metadata)
        self.assertEqual(created.artifact_metadata.project_id, "PROJECT-1")
        self.assertEqual(created.artifact_metadata.authority, "baseline")
        self.assertEqual(updated.content_format.value, "pdf")

    def test_project_artifact_requires_project_identity(self):
        with self.assertRaises(ValidationError):
            DocumentCreate(title="Unscoped source", artifact_metadata={"artifact_type": "requirement_version", "authority": "baseline"})


if __name__ == "__main__":
    unittest.main()
