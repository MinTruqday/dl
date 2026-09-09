import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from src.domain.schemas import GenerateInput
from src.services.generation import generate_requirement_drafts


class GenerationTests(unittest.IsolatedAsyncioTestCase):
    async def generate(self, result, scenario=False):
        with patch("src.services.generation.request_design_assistance", AsyncMock(return_value=result)):
            return await generate_requirement_drafts(
                {"_id": "V1", "project_id": "P1", "plain_text_projection": "Phone requires 10 digits"},
                [{"_id": "AC1", "plain_text": "Reject 9 digits"}],
                GenerateInput(categories=["boundary"]),
                scenario=scenario,
            )

    def result(self):
        return {"status": "SUCCESS", "model": {"provider": "primary"}, "suggestions": [{"title": "Từ chối số điện thoại 9 chữ số", "category": "boundary", "objective": "Kiểm tra giới hạn dưới", "preconditions": "Mở biểu mẫu số điện thoại", "steps": [{"action": "Nhập 123456789 và lưu", "expected": "Báo cần đủ 10 chữ số", "test_data": {"phone": "123456789"}}], "expected": "Không lưu số điện thoại thiếu chữ số", "acceptance_criterion_ids": ["AC1"]}]}

    async def test_model_content_becomes_test_draft(self):
        drafts, result = await self.generate(self.result())
        self.assertEqual("123456789", drafts[0].steps[0].test_data["phone"])
        self.assertEqual(["V1"], drafts[0].requirement_version_ids)
        self.assertEqual("primary", result["model"]["provider"])

    async def test_model_content_becomes_scenario(self):
        drafts, _ = await self.generate(self.result(), scenario=True)
        self.assertEqual("Kiểm tra giới hạn dưới", drafts[0].objective)
        self.assertEqual("draft", drafts[0].status)

    async def test_unavailable_model_does_not_generate_template(self):
        with self.assertRaises(HTTPException) as caught:
            await self.generate({"status": "DEGRADED"})
        self.assertEqual(503, caught.exception.status_code)

    async def test_unknown_evidence_is_rejected(self):
        result = self.result()
        result["suggestions"][0]["acceptance_criterion_ids"] = ["OTHER_PROJECT"]
        with self.assertRaises(HTTPException) as caught:
            await self.generate(result)
        self.assertEqual(502, caught.exception.status_code)

    async def test_missing_category_is_rejected(self):
        result = self.result()
        result["suggestions"] = []
        with self.assertRaises(HTTPException) as caught:
            await self.generate(result)
        self.assertEqual(502, caught.exception.status_code)
