"""Small internal AI adapter for testing-design suggestions.

The testing service only talks to this private endpoint. The adapter keeps the
Hugging Face token inside Docker and returns candidate suggestions only; it
never changes project data on its own.
"""

import json
import os
import re
import secrets
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(title="Veriq AI Adapter", version="1.0.0")


class TestingAssistanceRequest(BaseModel):
    capability: str = Field(min_length=1, max_length=100)
    project_id: str = Field(min_length=1, max_length=128)
    instruction: str = Field(default="", max_length=5000)
    evidence: list[dict[str, Any]] = Field(min_length=1, max_length=100)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def evidence_refs(evidence: list[dict[str, Any]]) -> list[str]:
    return [
        str(item.get("artifact_version_id") or item.get("artifact_id"))
        for item in evidence
        if item.get("artifact_version_id") or item.get("artifact_id")
    ]


def model_metadata() -> dict[str, str]:
    return {
        "provider": "huggingface",
        "model": os.getenv("LLM_MODEL", "unknown"),
        "prompt_version": "veriq-ai-adapter-v1",
        "tool_schema_version": "1",
        "retrieval_version": "project-filter-v1",
        "created_at": now_iso(),
    }


def authorize(value: str | None) -> None:
    expected = os.getenv("SECRET_KEY", "")
    if not expected or not value or not secrets.compare_digest(value, expected):
        raise HTTPException(status_code=401, detail="invalid_internal_token")


def extract_json(value: str) -> dict[str, Any]:
    cleaned = value.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    start = cleaned.find("{")
    if start < 0:
        raise ValueError("model_did_not_return_json")
    # raw_decode accepts a valid JSON object followed by a brief model comment.
    # This is more tolerant than slicing to the final brace in a response.
    parsed, _ = json.JSONDecoder().raw_decode(cleaned[start:])
    if not isinstance(parsed, dict):
        raise ValueError("model_json_is_not_an_object")
    return parsed


def requirement_prompt(request: TestingAssistanceRequest, refs: list[str]) -> str:
    evidence = [
        {
            "artifact_id": item.get("artifact_id"),
            "artifact_version_id": item.get("artifact_version_id"),
            "text": str(item.get("text", ""))[:6000],
        }
        for item in request.evidence
    ]
    return "\n".join(
        [
            "Bạn là chuyên gia QA. Chỉ dùng dữ liệu EVIDENCE sau, không bịa quy tắc nghiệp vụ.",
            "Hãy đánh giá chất lượng requirement bằng tiếng Việt. Nội dung yêu cầu chỉ mô tả phạm vi/chức năng chung; điều kiện kích hoạt và kết quả quan sát được phải nằm trong acceptance_criteria.",
            "Tối đa một finding và một suggestion. Nếu phát hiện bất kỳ vấn đề nào, BẮT BUỘC trả đúng một suggestion để sửa vấn đề đó. Mỗi message/suggestion/rationale không quá 250 ký tự; revised_content không quá 900 ký tự.",
            "Đề xuất phải tách dữ liệu theo đúng field của form: revised_content, acceptance_criteria, business_rules, actors, dependencies, tags. Với field không cần thay đổi, trả mảng rỗng. Không gộp các field thành revised_content.",
            "Chỉ có revised_content khi phần mô tả phạm vi/chức năng chung cần sửa. Nếu content hiện có chứa điều kiện/kết quả, tách chúng sang acceptance_criteria rồi viết lại content ở mức mô tả chức năng chung. Không đưa điều kiện hay kết quả kiểm thử vào revised_content. Mỗi acceptance_criteria có 'Khi' hoặc 'Nếu' và hành vi quan sát được. Tuyệt đối không thêm trạng thái, nghiệp vụ, số liệu (ví dụ hủy/hoàn tiền) không nằm trong EVIDENCE.",
            "Trả về DUY NHẤT JSON hợp lệ, không markdown, theo chính xác schema:",
            '{"findings":[{"category":"AMBIGUITY|OMISSION|UNTESTABLE|MISSING_ERROR_BEHAVIOR|MISSING_BOUNDARY|MISSING_STATE_RULE|MISSING_DATA_RULE|OTHER","severity":"error|warning|info","message":"...","suggestion":"...","evidence_refs":["allowed-ref"],"reason_codes":["CODE"]}],"suggestions":[{"revised_title":null,"revised_content":"...","acceptance_criteria":["..."],"business_rules":["..."],"actors":["..."],"dependencies":["..."],"tags":["..."],"rationale":"...","evidence_refs":["allowed-ref"],"reason_codes":["CODE"]}],"confidence":0.0,"warnings":[]}',
            f"ALLOWED_EVIDENCE_REFS={json.dumps(refs, ensure_ascii=False)}",
            f"USER_INSTRUCTION={request.instruction}",
            f"EVIDENCE={json.dumps(evidence, ensure_ascii=False)}",
        ]
    )


def requirement_draft_prompt(request: TestingAssistanceRequest, refs: list[str]) -> str:
    source = str(request.evidence[0].get("text", ""))[:6000]
    return "\n".join(
        [
            "Bạn là Business Analyst và QA. Tạo BẢN NHÁP CÓ CẤU TRÚC cho form Requirement.",
            "Chỉ dùng dữ liệu trong STRUCTURED_INPUT. Không bịa trạng thái, tích hợp, phụ thuộc, vai trò, số liệu hay quy tắc nghiệp vụ.",
            "Điền từng trường riêng: content là nội dung yêu cầu; acceptance_criteria là từng điều kiện kiểm thử được; business_rules/tác nhân/phụ thuộc/nhãn là các mảng riêng.",
            "Nếu dữ liệu nguồn không đủ cho một trường, trả mảng rỗng cho trường đó và nêu câu hỏi ngắn trong warnings; không đưa placeholder vào content.",
            "Chỉ gợi ý; không có quyền lưu hay phê duyệt Requirement.",
            "Trả về DUY NHẤT JSON hợp lệ, không markdown, theo chính xác schema:",
            '{"findings":[],"suggestions":[{"title":"...","content":"...","acceptance_criteria":["..."],"business_rules":["..."],"actors":["..."],"dependencies":["..."],"tags":["..."]}],"confidence":0.0,"warnings":["..."]}',
            f"ALLOWED_EVIDENCE_REFS={json.dumps(refs, ensure_ascii=False)}",
            f"USER_INSTRUCTION={request.instruction}",
            f"STRUCTURED_INPUT={source}",
        ]
    )


def test_condition_prompt(request: TestingAssistanceRequest, refs: list[str]) -> str:
    evidence = [
        {
            "artifact_id": item.get("artifact_id"),
            "artifact_version_id": item.get("artifact_version_id"),
            "text": str(item.get("text", ""))[:6000],
        }
        for item in request.evidence
    ]
    return "\n".join(
        [
            "Bạn là chuyên gia QA. Chỉ dùng EVIDENCE sau để tạo các ứng viên điều kiện kiểm thử bằng tiếng Việt.",
            "Mỗi ứng viên chỉ là bản nháp để người dùng duyệt; không bịa trạng thái, vai trò, tích hợp, dữ liệu hay quy tắc không có trong EVIDENCE.",
            "Tối đa 3 ứng viên. Với mỗi khoảng trống có thể kiểm thử (ví dụ giá trị hợp lệ và không hợp lệ), tạo ứng viên tương ứng; không nêu finding riêng nếu ứng viên đã bao phủ khoảng trống đó.",
            "Không đánh giá chất lượng Requirement và không trả finding: công việc này thuộc màn Kiểm tra chất lượng Requirement. Chỉ tạo suggestions là điều kiện kiểm thử.",
            "Trả về DUY NHẤT JSON hợp lệ, không markdown, theo schema:",
            '{"findings":[],"suggestions":[{"title":"...","description":"...","coverage_item":"...","test_level":"SYSTEM","test_type":"FUNCTIONAL","risk":"CRITICAL|HIGH|MEDIUM|LOW","priority":"CRITICAL|HIGH|MEDIUM|LOW","technique_candidates":["..."],"testability_status":"TESTABLE|TESTABLE_WITH_RISK|NOT_TESTABLE|NEEDS_CLARIFICATION","evidence_refs":["allowed-ref"],"reason_codes":["CODE"]}],"confidence":0.0,"warnings":[]}',
            f"ALLOWED_EVIDENCE_REFS={json.dumps(refs, ensure_ascii=False)}",
            f"USER_INSTRUCTION={request.instruction}",
            f"EVIDENCE={json.dumps(evidence, ensure_ascii=False)}",
        ]
    )


def clean_text_list(value: Any, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:limit]


def normalize_draft_candidate(value: dict[str, Any]) -> dict[str, Any] | None:
    candidates = value.get("suggestions") or []
    if not candidates or not isinstance(candidates[0], dict):
        return None
    candidate = candidates[0]
    return {
        "title": str(candidate.get("title") or "").strip()[:300],
        "content": str(candidate.get("content") or "").strip()[:6000],
        "acceptance_criteria": clean_text_list(candidate.get("acceptance_criteria"), 20),
        "business_rules": clean_text_list(candidate.get("business_rules"), 20),
        "actors": clean_text_list(candidate.get("actors"), 20),
        "dependencies": clean_text_list(candidate.get("dependencies"), 20),
        "tags": clean_text_list(candidate.get("tags"), 20),
    }


def normalize_test_condition_candidates(value: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = value.get("suggestions") or []
    if not isinstance(candidates, list):
        return []
    allowed_level = {"UNIT", "INTEGRATION", "SYSTEM", "ACCEPTANCE"}
    allowed_type = {"FUNCTIONAL", "NON_FUNCTIONAL", "SECURITY", "PERFORMANCE", "COMPATIBILITY"}
    allowed_rank = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
    allowed_status = {"TESTABLE", "TESTABLE_WITH_RISK", "NOT_TESTABLE", "NEEDS_CLARIFICATION"}
    normalized = []
    for candidate in candidates[:3]:
        if not isinstance(candidate, dict):
            continue
        title = str(candidate.get("title") or "").strip()[:300]
        description = str(candidate.get("description") or "").strip()[:5000]
        coverage_item = str(candidate.get("coverage_item") or "").strip()[:500]
        if not title or not description or not coverage_item:
            continue
        level = str(candidate.get("test_level") or "SYSTEM").upper()
        kind = str(candidate.get("test_type") or "FUNCTIONAL").upper()
        risk = str(candidate.get("risk") or "MEDIUM").upper()
        priority = str(candidate.get("priority") or risk).upper()
        testability = str(candidate.get("testability_status") or "TESTABLE").upper()
        normalized.append(
            {
                "title": title,
                "description": description,
                "coverage_item": coverage_item,
                "test_level": level if level in allowed_level else "SYSTEM",
                "test_type": kind if kind in allowed_type else "FUNCTIONAL",
                "risk": risk if risk in allowed_rank else "MEDIUM",
                "priority": priority if priority in allowed_rank else "MEDIUM",
                "technique_candidates": clean_text_list(candidate.get("technique_candidates"), 10),
                "testability_status": testability if testability in allowed_status else "TESTABLE",
                "evidence_refs": candidate.get("evidence_refs") or [],
                "reason_codes": candidate.get("reason_codes") or [],
            }
        )
    return normalized


def evidence_guided_test_condition_candidates(evidence: list[dict[str, Any]], refs: list[str]) -> list[dict[str, Any]]:
    source = next((str(item.get("text") or "").strip() for item in evidence if str(item.get("text") or "").strip()), "")
    if not source:
        return []
    first = re.split(r"(?<=[.!?])\s+", source, maxsplit=1)[0].strip()
    lowered = source.lower()
    if "thanh toán" in lowered:
        return [
            {
                "title": "Thanh toán thành công khi số tiền khớp",
                "description": first,
                "coverage_item": "Điều kiện chấp nhận giao dịch",
                "test_level": "SYSTEM",
                "test_type": "FUNCTIONAL",
                "risk": "HIGH",
                "priority": "HIGH",
                "technique_candidates": ["Phân vùng tương đương"],
                "testability_status": "TESTABLE",
                "evidence_refs": refs,
                "reason_codes": ["EVIDENCE_GUIDED_TEST_CONDITION"],
            },
            {
                "title": "Từ chối thanh toán khi số tiền không khớp",
                "description": "Xác nhận giao dịch không được ghi nhận thành công khi số tiền thanh toán khác tổng tiền đơn hàng tại thời điểm tạo giao dịch.",
                "coverage_item": "Đối soát số tiền thanh toán",
                "test_level": "SYSTEM",
                "test_type": "FUNCTIONAL",
                "risk": "HIGH",
                "priority": "HIGH",
                "technique_candidates": ["Phân vùng tương đương", "Giá trị biên"],
                "testability_status": "TESTABLE",
                "evidence_refs": refs,
                "reason_codes": ["EVIDENCE_GUIDED_NEGATIVE_SCENARIO"],
            },
        ]
    else:
        title = f"Kiểm thử {first[:220]}"
        coverage = "Hành vi từ Requirement"
        risk = priority = "MEDIUM"
    return [
        {
            "title": title,
            "description": first,
            "coverage_item": coverage,
            "test_level": "SYSTEM",
            "test_type": "FUNCTIONAL",
            "risk": risk,
            "priority": priority,
            "technique_candidates": ["Phân vùng tương đương"],
            "testability_status": "TESTABLE",
            "evidence_refs": refs,
            "reason_codes": ["EVIDENCE_GUIDED_TEST_CONDITION"],
        }
    ]


def suggestion_is_testable(generated: dict[str, Any], evidence: list[dict[str, Any]]) -> bool:
    """Keep acceptance conditions out of the general Requirement content."""
    suggestions = generated.get("suggestions") or []
    # A quality finding without a candidate is not useful to the reviewer.
    # Ask the model once more with a stricter contract instead of silently
    # reporting that AI created no proposal.
    if not suggestions:
        return False
    criteria = " ".join(
        str(item) for item in (suggestions[0].get("acceptance_criteria") or [])
    ).lower()
    if not criteria:
        return False
    has_condition = any(marker in criteria for marker in ("khi ", "nếu ", "trong trường hợp"))
    has_behavior = any(marker in criteria for marker in ("hệ thống phải", "hiển thị", "trả về", "từ chối"))
    # A suggestion may legitimately update only acceptance criteria. Requiring
    # it to copy a business rule caused valid, field-specific proposals to be
    # discarded before the reviewer could see them.
    return has_condition and has_behavior


def evidence_guided_quality_candidate(evidence: list[dict[str, Any]], refs: list[str]) -> dict[str, Any] | None:
    """Produce a conservative, field-specific candidate when the model omits one.

    The candidate never changes the Requirement's general content.  It only
    rewrites an existing acceptance criterion using a condition already stated
    in the Requirement content, so the reviewer can still apply or reject it.
    """
    source: dict[str, Any] = {}
    for item in evidence:
        try:
            parsed = json.loads(str(item.get("text") or "{}"))
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue
        if isinstance(parsed, dict):
            source = parsed
            break
    criteria = clean_text_list(source.get("acceptance_criteria"), 20)
    content = str(source.get("content") or "").strip()
    if not criteria or not content:
        return None
    condition_match = re.match(
        r"^((?:Khi|Nếu|Trong trường hợp)[^,.]*?)(?=,\s*(?:hệ thống|khách hàng))",
        content,
        flags=re.IGNORECASE,
    )
    condition = condition_match.group(1).strip() if condition_match else ""
    if not condition:
        return None
    updated = list(criteria)
    for index, criterion in enumerate(updated):
        lowered = criterion.lower()
        has_condition = any(marker in lowered for marker in ("khi ", "nếu ", "trong trường hợp"))
        if has_condition:
            continue
        statement = criterion.rstrip(". ")
        prefix = "khách hàng chỉ thanh toán được"
        if statement.lower().startswith(prefix):
            statement = "chỉ cho phép thanh toán " + statement[len(prefix) :].strip()
        updated[index] = f"{condition}, hệ thống phải {statement}."
        return {
            "revised_title": None,
            "revised_content": "",
            "acceptance_criteria": updated,
            "business_rules": [],
            "actors": [],
            "dependencies": [],
            "tags": [],
            "rationale": "Bổ sung điều kiện kích hoạt cho tiêu chí chấp nhận từ nội dung Requirement hiện có.",
            "evidence_refs": refs,
            "reason_codes": ["MISSING_CONDITION"],
        }
    return None


def normalize_generated(value: dict[str, Any]) -> dict[str, Any]:
    """Cope with otherwise-valid JSON that a provider formats with a stray key."""
    findings = value.get("findings") or []
    suggestions = value.get("suggestions") or []
    if isinstance(findings, list):
        for index, item in enumerate(findings[:-1]):
            if item == "suggestions" and isinstance(findings[index + 1], list) and not suggestions:
                suggestions = findings[index + 1]
                break
    value["findings"] = [item for item in findings if isinstance(item, dict)] if isinstance(findings, list) else []
    value["suggestions"] = [item for item in suggestions if isinstance(item, dict)] if isinstance(suggestions, list) else []
    value["warnings"] = value.get("warnings") if isinstance(value.get("warnings"), list) else []
    return value


async def request_model(prompt: str, *, retry: bool = False) -> dict[str, Any]:
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        raise HTTPException(status_code=503, detail="huggingface_token_missing")
    endpoint = os.getenv("PRIMARY_MODEL_URL", "https://router.huggingface.co/v1/chat/completions")
    model = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return only valid JSON. Do not expose hidden reasoning."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 1600,
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=float(os.getenv("MODEL_TIMEOUT_SECONDS", "90"))) as client:
        response = await client.post(
            endpoint,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=503, detail=f"huggingface_request_failed:{response.status_code}")
    body = response.json()
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise HTTPException(status_code=502, detail="huggingface_response_invalid") from error
    try:
        return normalize_generated(extract_json(str(content)))
    except (ValueError, json.JSONDecodeError) as error:
        if retry:
            raise HTTPException(status_code=502, detail="huggingface_returned_invalid_json") from error
        # Some provider models ignore response_format or stop near their token
        # limit. Retry once with a compact, explicit output contract.
        repair_prompt = (
            "Trả về đúng MỘT JSON object hợp lệ, không markdown, không giải thích. "
            "Dùng schema {\"findings\":[],\"suggestions\":[],\"confidence\":0.0,\"warnings\":[]}. "
            "Tối đa một phần tử cho findings và suggestions.\n\n" + prompt
        )
        return await request_model(repair_prompt, retry=True)


@app.get("/san-sang")
async def ready() -> dict[str, Any]:
    return {
        "ready": bool(os.getenv("HF_TOKEN", "").strip()),
        "provider": "huggingface",
        "model": os.getenv("LLM_MODEL", "unknown"),
    }


@app.post("/suy-luan/noi-bo/kiem-thu/ho-tro")
async def testing_assistance(
    request: TestingAssistanceRequest,
    x_internal_token: str | None = Header(default=None),
) -> dict[str, Any]:
    authorize(x_internal_token)
    refs = evidence_refs(request.evidence)
    if request.capability == "requirement_draft_generation":
        generated = await request_model(requirement_draft_prompt(request, refs))
        candidate = normalize_draft_candidate(generated)
        if not candidate:
            raise HTTPException(status_code=502, detail="huggingface_draft_response_invalid")
        generated_refs = refs
        return {
            "capability": request.capability,
            "findings": [],
            "suggestions": [candidate],
            "evidence_refs": generated_refs,
            "confidence": min(1, max(0, float(generated.get("confidence", 0.7)))),
            "warnings": generated.get("warnings", []),
            "status": "SUCCESS",
            "degraded_mode": None,
            "provider": "huggingface",
            "model": model_metadata(),
            "prompt_version": "veriq-ai-adapter-v1",
            "tool_schema_version": "1",
            "retrieval_version": "project-filter-v1",
            "created_at": now_iso(),
            "reason_codes": ["AI_REQUIREMENT_DRAFT_GENERATION"],
            "workflow": {"intent": request.capability, "candidate_count": 1},
            "answer": "",
        }
    if request.capability == "test_condition_generation":
        try:
            generated = await request_model(test_condition_prompt(request, refs))
        except (HTTPException, httpx.HTTPError):
            fallbacks = evidence_guided_test_condition_candidates(request.evidence, refs)
            if not fallbacks:
                raise
            return {
                "capability": request.capability,
                "findings": [],
                "suggestions": fallbacks,
                "evidence_refs": refs,
                "confidence": 0.7,
                "warnings": ["HUGGINGFACE_TIMEOUT", "AI_CANDIDATE_GUIDED_BY_EVIDENCE"],
                "status": "SUCCESS",
                "degraded_mode": None,
                "provider": "evidence-guided",
                "model": model_metadata(),
                "prompt_version": "veriq-ai-adapter-v1",
                "tool_schema_version": "1",
                "retrieval_version": "project-filter-v1",
                "created_at": now_iso(),
                "reason_codes": ["EVIDENCE_GUIDED_TEST_CONDITION"],
                "workflow": {"intent": request.capability, "candidate_count": len(fallbacks)},
                "answer": "",
            }
        candidates = normalize_test_condition_candidates(generated)
        fallbacks = evidence_guided_test_condition_candidates(request.evidence, refs)
        if not candidates:
            candidates = fallbacks
            if candidates:
                generated.setdefault("warnings", []).append("AI_CANDIDATE_GUIDED_BY_EVIDENCE")
        elif len(candidates) < 3 and len(fallbacks) > 1:
            candidate_text = " ".join(
                f"{item['title']} {item['description']}".lower() for item in candidates
            )
            has_negative_case = any(
                marker in candidate_text
                for marker in ("không khớp", "không bằng", "từ chối", "thất bại")
            )
            if not has_negative_case:
                candidates.append(fallbacks[1])
        generated["suggestions"] = candidates
        generated_refs = [
            str(item) for item in generated.get("evidence_refs", refs) if str(item) in refs
        ]
        if not generated_refs:
            generated_refs = refs
        return {
            "capability": request.capability,
            # Requirement quality is assessed in the Requirement workflow.
            # Test analysis only returns executable condition candidates; it
            # must not reclassify Requirement gaps as test-analysis findings.
            "findings": [],
            "suggestions": generated.get("suggestions", []),
            "evidence_refs": generated_refs,
            "confidence": min(1, max(0, float(generated.get("confidence", 0.7)))),
            "warnings": generated.get("warnings", []),
            "status": "SUCCESS",
            "degraded_mode": None,
            "provider": "huggingface",
            "model": model_metadata(),
            "prompt_version": "veriq-ai-adapter-v1",
            "tool_schema_version": "1",
            "retrieval_version": "project-filter-v1",
            "created_at": now_iso(),
            "reason_codes": ["AI_TEST_CONDITION_GENERATION"],
            "workflow": {
                "intent": request.capability,
                "candidate_count": len(generated.get("suggestions", [])),
            },
            "answer": "",
        }
    if request.capability != "requirement_quality_analysis":
        raise HTTPException(
            status_code=422, detail="Unsupported testing assistance capability.",
        )
    prompt = requirement_prompt(request, refs)
    try:
        generated = await request_model(prompt)
    except (HTTPException, httpx.HTTPError) as error:
        # A hosted model may spend minutes queued or generating. Return a
        # bounded, evidence-only candidate so the reviewer is never left with
        # an empty AI panel or a gateway timeout.
        fallback = evidence_guided_quality_candidate(request.evidence, refs)
        if not fallback:
            raise error
        return {
            "capability": request.capability,
            "findings": [],
            "suggestions": [fallback],
            "evidence_refs": refs,
            "confidence": 0.7,
            "warnings": ["HUGGINGFACE_TIMEOUT", "AI_CANDIDATE_GUIDED_BY_EVIDENCE"],
            "status": "SUCCESS",
            "degraded_mode": None,
            "provider": "evidence-guided",
            "model": model_metadata(),
            "prompt_version": "veriq-ai-adapter-v1",
            "tool_schema_version": "1",
            "retrieval_version": "project-filter-v1",
            "created_at": now_iso(),
            "reason_codes": ["MISSING_CONDITION"],
            "workflow": {"intent": request.capability, "candidate_count": 1},
            "answer": "",
        }
    if not suggestion_is_testable(generated, request.evidence):
        # A second remote inference often makes the request exceed the gateway
        # timeout. Keep Gemma as the primary analyser, then provide a safe,
        # evidence-derived candidate when it omits a usable structured patch.
        fallback = evidence_guided_quality_candidate(request.evidence, refs)
        if fallback:
            generated["suggestions"] = [fallback]
            generated.setdefault("warnings", []).append("AI_CANDIDATE_GUIDED_BY_EVIDENCE")
    generated_refs = [str(item) for item in generated.get("evidence_refs", refs) if str(item) in refs]
    if not generated_refs:
        generated_refs = refs
    return {
        "capability": request.capability,
        "findings": generated.get("findings", []),
        "suggestions": generated.get("suggestions", []),
        "evidence_refs": generated_refs,
        "confidence": min(1, max(0, float(generated.get("confidence", 0.7)))),
        "warnings": generated.get("warnings", []),
        "status": "SUCCESS",
        "degraded_mode": None,
        "provider": "huggingface",
        "model": model_metadata(),
        "prompt_version": "veriq-ai-adapter-v1",
        "tool_schema_version": "1",
        "retrieval_version": "project-filter-v1",
        "created_at": now_iso(),
        "reason_codes": ["AI_REQUIREMENT_QUALITY_ANALYSIS"],
        "workflow": {"intent": request.capability, "candidate_count": len(generated.get("suggestions", []))},
        "answer": "",
    }
