import json
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.schemas.inference import TestingAssistanceRequest
from src.services.testing_assistance import generate_testing_assistance


class TestingSkillInput(BaseModel):
    project_id: Annotated[str, Field(description="Mã dự án kiểm thử")]
    instruction: Annotated[str, Field(description="Yêu cầu động cho lần xử lý hiện tại")] = ""


async def execute_skill(capability, project_id, instruction, config):
    evidence = (config or {}).get("configurable", {}).get("evidence", [])
    if not evidence:
        return json.dumps(
            {
                "status": "INSUFFICIENT_EVIDENCE",
                "capability": capability,
                "reason_codes": ["INSUFFICIENT_EVIDENCE"],
            }
        )
    result = await generate_testing_assistance(
        TestingAssistanceRequest(
            capability=capability,
            project_id=project_id,
            instruction=instruction,
            evidence=evidence,
        )
    )
    return result.model_dump_json()


def testing_skill(capability, description):
    async def invoke(
        project_id: str,
        instruction: str = "",
        config: RunnableConfig = None,
    ):
        return await execute_skill(capability, project_id, instruction, config)

    return StructuredTool.from_function(
        coroutine=invoke,
        name=capability,
        description=description,
        args_schema=TestingSkillInput,
    )


structured_skills = [
    testing_skill("project_question", "Trả lời câu hỏi dự án chỉ từ bằng chứng đã truy xuất"),
    testing_skill(
        "requirement_quality_analysis",
        "Phân tích chất lượng requirement và tạo đề xuất có căn cứ",
    ),
    testing_skill("scenario_generation", "Sinh test scenario có cấu trúc từ bằng chứng"),
    testing_skill("test_generation", "Sinh test case có cấu trúc từ bằng chứng"),
    testing_skill("impact_analysis", "Phân loại ảnh hưởng thay đổi từ bằng chứng"),
    testing_skill("security_test_generation", "Sinh ứng viên kiểm thử bảo mật"),
    testing_skill("performance_plan_generation", "Sinh ứng viên kế hoạch kiểm thử hiệu năng"),
    testing_skill("automation_script_generation", "Sinh bản nháp automation script"),
    testing_skill("test_condition_generation", "Sinh test condition có cấu trúc"),
    testing_skill("causal_analysis", "Sinh giả thuyết phân tích nguyên nhân có căn cứ"),
    testing_skill("status_report_narrative", "Soạn bản nháp báo cáo trạng thái có căn cứ"),
    testing_skill("completion_report_narrative", "Soạn bản nháp báo cáo hoàn tất có căn cứ"),
    testing_skill("lessons_learned_clustering", "Gom nhóm bài học kinh nghiệm có căn cứ"),
]
