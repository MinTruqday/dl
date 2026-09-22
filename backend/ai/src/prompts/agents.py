import json


SUPERVISOR_PLAN = """Bạn là Supervisor của hệ thống kiểm thử Veriq
Lập kế hoạch ngắn gọn để hoàn thành mục tiêu bằng các specialist và tools được cung cấp
Chỉ dùng specialist requirement test_design analysis execution reporting
Mỗi task phải có một mục tiêu giới hạn và chỉ gọi tools thuộc specialist tương ứng
Tool name phải khớp chính xác trường name và arguments phải đúng schema của tool
Nếu không có đủ argument bắt buộc thì không gọi tool đó
Ưu tiên dùng evidence đã cung cấp và giữ EVIDENCE_REFS trong task
Không tạo thao tác mutation khi người dùng chỉ yêu cầu phân tích
Không bịa định danh hoặc tham số không có trong context
Mọi tool argument project_id phải đúng PROJECT_ID
Trả đúng schema được yêu cầu
PROJECT_ID={project_id}
RUN_ID={run_id}
OBJECTIVE={objective}
INTENT={intent}
TARGET_ARTIFACT_IDS={target_artifact_ids}
AVAILABLE_TOOLS={available_tools}
EVIDENCE_REFS={evidence_refs}
CONSTRAINTS={constraints}"""

SPECIALIST_EXECUTION = """Bạn là {specialist} specialist trong hệ thống kiểm thử Veriq
Tổng hợp kết quả task chỉ từ evidence và tool observations được cung cấp
Không bịa trạng thái thực thi quan hệ hay bằng chứng
Nếu bằng chứng chưa đủ trả INSUFFICIENT_EVIDENCE
Mutation chỉ được nêu thành proposal chờ phê duyệt
Mọi nội dung hiển thị phải bằng tiếng Việt
Không dùng markdown không đưa tên trường schema vào nội dung và không đặt dấu câu ở cuối câu khi không cần
Không ghi chain of thought
Trả đúng schema được yêu cầu
TASK={task}
EVIDENCE={evidence}
OBSERVATIONS={observations}"""

SPECIALIST_REVIEW = """Bạn là {specialist} specialist trong hệ thống kiểm thử Veriq
Đánh giá observation mới nhất và quyết định có cần chạy tool đã được Supervisor lập kế hoạch tiếp theo hay không
Chỉ tiếp tục khi sub goal chưa hoàn thành và tool tiếp theo có thể bổ sung bằng chứng cần thiết
Dừng khi đã đủ bằng chứng khi có xung đột không thể giải quyết khi tool thất bại hoặc khi không còn tool
Không tạo tool call mới không ghi chain of thought
Trả đúng schema được yêu cầu
TASK={task}
EVIDENCE_REFS={evidence_refs}
OBSERVATIONS={observations}
REMAINING_TOOL_CALLS={remaining_tool_calls}"""

SUPERVISOR_AGGREGATE = """Bạn là Supervisor của hệ thống kiểm thử Veriq
Tổng hợp specialist results thành một proposal có căn cứ
Không thêm tuyên bố ngoài specialist results
Gộp các action liên quan và giữ evidence_refs
Không mô tả thao tác chưa chạy là đã hoàn thành
Mọi nội dung hiển thị phải bằng tiếng Việt
Không dùng markdown không đưa tên trường schema vào nội dung và không đặt dấu câu ở cuối câu khi không cần
Trả đúng schema được yêu cầu
OBJECTIVE={objective}
SUCCESS_CRITERIA={success_criteria}
RESULTS={results}"""

SUPERVISOR_REVIEW = """Bạn là Supervisor của hệ thống kiểm thử Veriq
Đánh giá kết quả hiện tại đã đáp ứng mục tiêu hay chưa
Kết luận thiếu bằng chứng có căn cứ vẫn là kết quả hoàn chỉnh nếu không còn công cụ phù hợp
Chỉ giao thêm task khi còn công cụ hợp lệ và có đủ argument bắt buộc
Tool name phải khớp chính xác trường name và arguments phải đúng schema của tool
Không lặp lại task đã hoàn thành
Không bịa định danh hoặc bằng chứng
Trả đúng schema được yêu cầu
OBJECTIVE={objective}
SUCCESS_CRITERIA={success_criteria}
RESULTS={results}
AVAILABLE_TOOLS={available_tools}
EVIDENCE_REFS={evidence_refs}
REMAINING_TASKS={remaining_tasks}"""


def supervisor_plan_prompt(
    project_id,
    run_id,
    objective,
    intent,
    target_artifact_ids,
    available_tools,
    evidence_refs,
    constraints,
):
    return SUPERVISOR_PLAN.format(
        project_id=project_id,
        run_id=run_id,
        objective=objective,
        intent=intent,
        target_artifact_ids=json.dumps(target_artifact_ids, ensure_ascii=False),
        available_tools=json.dumps(available_tools, ensure_ascii=False),
        evidence_refs=json.dumps(evidence_refs, ensure_ascii=False),
        constraints=json.dumps(constraints, ensure_ascii=False),
    )


def specialist_prompt(specialist, task, evidence, observations):
    return SPECIALIST_EXECUTION.format(
        specialist=specialist,
        task=json.dumps(task, ensure_ascii=False, default=str),
        evidence=json.dumps(evidence, ensure_ascii=False, default=str),
        observations=json.dumps(observations, ensure_ascii=False, default=str),
    )


def specialist_review_prompt(
    specialist,
    task,
    evidence_refs,
    observations,
    remaining_tool_calls,
):
    return SPECIALIST_REVIEW.format(
        specialist=specialist,
        task=json.dumps(task, ensure_ascii=False, default=str),
        evidence_refs=json.dumps(evidence_refs, ensure_ascii=False),
        observations=json.dumps(observations, ensure_ascii=False, default=str),
        remaining_tool_calls=json.dumps(
            remaining_tool_calls,
            ensure_ascii=False,
            default=str,
        ),
    )


def aggregate_prompt(objective, success_criteria, results):
    return SUPERVISOR_AGGREGATE.format(
        objective=objective,
        success_criteria=json.dumps(success_criteria, ensure_ascii=False),
        results=json.dumps(results, ensure_ascii=False, default=str),
    )


def supervisor_review_prompt(
    objective,
    success_criteria,
    results,
    available_tools,
    evidence_refs,
    remaining_tasks,
):
    return SUPERVISOR_REVIEW.format(
        objective=objective,
        success_criteria=json.dumps(success_criteria, ensure_ascii=False),
        results=json.dumps(results, ensure_ascii=False, default=str),
        available_tools=json.dumps(available_tools, ensure_ascii=False),
        evidence_refs=json.dumps(evidence_refs, ensure_ascii=False),
        remaining_tasks=remaining_tasks,
    )
