from src.core.common import audit, get_project, get_project_entity
from src.repositories import analysis_repository
from src.services.design_assistance import ai_contract_metadata
from src.services.domain_policy import domain_policy
from src.services.generation import generate_requirement_drafts
from src.services.linters import duplicate_score
from src.services.test_case_records import create_test_case_draft_record


async def generate_test_case_draft_records(version_id, payload, user):
    version = await get_project_entity(
        "requirement_versions", version_id, user, "ai.generate_testcase"
    )
    await get_project(version["project_id"], user, "testcase.create")
    criteria = await analysis_repository.list_acceptance_criteria(version_id)
    drafts, result = await generate_requirement_drafts(version, criteria, payload, scenario=False)
    created = [
        await create_test_case_draft_record(version["project_id"], draft, user) for draft in drafts
    ]
    await audit(
        user.id,
        "test_case_drafts_generated",
        "RequirementVersion",
        version_id,
        version["project_id"],
        {"count": len(created), "model": result.get("model", {})},
    )
    return {
        "items": created,
        "evidence": criteria,
        **ai_contract_metadata(result),
        "generation_status": result["status"],
    }


async def find_duplicate_test_case_records(project_id, user):
    await get_project(project_id, user, "testcase.duplicate_check")
    await get_project(project_id, user, "ai.run_duplicate_check")
    policy = domain_policy("duplicate_detection")
    versions = await analysis_repository.list_active_test_case_versions(
        project_id, policy["test_case_active_status"]
    )
    pairs = []
    for index, left in enumerate(versions):
        for right in versions[index + 1 :]:
            score, reasons = duplicate_score(left, right)
            if score >= policy["test_case_minimum"]:
                pairs.append(
                    {"left": left, "right": right, "similarity": score, "reasons": reasons}
                )
    return sorted(pairs, key=lambda item: item["similarity"], reverse=True)[
        : policy["maximum_pairs"]
    ]
