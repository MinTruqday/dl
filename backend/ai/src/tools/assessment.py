import json
from typing import Annotated, Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from pydantic import Field

from src.core.infrastructure.configuration import settings
from src.tools.http_client import INTERNAL_API_URL, make_api_request


def auth_headers(config: RunnableConfig):
    token = (config or {}).get("configurable", {}).get("token")
    if not token:
        return None
    return {"Authorization": token, "X-Internal-Token": settings.SECRET_KEY}


async def call_domain(method: str, path: str, config: RunnableConfig, payload: dict | None = None):
    headers = auth_headers(config)
    if not headers:
        return json.dumps({"status": "authentication_required"})
    response = await make_api_request(
        method,
        f"{INTERNAL_API_URL}{path}",
        headers=headers,
        json=payload,
        timeout=60,
    )
    try:
        body = response.json()
    except ValueError:
        body = {"status": "upstream_response_invalid"}
    if response.status_code >= 400:
        return json.dumps(
            {"status": "domain_operation_failed", "upstream_status": response.status_code, "detail": body.get("detail")},
            ensure_ascii=False,
        )
    return json.dumps(body.get("data", body), ensure_ascii=False, default=str)


@tool
async def get_curriculum_context(
    query: Annotated[str, Field(min_length=1, description="Nội dung cần tìm trong chương trình học")],
    education_level: Annotated[str, Field(description="Cấp học mục tiêu")],
    subject: Annotated[str, Field(description="Môn học mục tiêu")],
    target_program: Annotated[str, Field(description="Chương trình mục tiêu")],
    lesson_id: Annotated[str, Field(description="Mã bài học nếu đã biết")] = "",
    config: RunnableConfig = None,
) -> str:
    """Truy xuất bằng chứng chương trình học theo metadata và provenance"""
    filters = {
        "education_level": education_level,
        "subject": subject,
        "target_program": target_program,
        "source_type": "curriculum",
        "authority": ["official", "verified"],
    }
    if lesson_id:
        filters["lesson_id"] = lesson_id
    return await call_domain(
        "POST",
        "/rag/retrieve",
        config,
        {"query": query, "k": 8, "metadata_filters": filters},
    )


@tool
async def get_teacher_material_context(
    query: Annotated[str, Field(min_length=1, description="Nội dung cần tìm trong tài liệu riêng của giáo viên")],
    subject: Annotated[str, Field(description="Môn học nếu đã biết")] = "",
    target_program: Annotated[str, Field(description="Chương trình mục tiêu nếu đã biết")] = "",
    config: RunnableConfig = None,
) -> str:
    """Truy xuất tài liệu riêng trong đúng phạm vi chủ sở hữu hiện tại"""
    policy = await call_domain("GET", "/education/teacher-profile/me", config)
    try:
        profile = json.loads(policy)
    except (TypeError, json.JSONDecodeError):
        return json.dumps({"status": "teacher_material_policy_unavailable"})
    if profile.get("status"):
        return policy
    if profile.get("use_own_materials") is False:
        return json.dumps({"status": "teacher_material_use_disabled"})
    filters = {"source_type": "teacher_material"}
    if subject:
        filters["subject"] = subject
    if target_program:
        filters["target_program"] = target_program
    return await call_domain(
        "POST",
        "/rag/retrieve",
        config,
        {"query": query, "k": 8, "metadata_filters": filters},
    )


@tool
async def create_question_draft(
    assessment_draft_id: Annotated[str, Field(description="Mã bản nháp bài đánh giá")],
    question_json: Annotated[str, Field(description="QuestionDraft JSON có Tiptap JSON và scoring tách biệt")],
    config: RunnableConfig = None,
) -> str:
    """Tạo QuestionDraft bằng domain operation để giáo viên rà soát"""
    try:
        payload = json.loads(question_json)
    except (TypeError, json.JSONDecodeError):
        return json.dumps({"status": "question_payload_invalid"})
    return await call_domain("POST", f"/assessment-drafts/{assessment_draft_id}/questions", config, payload)


@tool
async def import_assessment(
    assessment_draft_id: Annotated[str, Field(description="Mã bản nháp bài đánh giá")],
    import_json: Annotated[str, Field(description="ImportRequest JSON gồm nguồn trang và khóa chống lặp")],
    config: RunnableConfig = None,
) -> str:
    """Phân tích nguồn nhập thành candidate và giữ bước xác nhận của giáo viên"""
    try:
        payload = json.loads(import_json)
    except (TypeError, json.JSONDecodeError):
        return json.dumps({"status": "import_payload_invalid"})
    return await call_domain("POST", f"/assessment-drafts/{assessment_draft_id}/import", config, payload)


@tool
async def map_question_to_curriculum(
    question_draft_id: Annotated[str, Field(description="Mã QuestionDraft cần gắn chương trình")],
    expected_revision: Annotated[int, Field(ge=1, description="Revision hiện tại của QuestionDraft")],
    curriculum_links_json: Annotated[str, Field(description="Danh sách JSON curriculum links có provenance")],
    concept_ids_json: Annotated[str, Field(description="Danh sách JSON concept IDs")],
    skill_ids_json: Annotated[str, Field(description="Danh sách JSON skill IDs")],
    config: RunnableConfig = None,
) -> str:
    """Gắn QuestionDraft vào curriculum bằng optimistic concurrency và stable IDs"""
    try:
        curriculum_links = json.loads(curriculum_links_json)
        concept_ids = json.loads(concept_ids_json)
        skill_ids = json.loads(skill_ids_json)
    except (TypeError, json.JSONDecodeError):
        return json.dumps({"status": "curriculum_mapping_payload_invalid"})
    if not isinstance(curriculum_links, list) or not isinstance(concept_ids, list) or not isinstance(skill_ids, list):
        return json.dumps({"status": "curriculum_mapping_payload_invalid"})
    return await call_domain(
        "PATCH",
        f"/question-drafts/{question_draft_id}",
        config,
        {
            "expected_revision": expected_revision,
            "curriculum_links": curriculum_links,
            "concept_ids": concept_ids,
            "skill_ids": skill_ids,
        },
    )


@tool
async def analyze_question(
    question_draft_id: Annotated[str, Field(description="Mã QuestionDraft cần kiểm định")],
    config: RunnableConfig = None,
) -> str:
    """Chạy bộ kiểm định chất lượng có cấu trúc cho QuestionDraft"""
    return await call_domain("POST", f"/question-drafts/{question_draft_id}/validate", config)


@tool
async def record_teacher_difficulty_estimate(
    question_draft_id: Annotated[str, Field(description="Mã QuestionDraft")],
    estimated_difficulty: Annotated[float, Field(ge=1, le=5, description="Ước lượng độ khó của giáo viên")],
    self_confidence: Annotated[str, Field(description="Mức tự tin low medium hoặc high")] = "medium",
    config: RunnableConfig = None,
) -> str:
    """Ghi snapshot ước lượng giáo viên mà không ghi đè lịch sử"""
    return await call_domain(
        "POST",
        f"/question-drafts/{question_draft_id}/teacher-estimate",
        config,
        {"estimated_difficulty": estimated_difficulty, "self_confidence": self_confidence},
    )


@tool
async def predict_item_difficulty(
    question_draft_id: Annotated[str, Field(description="Mã QuestionDraft")],
    model_version: Annotated[str, Field(description="Phiên bản mô hình dự đoán")] = "structured_cold_start_v2",
    prediction_kind: Annotated[str, Field(description="structured hoặc llm_direct")] = "structured",
    config: RunnableConfig = None,
) -> str:
    """Tạo dự đoán cold start có uncertainty và feature snapshot"""
    return await call_domain(
        "POST",
        f"/question-drafts/{question_draft_id}/predict-difficulty",
        config,
        {"model_version": model_version, "prediction_kind": prediction_kind},
    )


@tool
async def get_item_calibration(
    question_version_id: Annotated[str, Field(description="Mã QuestionVersion bất biến")],
    config: RunnableConfig = None,
) -> str:
    """Lấy lịch sử snapshot hiệu chỉnh thực nghiệm của một QuestionVersion"""
    return await call_domain("GET", f"/questions/{question_version_id}/calibration", config)


@tool
async def compare_difficulty_signals(
    question_version_id: Annotated[str, Field(description="Mã QuestionVersion bất biến")],
    config: RunnableConfig = None,
) -> str:
    """Đối chiếu target teacher AI và empirical cùng context bằng chứng"""
    return await call_domain("GET", f"/questions/{question_version_id}/difficulty-signals", config)


@tool
async def inspect_question_versions(
    question_id: Annotated[str, Field(description="Mã logical Question cần so sánh các version")],
    config: RunnableConfig = None,
) -> str:
    """Lấy chuỗi QuestionVersion bất biến để điều tra thay đổi nội dung và construct"""
    return await call_domain("GET", f"/questions/{question_id}/versions", config)


@tool
async def get_question_research_metrics(
    question_id: Annotated[str, Field(description="Mã logical Question cần đo error v1 và v2")],
    config: RunnableConfig = None,
) -> str:
    """Lấy sai số teacher AI empirical qua các version và mức giảm sai số"""
    return await call_domain("GET", f"/questions/{question_id}/research-metrics", config)


@tool
async def get_research_evaluation(config: RunnableConfig = None) -> str:
    """Lấy MAE RMSE correlation teacher baseline AI hybrid và kiểm tra data leakage"""
    return await call_domain("GET", "/research/evaluation", config)


@tool
async def evaluate_learner_fit(
    assessment_draft_id: Annotated[str, Field(description="Mã AssessmentDraft cần đánh giá độ phù hợp")],
    minimum_ability: Annotated[float, Field(ge=1, le=5, description="Cận dưới dải năng lực mục tiêu")],
    maximum_ability: Annotated[float, Field(ge=1, le=5, description="Cận trên dải năng lực mục tiêu")],
    minimum_success: Annotated[float, Field(gt=0, lt=1, description="Cận dưới xác suất thành công mục tiêu")] = 0.45,
    maximum_success: Annotated[float, Field(gt=0, lt=1, description="Cận trên xác suất thành công mục tiêu")] = 0.8,
    config: RunnableConfig = None,
) -> str:
    """Đánh giá learner fit deterministic và không thay đổi bản nháp"""
    if minimum_ability > maximum_ability or minimum_success >= maximum_success:
        return json.dumps({"status": "learner_fit_range_invalid"})
    return await call_domain(
        "POST",
        f"/assessment-drafts/{assessment_draft_id}/learner-fit",
        config,
        {
            "target_learner": {
                "ability_band": [minimum_ability, maximum_ability],
                "confidence": 0.4,
                "source": "agent_requested_generic_band",
            },
            "target_success_range": [minimum_success, maximum_success],
        },
    )


@tool
async def analyze_blueprint_impact(
    assessment_draft_id: Annotated[str, Field(description="Mã AssessmentDraft cần mô phỏng tác động Blueprint")],
    config: RunnableConfig = None,
) -> str:
    """Đối chiếu phân bố hiện tại với Blueprint mà không tự sửa câu hỏi"""
    return await call_domain("GET", f"/assessment-drafts/{assessment_draft_id}/difficulty-analysis", config)


@tool
async def run_calibration(
    question_version_ids_json: Annotated[str, Field(description="Danh sách JSON QuestionVersion cần hiệu chỉnh")],
    population_context_json: Annotated[str, Field(description="JSON mô tả sample và population")],
    method: Annotated[str, Field(description="CTT hoặc Rasch")] = "CTT",
    config: RunnableConfig = None,
) -> str:
    """Chạy psychometrics deterministic và tạo snapshot mới"""
    try:
        question_version_ids = json.loads(question_version_ids_json)
        population_context = json.loads(population_context_json)
    except (TypeError, json.JSONDecodeError):
        return json.dumps({"status": "calibration_payload_invalid"})
    return await call_domain(
        "POST",
        "/calibration/run",
        config,
        {
            "question_version_ids": question_version_ids,
            "population_context": population_context,
            "method": method,
            "evidence_policy_version": "ai_v1",
        },
    )


@tool
async def verify_construct_preservation(
    original_construct_json: Annotated[str, Field(description="Construct JSON của phiên bản gốc")],
    proposed_construct_json: Annotated[str, Field(description="Construct JSON của phiên bản đề xuất")],
) -> str:
    """Kiểm tra concept learning objective và primary skill trước khi tạo revision"""
    try:
        original = json.loads(original_construct_json)
        proposed = json.loads(proposed_construct_json)
    except (TypeError, json.JSONDecodeError):
        return json.dumps({"status": "construct_payload_invalid"})
    keys = ["primary_concept", "learning_objective", "primary_skill"]
    checks = {key: original.get(key) == proposed.get(key) for key in keys}
    return json.dumps({"passed": all(checks.values()), "checks": checks}, ensure_ascii=False)


@tool
async def propose_question_revision(
    question_id: Annotated[str, Field(description="Mã logical Question")],
    proposal_json: Annotated[str, Field(description="RevisionProposal JSON gồm evidence reason và construct check")],
    config: RunnableConfig = None,
) -> str:
    """Tạo revision proposal chờ giáo viên duyệt mà không sửa production"""
    try:
        payload = json.loads(proposal_json)
    except (TypeError, json.JSONDecodeError):
        return json.dumps({"status": "revision_payload_invalid"})
    return await call_domain("POST", f"/questions/{question_id}/revisions", config, payload)


@tool
async def create_revision_draft(
    question_draft_id: Annotated[str, Field(description="Mã QuestionDraft cần tạo proposal")],
    action: Annotated[
        Literal["increase_difficulty", "decrease_difficulty", "clarify_wording", "regenerate_distractors"],
        Field(description="Hành động proposal có cấu trúc"),
    ],
    instruction: Annotated[str, Field(description="Chỉ dẫn có bằng chứng cho proposal")] = "",
    config: RunnableConfig = None,
) -> str:
    """Tạo draft revision chờ giáo viên duyệt và không sửa bản nháp hiện tại"""
    if action in {"clarify_wording", "regenerate_distractors"} and not instruction.strip():
        return json.dumps({"status": "revision_instruction_required", "action": action}, ensure_ascii=False)
    return await call_domain(
        "POST",
        f"/question-drafts/{question_draft_id}/ai/revise",
        config,
        {"action": action, "instruction": instruction},
    )


@tool
async def publish_assessment_version(
    assessment_id: Annotated[str, Field(description="Mã Assessment")],
    assessment_draft_id: Annotated[str, Field(description="Mã AssessmentDraft")],
    expected_revision: Annotated[int, Field(ge=1, description="Revision hiện tại của AssessmentDraft")],
    idempotency_key: Annotated[str, Field(min_length=8, description="Khóa chống publish lặp")],
    config: RunnableConfig = None,
) -> str:
    """Đóng băng và publish AssessmentVersion qua approval policy"""
    return await call_domain(
        "POST",
        f"/assessments/{assessment_id}/publish",
        config,
        {
            "assessment_draft_id": assessment_draft_id,
            "expected_revision": expected_revision,
            "idempotency_key": idempotency_key,
        },
    )
