import json
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.schemas.inference import TestingAssistanceRequest
from src.services.testing_assistance import generate_testing_assistance


class TestingSkillInput(BaseModel):
    project_id: Annotated[str, Field(description="Testing project identifier")]
    instruction: Annotated[str, Field(description="Runtime instruction for the current request")] = ""


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
    testing_skill("project_question", "Answer a project question only from retrieved evidence"),
    testing_skill(
        "requirement_quality_analysis",
        "Analyze requirement quality and create evidence grounded proposals",
    ),
    testing_skill("scenario_generation", "Generate structured test scenarios from evidence"),
    testing_skill("test_generation", "Generate structured test cases from evidence"),
    testing_skill("impact_analysis", "Classify change impact from evidence"),
    testing_skill("security_test_generation", "Generate security test candidates"),
    testing_skill("performance_plan_generation", "Generate performance test plan candidates"),
    testing_skill("automation_script_generation", "Generate an automation script draft"),
    testing_skill("test_condition_generation", "Generate structured test conditions"),
    testing_skill("causal_analysis", "Generate evidence grounded causal hypotheses"),
    testing_skill("status_report_narrative", "Draft an evidence grounded status report"),
    testing_skill("completion_report_narrative", "Draft an evidence grounded completion report"),
    testing_skill("lessons_learned_clustering", "Cluster lessons learned from evidence"),
]
