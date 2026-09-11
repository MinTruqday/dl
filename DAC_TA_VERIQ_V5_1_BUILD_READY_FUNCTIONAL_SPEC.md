# VERIQ V5.1 — BUILD-READY FUNCTIONAL SPECIFICATION
## Làm rõ chức năng trước khi build theo Test Process quốc tế, kế thừa V5 và implementation hiện tại

**Tài liệu:** V5.1 Functional Build Contract  
**Ngày:** 12/09/2026  
**Repository:** `MinTruqday/dl`  
**Source-audit baseline của V5:** commit `484a56d571142010bff3b7afdea7b17ce60ae823` (`562 commit`)  
**Repository HEAD quan sát sau đó:** commit `3b3f506a9cc2198268b1cbaa452922d6c5fd18f1` (`564 commit`)  
**Mục đích:** chuyển các gap của V5 thành đặc tả đủ chi tiết để dev build trực tiếp  
**Quan hệ với V5:** V5.1 không đổi định hướng V5; V5.1 thay thế V5 về chi tiết triển khai chức năng mới/được mở rộng.  
**Không thay thế:** các Function ID/contract hiện hữu của Requirement, TestCase, Traceability, Execution, Defect, Change/Impact, Automation nếu chúng đã tồn tại và hoạt động đúng.

---

# 0. QUY TẮC DÙNG TÀI LIỆU

## 0.1. V5.1 giải quyết vấn đề gì?

V5 đã trả lời:

```text
Dự án còn thiếu process-area nào?
Tại sao cần?
Nên build module nào?
```

Nhưng trước khi code cần thêm:

```text
Module đó có những chức năng nào?
Từng chức năng có sub-feature nào?
Ai được dùng?
Dữ liệu nào được tạo?
State chuyển thế nào?
API nào gọi?
Màn hình nào hiển thị?
Validation gì?
Error code gì?
Audit gì?
Idempotency/concurrency xử lý ra sao?
Acceptance test nào chứng minh build đúng?
```

V5.1 trả lời các câu hỏi trên.

## 0.2. Trạng thái implementation dùng trong V5.1

| Trạng thái | Ý nghĩa |
|---|---|
| `IMPLEMENTED` | Đã được source audit xác nhận hoặc contract hiện tại đã rõ |
| `README_IMPLEMENTED` | README hiện tại báo đã hoàn thiện; phải chạy test/runtime verification trước khi đóng |
| `PARTIAL` | Đã có nền nhưng chưa đủ process contract |
| `TO_BUILD_P0` | Cần build trước khi coi lifecycle chính hoàn chỉnh |
| `TO_BUILD_P1` | Nên build sau P0 để đạt maturity tốt hơn |
| `TO_BUILD_P2` | Research/optimization extension, không block đồ án |
| `OUT_OF_SCOPE` | Không build để tránh project phình thành enterprise suite khác |

## 0.3. Không tạo chức năng trùng

Nếu repo đã có chức năng tương đương thì:

```text
KHÔNG:
tạo entity/API/UI thứ hai chỉ vì V5.1 dùng tên khác.

ĐÚNG:
map implementation hiện tại → contract V5.1
→ bổ sung field/state/rule còn thiếu
→ migration nếu cần
→ giữ backward compatibility khi hợp lý.
```

Ví dụ Quality Gate hiện tại đã có quyết định:

```text
Phê duyệt
Chặn phát hành
Chấp nhận rủi ro
```

V5.1 **không tạo một Quality Gate khác**.

V5.1 tách rõ:

```text
QualityGateEvaluation
= hệ thống tính deterministic

QualityDecision
= QA Lead ra quyết định có lý do

ProductQualityEvaluation
= artifact tổng hợp cấp release, P1
```

---

# 1. BASELINE CHỨC NĂNG HIỆN TẠI — KHÔNG BUILD LẠI

## 1.1. AI Requirement Assistance — README_IMPLEMENTED

README hiện tại mô tả:

```text
AI Requirement Quality Check
AI Revision Suggestion
Apply selected AI suggestion
Generate Test Scenario/Test Case draft
Human approves Requirement
```

V5.1 chỉ yêu cầu hardening:

```text
AI suggestion phải có evidence/reason code.
Apply vào DRAFT, không mutate APPROVED version.
Apply phải audit.
AI provider unavailable không được phá manual editing.
```

## 1.2. Execution Improvement — README_IMPLEMENTED

Giữ:

```text
Create TestRun from selected exact TestCaseVersions
Retest Defect only linked test scope
Fail step → Save Fail + Create Defect
Prefill execution/build/environment/expected result
```

Không build một retest engine khác.

## 1.3. Defect Evidence — README_IMPLEMENTED

Giữ policy:

```text
QA Lead → project-wide evidence
Tester → own-created defect / own-executed result evidence
Developer → assigned-defect evidence
BA → evidence for requirement-linked defect
Viewer → no defect evidence by default
```

V5.1 chỉ yêu cầu permission integration test và audit download/view.

## 1.4. QA Lead Quality Dashboard/Gate — README_IMPLEMENTED / PARTIAL

Hiện có:
- release quality status;
- pass/fail/blocked/open defect indicators;
- pending work;
- quality decision history;
- approve/block/accept-risk;
- mandatory reason for accepted risk;
- audit.

V5.1 xem đây là **foundation** cho:
- Test Monitoring & Control;
- Quality Gate Evaluation;
- Status Reporting;
- Product Quality Evaluation.

Không xóa.

---

# 2. PRODUCT POSITIONING SAU V5.1

Veriq không phải chỉ là bug tracker hay TestCase repository.

Canonical product statement:

> **Veriq là nền tảng quản lý và soạn thảo tài liệu kiểm thử có cấu trúc, hỗ trợ vòng đời kiểm thử từ Test Basis/Requirement, Test Analysis, Test Design, Planning, Execution, Defect, Monitoring, Completion đến bảo trì Test Case khi Requirement thay đổi; AI đóng vai trò trợ lý phân tích và đề xuất, còn quyết định chất lượng quan trọng thuộc con người.**

Canonical lifecycle:

```text
Project
→ Test Strategy
→ Requirement/Test Basis
→ Test Analysis
→ Test Condition
→ Test Scenario
→ Test Case
→ Traceability
→ Test Plan
→ Release/Build/Environment
→ Test Suite
→ Test Run
→ Test Result
→ Defect/Retest
→ Monitoring Snapshot
→ Quality Gate Evaluation
→ Quality Decision
→ Status Report
→ Requirement Change
→ Impact Analysis
→ AI Maintenance Proposal
→ Human Approval
→ Regression
→ Completion Report
→ Release Close
→ Lessons Learned / RCA / Improvement
```

---

# 3. BUILD CONTRACT CHUNG

Mỗi chức năng mới phải map đủ:

```text
Function ID
Module
Business objective
Actor/Role
Permission key
Precondition
Input
Validation
Entity read/write
State transition
API
Frontend action
Audit event
Idempotency
Optimistic concurrency
Error codes
Acceptance tests
```

## 3.1. API envelope

Giữ convention hiện tại:

```json
{
  "data": {},
  "meta": {
    "trace_id": "..."
  }
}
```

Error:

```json
{
  "error": {
    "code": "CANONICAL_ERROR_CODE",
    "message": "...",
    "details": {}
  },
  "trace_id": "..."
}
```

## 3.2. Mutation rules

Mutation quan trọng phải có ít nhất một trong:

```text
expected_revision
idempotency_key
immutable version creation
```

Không silent last-write-wins.

## 3.3. Audit rules

Bắt buộc audit:
- approval;
- rejection;
- override;
- accept risk;
- quality decision;
- completion close;
- RCA approval;
- strategy approval;
- release gate;
- cross-role assignment;
- privileged evidence access.

---

# 4. P0-A — DOMAIN CLEANUP

**Status:** `TO_BUILD_P0`

## 4.1. Mục tiêu

Xóa vocabulary education còn sót khỏi bounded context `testing`.

### Loại bỏ

```text
teacher_material
official_textbook
curriculum
teacher_id
subject
grade
```

### Thay bằng

```text
SRS
BRD
USER_STORY
ACCEPTANCE_CRITERIA
BUSINESS_RULE
API_SPEC
UI_SPEC
ARCHITECTURE
MEETING_NOTE
RELEASE_NOTE
BUG_HISTORY
TEST_ARTIFACT
REGULATION
REFERENCE
OTHER
```

Authority:

```text
APPROVED_SOURCE
CONTROLLED_SOURCE
PROJECT_REFERENCE
SUPPLEMENTAL
DRAFT
UNVERIFIED
```

## 4.2. Entity metadata mới

```text
source_type
authority
owner_id
module
component
product_area
release_id
external_source_id
source_version
approval_status
approved_by
approved_at
effective_from
tags[]
```

## 4.3. Function register

| ID | Function | Role | Permission | Priority |
|---|---|---|---|---|
| CLN-01 | Scan legacy metadata | QA Lead/Admin migration | internal | P0 |
| CLN-02 | Map legacy source type | system migration | internal | P0 |
| CLN-03 | Map legacy authority | system migration | internal | P0 |
| CLN-04 | Migrate metadata | system migration | internal | P0 |
| CLN-05 | Reindex project knowledge | QA Lead/system | `knowledge.manage` | P0 |
| CLN-06 | Validate migrated references | system | internal | P0 |
| CLN-07 | Remove legacy API fields | system | internal | P0 |
| CLN-08 | Remove legacy frontend fields | system | internal | P0 |

## 4.4. Build location

```text
backend/testing/src/domain/schemas.py
backend/testing/src/api/requirements.py
backend/testing/src/api/analytics.py
backend/testing/src/services/project_knowledge.py
backend/testing/src/core/database.py
frontend/features/testing/pages/workspace/RequirementsPage.jsx
frontend/features/testing/pages/workspace/KnowledgePage.jsx
scripts/migrate_testing_knowledge_metadata_v51.py
```

## 4.5. Error/validation

```text
LEGACY_METADATA_UNMAPPED
SOURCE_TYPE_INVALID
AUTHORITY_INVALID
KNOWLEDGE_REINDEX_FAILED
MIGRATION_REFERENCE_BROKEN
```

## 4.6. Acceptance

```text
AC-CLN-01 Không còn teacher_* field trong Testing OpenAPI.
AC-CLN-02 Existing documents không mất content/provenance.
AC-CLN-03 Project search vẫn tìm được source cũ sau migration.
AC-CLN-04 RAG filter vẫn project-scoped.
AC-CLN-05 Approved source được rank cao hơn draft.
AC-CLN-06 Migration chạy lại không tạo duplicate.
```

---

# 5. P0-B — TEST STRATEGY

**Status:** `TO_BUILD_P0`

## 5.1. Business objective

TestPlan trả lời:

```text
Lần test này làm gì?
```

TestStrategy trả lời:

```text
Project này kiểm thử theo nguyên tắc nào?
```

Không dùng `Project.settings` làm TestStrategy.

## 5.2. Entity: TestStrategy

```text
_id
project_id
strategy_key
name
version
status
objective
context_doc
test_levels[]
test_types[]
approach
risk_model
technique_policy
automation_policy
environment_policy
test_data_policy
defect_policy
review_policy
entry_criteria_defaults[]
exit_criteria_defaults[]
suspension_criteria[]
resumption_criteria[]
deliverables[]
reporting_policy
quality_objectives[]
standards_refs[]
tailoring_rationale
parent_strategy_id
parent_version_id
revision
created_by
created_at
updated_by
updated_at
submitted_by
submitted_at
approved_by
approved_at
archive_reason
```

## 5.3. Test levels

```text
COMPONENT
INTEGRATION
SYSTEM
SYSTEM_INTEGRATION
ACCEPTANCE
CUSTOM
```

Không bắt buộc project dùng tất cả.

## 5.4. Test types

```text
FUNCTIONAL
API
UI
REGRESSION
SMOKE
SANITY
SECURITY
PERFORMANCE
USABILITY
COMPATIBILITY
ACCESSIBILITY
RECOVERY
INSTALLATION
DATA
LOCALIZATION
CUSTOM
```

## 5.5. Risk model

```text
probability_scale
impact_scale
calculation_method
risk_levels
thresholds
mandatory_depth_by_level
regression_rule
```

Default formula:

```text
risk_exposure = probability * impact
```

Cho phép project customize mapping nhưng không custom executable code.

## 5.6. Strategy states

```text
DRAFT
→ IN_REVIEW
→ APPROVED
→ SUPERSEDED
→ ARCHIVED

IN_REVIEW
→ DRAFT        request changes
```

Rules:

```text
APPROVED immutable.
Approve v2 → v1 SUPERSEDED.
Project có tối đa một current APPROVED strategy.
ARCHIVED strategy không bind vào TestPlan mới.
Plan cũ vẫn đọc được exact strategy version.
```

## 5.7. Function register

| ID | Function | Default role | Permission | API |
|---|---|---|---|---|
| STR-01 | List strategies | all project roles | `teststrategy.read` | GET project strategies |
| STR-02 | View strategy | all project roles | `teststrategy.read` | GET strategy |
| STR-03 | Create draft | QA Lead/Tester | `teststrategy.create` | POST |
| STR-04 | Edit draft | QA Lead/Tester | `teststrategy.update` | PATCH |
| STR-05 | Submit review | QA Lead/Tester | `teststrategy.submit_review` | POST |
| STR-06 | Review | QA Lead/Tester/BA | `teststrategy.review` | POST/comment |
| STR-07 | Request changes | QA Lead | `teststrategy.review` | POST |
| STR-08 | Approve | QA Lead | `teststrategy.approve` | POST |
| STR-09 | Create new version | QA Lead | `teststrategy.version.create` | POST |
| STR-10 | Compare versions | all project roles | `teststrategy.version.read` | GET/POST compare |
| STR-11 | Archive | QA Lead | `teststrategy.archive` | POST |
| STR-12 | Set project current | system on approval | internal | internal |
| STR-13 | Clone from previous project strategy | QA Lead | `teststrategy.create` | POST clone |
| STR-14 | Validate strategy completeness | QA Lead/Tester | `teststrategy.review` | POST validate |

## 5.8. STR-14 completeness rules

At minimum:

```text
objective non-empty
>= 1 test level
>= 1 test type
risk model configured
entry criteria defaults exist
exit criteria defaults exist
suspension/resumption configured
reporting cadence configured
quality objectives exist
```

Result:

```json
{
  "ready_for_review": false,
  "findings": [
    {
      "code": "STRATEGY_EXIT_CRITERIA_MISSING",
      "severity": "MAJOR"
    }
  ]
}
```

## 5.9. UI

New area:

```text
Planning & Execution
└── Test Strategy
```

Components:

```text
StrategyList
StrategyEditor
StrategyOverview
RiskModelEditor
EntryExitCriteriaEditor
AutomationPolicyEditor
StrategyReviewPanel
StrategyVersionHistory
StrategyDiff
```

## 5.10. Backend

```text
backend/testing/src/api/test_strategy.py
backend/testing/src/services/test_strategy_service.py
backend/testing/src/repositories/test_strategy_repository.py
backend/testing/src/domain/test_strategy.py
```

## 5.11. Errors

```text
TEST_STRATEGY_NOT_FOUND
TEST_STRATEGY_NOT_DRAFT
TEST_STRATEGY_INCOMPLETE
TEST_STRATEGY_ALREADY_APPROVED
TEST_STRATEGY_STALE_REVISION
TEST_STRATEGY_ACTIVE_CONFLICT
TEST_STRATEGY_ARCHIVED
INVALID_RISK_MODEL
INVALID_STATE_TRANSITION
```

## 5.12. Acceptance tests

```text
AC-STR-01 Tester tạo draft được.
AC-STR-02 Tester không approve.
AC-STR-03 BA review được nhưng mặc định không approve.
AC-STR-04 Viewer chỉ read.
AC-STR-05 System Admin không membership không đọc artifact.
AC-STR-06 Approve strategy incomplete bị 409.
AC-STR-07 Approved strategy PATCH bị 409.
AC-STR-08 New version giữ parent version.
AC-STR-09 Approve v2 supersede v1.
AC-STR-10 Plan bind v1 vẫn đọc được sau v2.
AC-STR-11 Concurrent PATCH stale revision bị 409.
AC-STR-12 Audit create/update/submit/approve/archive.
```

---

# 6. P0-C — TEST PLAN EXTENSION

**Status:** `PARTIAL → EXTEND P0`

## 6.1. Giữ nguyên field đang có

```text
name
objective
scope_in
scope_out
environment
environment_id
entry_criteria
exit_criteria
risks
test_types
members
release
release_id
build
build_id
```

## 6.2. Bổ sung field

```text
strategy_id
strategy_version
strategy_snapshot_hash

test_level

assumptions[]
constraints[]
dependencies[]
stakeholders[]

responsibility_matrix[]

estimation {
  method
  planned_effort_hours
  planned_people
  basis
}

schedule {
  planned_start_at
  planned_end_at
}

milestones[]

deliverables[]
tools[]

suspension_criteria[]
resumption_criteria[]

monitoring_metrics[]
quality_targets[]

risk_register[]

communication_plan {
  status_report_frequency
  recipients[]
  escalation_roles[]
}

approved_snapshot_hash
```

## 6.3. RiskRegisterItem

```text
risk_id
title
description
probability
impact
exposure
response
owner_id
status
due_at
```

State:

```text
OPEN
MITIGATING
ACCEPTED
CLOSED
```

## 6.4. ResponsibilityMatrixItem

```text
activity
responsible_user_ids[]
accountable_user_id
consulted_user_ids[]
informed_user_ids[]
```

## 6.5. Milestone

```text
name
planned_at
actual_at
status
evidence_refs[]
```

## 6.6. Function additions

| ID | Function | Role | Permission |
|---|---|---|---|
| PLN-21 | Bind StrategyVersion | QA Lead/Tester draft | `testplan.update` |
| PLN-22 | Manage estimation | QA Lead/Tester | `testplan.update` |
| PLN-23 | Manage schedule | QA Lead/Tester | `testplan.update` |
| PLN-24 | Manage RACI | QA Lead/Tester policy | `testplan.update` |
| PLN-25 | Manage suspension criteria | QA Lead/Tester | `testplan.update` |
| PLN-26 | Manage resumption criteria | QA Lead/Tester | `testplan.update` |
| PLN-27 | Manage quality targets | QA Lead/Tester | `testplan.update` |
| PLN-28 | Manage monitoring metric selection | QA Lead/Tester | `testplan.update` |
| PLN-29 | Manage risk register | QA Lead/Tester | `testplan.update` |
| PLN-30 | Validate plan completeness | QA Lead/Tester | `testplan.review` |
| PLN-31 | Freeze approval snapshot | system | internal |
| PLN-32 | Compare plan vs actual | QA Lead/Tester | `testmonitor.read` |

## 6.7. Approval validation

TestPlan không được approve nếu policy bật `strict_test_plan_approval` và thiếu:

```text
approved TestStrategy binding
objective
scope_in
entry criteria
exit criteria
test type
release/environment when required
schedule
quality targets
```

## 6.8. Không làm

Không cần:
- financial cost accounting;
- timesheet;
- HR capacity management;
- enterprise portfolio planning.

---

# 7. P0-D — TEST ANALYSIS & TEST CONDITION

**Status:** `TO_BUILD_P0`

## 7.1. Tại sao TestScenario chưa đủ?

Canonical:

```text
Test Basis → Test Condition → Test Scenario → Test Case
```

`TestCondition` là **what to test**.
`TestScenario` là **high-level situation/flow**.
`TestCase` là **how to test with data/expected result**.

## 7.2. Entity: TestCondition

```text
_id
project_id
condition_key
title
description_doc
basis_refs[]
coverage_item
test_level
test_type
risk
priority
technique_candidates[]
testability_status
analysis_finding_ids[]
status
origin
revision
created_by
created_at
updated_by
updated_at
submitted_by
approved_by
approved_at
archived_at
```

## 7.3. BasisRef

```text
artifact_type:
  requirement_version
  acceptance_criterion
  business_rule
  api_operation
  knowledge_source
  defect
  risk_item
  regulation

artifact_id
artifact_version_id
relationship
source_span
```

## 7.4. Testability status

```text
TESTABLE
TESTABLE_WITH_RISK
NOT_TESTABLE
NEEDS_CLARIFICATION
```

## 7.5. AnalysisFinding

```text
_id
project_id
artifact_type
artifact_id
artifact_version_id
category
severity
title
description
source_span
suggestion
status
owner_id
resolution
resolution_ref
created_by
resolved_by
timestamps
```

Category:

```text
AMBIGUITY
OMISSION
INCONSISTENCY
CONTRADICTION
UNTESTABLE
MISSING_ACCEPTANCE_CRITERIA
MISSING_ERROR_BEHAVIOR
MISSING_PERMISSION_RULE
MISSING_BOUNDARY
MISSING_STATE_RULE
MISSING_DATA_RULE
MISSING_NON_FUNCTIONAL_CRITERIA
DUPLICATE
OTHER
```

Severity:

```text
BLOCKER
MAJOR
MINOR
INFO
```

Finding state:

```text
OPEN
→ IN_PROGRESS
→ RESOLVED
→ VERIFIED

OPEN
→ ACCEPTED_RISK
```

## 7.6. TestCondition state

```text
DRAFT
→ IN_REVIEW
→ APPROVED
→ ARCHIVED

IN_REVIEW
→ DRAFT
```

Project setting:

```text
require_condition_approval_before_testcase = true|false
```

Nếu false:
- DRAFT/IN_REVIEW condition vẫn có thể dùng;
- UI warning.

Nếu true:
- TestCase official submit phải trace APPROVED condition.

## 7.7. Function register

| ID | Function | Default role | Permission |
|---|---|---|---|
| TAN-01 | Open Test Analysis workspace | QA Lead/Tester/BA | `testanalysis.read` |
| TAN-02 | Select Test Basis | QA Lead/Tester/BA | `testanalysis.read` |
| TAN-03 | Run deterministic testability checks | QA Lead/Tester/BA | `testanalysis.execute` |
| TAN-04 | Run AI testability analysis | QA Lead/Tester/BA | `testanalysis.run_ai` |
| TAN-05 | Create analysis finding | QA Lead/Tester/BA | `testanalysis.finding.create` |
| TAN-06 | Assign finding | QA Lead | `testanalysis.finding.assign` |
| TAN-07 | Resolve finding | owner/QA Lead/BA by policy | `testanalysis.resolve_finding` |
| TAN-08 | Verify resolution | QA Lead/Tester/BA | `testanalysis.verify_finding` |
| TCN-01 | List Test Conditions | all read roles | `testcondition.read` |
| TCN-02 | Create Test Condition | QA Lead/Tester | `testcondition.create` |
| TCN-03 | Edit Test Condition | QA Lead/Tester | `testcondition.update` |
| TCN-04 | Generate conditions by AI | QA Lead/Tester | `ai.generate_testcondition` |
| TCN-05 | Suggest techniques | QA Lead/Tester | `ai.suggest_test_technique` |
| TCN-06 | Submit condition review | QA Lead/Tester | `testcondition.submit_review` |
| TCN-07 | Review condition | QA Lead/Tester/BA | `testcondition.review` |
| TCN-08 | Approve condition | QA Lead | `testcondition.approve` |
| TCN-09 | Archive condition | QA Lead | `testcondition.archive` |
| TCN-10 | Trace condition to scenario/case | QA Lead/Tester | `trace.create` |
| TCN-11 | Detect uncovered conditions | read roles | `coverage.read` |
| TCN-12 | Bulk prioritize conditions | QA Lead/Tester | `testcondition.bulk.update` |

## 7.8. Deterministic checks TAN-03

Không cần LLM cho:

```text
missing title
missing AC
empty expected behavior
unresolved placeholder/TODO
requirement has permission keyword but no actor/rule
numeric bound mentioned but no boundary semantics
state transition keyword but no source/target state
NFR requirement lacks measurable target
```

AI chỉ bổ sung semantic analysis.

## 7.9. AI output contract

```json
{
  "status": "SUCCESS",
  "findings": [
    {
      "category": "AMBIGUITY",
      "severity": "MAJOR",
      "statement": "...",
      "evidence_refs": ["..."],
      "reason_codes": ["MULTIPLE_INTERPRETATIONS"],
      "suggestion": "..."
    }
  ],
  "condition_candidates": [],
  "model": {},
  "confidence": 0.81
}
```

Không lưu hidden chain-of-thought.

## 7.10. UI

Route:

```text
/du-an/{project_id}/phan-tich-kiem-thu
```

Layout:

```text
left: Test Basis tree
center: Requirement/AC content + findings anchors
right: Findings / TestCondition candidates
bottom: Trace preview
```

Actions:
- Create Condition;
- AI Analyze;
- Resolve Finding;
- Submit Review;
- Approve;
- Generate Scenario from selected Condition.

## 7.11. Errors

```text
TEST_BASIS_NOT_FOUND
TEST_BASIS_PROJECT_MISMATCH
TEST_CONDITION_NOT_FOUND
TEST_CONDITION_NOT_DRAFT
TEST_CONDITION_INCOMPLETE
TEST_CONDITION_NOT_APPROVED
ANALYSIS_FINDING_NOT_FOUND
ANALYSIS_FINDING_ALREADY_RESOLVED
ANALYSIS_FINDING_RESOLUTION_REQUIRED
AI_TEST_ANALYSIS_UNAVAILABLE
```

## 7.12. Acceptance

```text
AC-TAN-01 Cross-project basis ref bị reject.
AC-TAN-02 AI down vẫn manual-create condition được.
AC-TAN-03 AI candidate không tự approve.
AC-TAN-04 RequirementVersion v2 không rewrite condition linked v1.
AC-TAN-05 Coverage hiển thị uncovered condition.
AC-TAN-06 Finding resolution có audit.
AC-TAN-07 Strict policy chặn submit TestCase không có approved condition.
AC-TAN-08 BA có thể review semantics nhưng không mặc định approve TestCase.
```

---

# 8. P0-E — TEST MONITORING & CONTROL

**Status:** `PARTIAL → EXTEND P0`

## 8.1. Tận dụng Quality Dashboard hiện tại

Không tạo dashboard mới.

Current quality dashboard trở thành presentation layer cho:

```text
MonitoringSnapshot
QualityGateEvaluation
ControlAction
QualityDecision
```

## 8.2. Entity: TestMonitoringSnapshot

```text
_id
project_id
test_plan_id
release_id
build_id
captured_at
captured_by
plan_revision
strategy_version_id
source_fingerprint

planned {
  total_scope
  planned_execution
  planned_start_at
  planned_end_at
  planned_effort_hours
}

actual {
  total_scope
  executed
  not_run
  in_progress
  pass
  fail
  blocked
  skipped
  not_applicable
  actual_effort_hours
}

coverage {
  requirement
  acceptance_criterion
  test_condition
  risk
}

defects {
  open_total
  blocker
  critical
  major
  minor
  reopened
  aging
}

maintenance {
  stale_testcases
  pending_impact
  pending_proposals
}

schedule {
  elapsed_percent
  execution_percent
  expected_completion_at
  variance
}

exit_criteria_evaluations[]
quality_gate_status
deviations[]
blockers[]
risk_refs[]
```

Snapshot immutable.

## 8.3. QualityGateEvaluation

```text
_id
project_id
test_plan_id
release_id
snapshot_id
rules[]
overall_status
blocking_reasons[]
warning_reasons[]
evaluated_at
engine_version
```

Status:

```text
PASS
WARN
FAIL
INSUFFICIENT_DATA
```

Đây là machine evaluation, không phải human decision.

## 8.4. ExitCriterionEvaluation

```text
criterion_id
description
rule_type
operator
threshold
actual
unit
status
evidence_refs[]
manual
```

Rule types P0:

```text
EXECUTION_PERCENT_MIN
PASS_RATE_MIN
OPEN_BLOCKER_MAX
OPEN_CRITICAL_MAX
REQUIREMENT_COVERAGE_MIN
AC_COVERAGE_MIN
CONDITION_COVERAGE_MIN
STALE_TESTCASE_MAX
REQUIRED_RUNS_COMPLETED
ENVIRONMENT_INCIDENT_MAX
CUSTOM_MANUAL_GATE
```

## 8.5. Deviation

```text
type
planned
actual
variance
severity
reason
owner_id
status
```

Types:
```text
SCHEDULE
SCOPE
EXECUTION
DEFECT
COVERAGE
EFFORT
ENVIRONMENT
QUALITY
```

## 8.6. ControlAction

```text
_id
project_id
test_plan_id
release_id
snapshot_id
type
title
description
priority
owner_id
due_at
status
decision_reason
evidence_refs[]
created_by
timestamps
```

Types:
```text
PAUSE_EXECUTION
RESUME_EXECUTION
REQUEST_RETEST
CREATE_ADDITIONAL_TEST_SCOPE
REQUEST_NEW_BUILD
BLOCK_RELEASE
ACCEPT_RISK_PROPOSAL
ESCALATE_DEFECT
REPRIORITIZE_REGRESSION
EXTEND_TEST_WINDOW
FIX_ENVIRONMENT
CLARIFY_REQUIREMENT
CUSTOM
```

State:
```text
OPEN
→ IN_PROGRESS
→ DONE
→ CANCELLED
```

## 8.7. QualityDecision — formalize current README behavior

Current actions:

```text
APPROVE_RELEASE
BLOCK_RELEASE
ACCEPT_RISK
```

Entity/record phải lưu:

```text
_id
project_id
release_id
build_id
snapshot_id
gate_evaluation_id
decision
reason
risk_acceptance {
  risks[]
  owner_id
  expiry_at
}
decided_by
decided_at
evidence_refs[]
supersedes_decision_id
```

Rules:

```text
Only QA_LEAD by default.
ACCEPT_RISK → reason required.
FAIL gate + APPROVE_RELEASE → forbidden unless project policy explicitly permits override.
Override → separate override reason + audit.
New decision does not delete previous history.
```

## 8.8. Function register

| ID | Function | Role | Permission |
|---|---|---|---|
| MON-01 | View monitoring dashboard | all read roles | `testmonitor.read` |
| MON-02 | Create snapshot | QA Lead/system | `testmonitor.snapshot.create` |
| MON-03 | View snapshot history | all read roles | `testmonitor.read` |
| MON-04 | Evaluate exit criteria | system/QA Lead | `testmonitor.evaluate` |
| MON-05 | View deviations | all read roles | `testmonitor.read` |
| MON-06 | Create control action | QA Lead/Tester suggest | `testmonitor.control.create` |
| MON-07 | Assign control action | QA Lead | `testmonitor.control.assign` |
| MON-08 | Update control action | owner/QA Lead | `testmonitor.control.update` |
| MON-09 | Close control action | QA Lead/owner | `testmonitor.control.update` |
| MON-10 | Re-evaluate after new result | system | internal |
| QGT-01 | View gate evaluation | read roles | `qualitygate.read` |
| QGT-02 | Approve release | QA Lead | `qualitygate.decide` |
| QGT-03 | Block release | QA Lead | `qualitygate.decide` |
| QGT-04 | Accept risk | QA Lead | `qualitygate.accept_risk` |
| QGT-05 | Override failed criterion | QA Lead + policy | `qualitygate.override` |
| QGT-06 | View decision history | read roles | `qualitygate.read` |
| QGT-07 | Supersede prior decision | QA Lead | `qualitygate.decide` |
| QGT-08 | Export gate evidence | QA Lead/Viewer policy | `report.export` |

## 8.9. Calculations

Deterministic:

```text
execution_percent =
executed / in_scope * 100

pass_rate =
pass / (pass + fail + blocked) * 100
```

Rules:
- SKIPPED/NOT_APPLICABLE denominator configurable and explicit.
- Zero denominator → `INSUFFICIENT_DATA`, không tự thành 100%.
- Corrected result uses current effective result while snapshot captures point-in-time values.

## 8.10. Snapshot trigger

Support:

```text
manual
scheduled
run_completed
build_changed
before_quality_decision
before_status_report
before_completion_report
```

P0 không cần background scheduler phức tạp; có thể event-driven + manual.

## 8.11. UI changes

Current QA Lead quality area:
- giữ cards;
- thêm `Snapshot at`;
- link gate evidence;
- exit criteria table;
- deviations;
- control actions;
- decision history.

Other roles:
- read metrics allowed by permission;
- hide decision actions.

## 8.12. Acceptance

```text
AC-MON-01 Snapshot immutable.
AC-MON-02 Same source fingerprint + idempotency không duplicate.
AC-MON-03 Snapshot cũ không đổi sau ResultCorrection.
AC-MON-04 Gate calculation deterministic.
AC-MON-05 Zero denominator = insufficient data.
AC-MON-06 Accept risk requires reason.
AC-MON-07 Viewer cannot decide.
AC-MON-08 System Admin without membership cannot decide.
AC-MON-09 Control action cannot mutate frozen TestRun scope.
AC-MON-10 Quality decision history append-only.
```

---

# 9. P0-F — TEST STATUS REPORT

**Status:** `TO_BUILD_P0`

## 9.1. Khác Dashboard

```text
Dashboard = live
StatusReport = frozen communication artifact
```

## 9.2. Entity

```text
TestStatusReport
_id
project_id
report_key
test_plan_id
strategy_version_id
release_id
build_id
reporting_period_start
reporting_period_end
snapshot_id

executive_summary_doc
progress_summary
coverage_summary
defect_summary
maintenance_summary

deviations[]
blockers[]
risks[]
control_action_ids[]

forecast {
  expected_completion_at
  confidence
  assumptions[]
}

recommendation
distribution[]
status
revision
created_by
submitted_by
approved_by
published_at
timestamps
```

Recommendation:
```text
ON_TRACK
AT_RISK
BLOCKED
CONTINUE_TESTING
READY_WITH_RISK
NOT_READY
```

State:
```text
DRAFT
→ IN_REVIEW
→ APPROVED
→ PUBLISHED
→ ARCHIVED

IN_REVIEW
→ DRAFT
```

Approved/published report immutable.

## 9.3. Function register

| ID | Function | Role | Permission |
|---|---|---|---|
| TSR-01 | List status reports | read roles | `teststatusreport.read` |
| TSR-02 | Generate from snapshot | QA Lead/Tester policy | `teststatusreport.create` |
| TSR-03 | Edit narrative | creator/QA Lead | `teststatusreport.update` |
| TSR-04 | Submit review | creator | `teststatusreport.submit_review` |
| TSR-05 | Review | QA Lead/BA/Tester | `teststatusreport.review` |
| TSR-06 | Approve | QA Lead | `teststatusreport.approve` |
| TSR-07 | Publish | QA Lead | `teststatusreport.publish` |
| TSR-08 | Export | permitted roles | `report.export` |
| TSR-09 | Compare reports | read roles | `teststatusreport.read` |
| TSR-10 | Archive | QA Lead | `teststatusreport.archive` |

## 9.4. Generated vs editable

Generated facts:
```text
progress
coverage
defect counts
gate state
deviations
```

Không cho user sửa số.

Editable:
```text
executive summary
risk explanation
forecast assumptions
recommendation narrative
```

## 9.5. Acceptance

```text
AC-TSR-01 Report facts match snapshot.
AC-TSR-02 Editing narrative cannot change numeric facts.
AC-TSR-03 Published report immutable.
AC-TSR-04 Export includes report/snapshot timestamp.
AC-TSR-05 Historical report survives later result corrections.
```

---

# 10. P0-G — TEST COMPLETION / CLOSURE

**Status:** `TO_BUILD_P0`

## 10.1. Entity

```text
TestCompletionReport
_id
project_id
completion_key
test_plan_id
strategy_version_id
release_id
build_ids[]
final_snapshot_id

scope_snapshot
completed_run_ids[]
execution_summary
coverage_summary
defect_summary
maintenance_summary

unexecuted_scope[]
unresolved_items[]
residual_risks[]
exit_criteria_evaluations[]
deviations[]

testware_handover[]
archived_artifacts[]
environment_closure[]

lessons_learned[]
improvement_actions[]

recommendation
sign_offs[]

status
revision
created_by
submitted_by
approved_by
closed_by
timestamps
```

## 10.2. ResidualRisk

```text
risk_id
title
description
severity
probability
impact
source_refs[]
owner_id
treatment
accepted_by
accepted_at
expiry_at
status
```

## 10.3. TestwareHandoverItem

```text
artifact_type
artifact_id
artifact_version_id
handover_to
storage_location
status
note
```

## 10.4. LessonsLearnedItem

```text
category
observation
impact
recommendation
evidence_refs[]
owner_id
convert_to_improvement
```

## 10.5. State

```text
DRAFT
→ IN_REVIEW
→ APPROVED
→ CLOSED

IN_REVIEW
→ DRAFT
```

`CLOSED` final immutable.

## 10.6. Completion readiness

Cannot approve when project policy requires and:

```text
mandatory runs not completed
open Blocker > threshold
critical residual risk has no owner
exit criterion FAIL without accepted waiver
unexecuted scope has no reason
```

## 10.7. Release close integration

Setting:

```text
require_completion_report_before_release_close
```

When true:

```text
Release close
→ require CompletionReport APPROVED/CLOSED
→ require no unresolved mandatory gate
```

## 10.8. Function register

| ID | Function | Role | Permission |
|---|---|---|---|
| TCP-01 | List completion reports | read roles | `testcompletion.read` |
| TCP-02 | Generate draft | QA Lead | `testcompletion.create` |
| TCP-03 | Update narrative/risk | QA Lead/Tester contribute | `testcompletion.update` |
| TCP-04 | Add residual risk | QA Lead | `testcompletion.risk.manage` |
| TCP-05 | Add lesson learned | QA Lead/Tester/BA/Dev | `testcompletion.lesson.create` |
| TCP-06 | Manage handover | QA Lead | `testcompletion.handover.manage` |
| TCP-07 | Submit review | QA Lead | `testcompletion.submit_review` |
| TCP-08 | Review | QA Lead/Tester/BA/Dev | `testcompletion.review` |
| TCP-09 | Approve | QA Lead | `testcompletion.approve` |
| TCP-10 | Close | QA Lead | `testcompletion.close` |
| TCP-11 | Export | permitted | `report.export` |
| TCP-12 | Gate Release close | system | internal |

## 10.9. Acceptance

```text
AC-TCP-01 Completion uses final immutable snapshot.
AC-TCP-02 Open blocker appears in unresolved list.
AC-TCP-03 Residual critical risk needs owner.
AC-TCP-04 Failed criterion cannot disappear.
AC-TCP-05 Closed report immutable.
AC-TCP-06 Release close blocked by policy if report missing.
AC-TCP-07 Lessons learned remain after project archive.
```

---

# 11. P1-A — FORMAL PEER REVIEW

**Status:** `TO_BUILD_P1`

Current `ReviewComment` remains.

Formal review is an additional orchestration layer.

## 11.1. Entity

```text
ReviewSession
_id
project_id
review_key
review_type
artifact_type
artifact_id
artifact_version_id
objective
checklist_version_id
moderator_id
author_id
reviewer_ids[]
scribe_id
planned_at
started_at
completed_at
decision
status
metrics
revision
timestamps
```

```text
ReviewFinding
_id
review_session_id
project_id
category
severity
anchor
description
suggested_action
owner_id
due_at
status
resolution
resolved_by
verified_by
timestamps
```

## 11.2. Review type

```text
REQUIREMENT
TEST_STRATEGY
TEST_PLAN
TEST_CONDITION
TEST_CASE
IMPACT_ANALYSIS
STATUS_REPORT
COMPLETION_REPORT
```

## 11.3. State

ReviewSession:
```text
PLANNED
→ IN_PROGRESS
→ DECISION_PENDING
→ COMPLETED
→ ARCHIVED

PLANNED → CANCELLED
```

Finding:
```text
OPEN
→ IN_PROGRESS
→ RESOLVED
→ VERIFIED
```

Decision:
```text
ACCEPTED
ACCEPTED_WITH_ACTIONS
REWORK_REQUIRED
REJECTED
```

## 11.4. Function register

```text
RVS-01 Create session
RVS-02 Assign reviewers
RVS-03 Start session
RVS-04 Add finding
RVS-05 Assign finding
RVS-06 Resolve finding
RVS-07 Verify finding
RVS-08 Record decision
RVS-09 Complete session
RVS-10 View metrics
RVS-11 Reopen review only by new session
RVS-12 Export review record
```

No in-place reopen of COMPLETED session.
Create follow-up session.

---

# 12. P1-B — MEASUREMENT REGISTRY

**Status:** `TO_BUILD_P1`

## 12.1. MeasurementDefinition

```text
_id
project_id | null for platform template
key
name
objective
description
formula_type
formula
unit
data_sources[]
dimensions[]
aggregation
period
target
warning_threshold
critical_threshold
owner_role
status
version
```

No arbitrary Python/JS formula execution.

Supported formula types:
```text
BUILT_IN
RATIO
COUNT
DURATION
PERCENTILE
CUSTOM_SAFE_EXPRESSION
```

## 12.2. P1 metric catalogue

```text
REQUIREMENT_COVERAGE
AC_COVERAGE
CONDITION_COVERAGE
RISK_COVERAGE
EXECUTION_PROGRESS
PASS_RATE
BLOCKED_RATE
DEFECT_REOPEN_RATE
CRITICAL_DEFECT_AGING
MEAN_TIME_TO_RETEST
STALE_TEST_RATIO
REQUIREMENT_VOLATILITY
IMPACT_PROPOSAL_ACCEPTANCE_RATE
REGRESSION_EFFECTIVENESS
AUTOMATION_COVERAGE
AUTOMATION_STABILITY
```

Conditional:
```text
ESCAPED_DEFECT_RATE
DEFECT_REMOVAL_EFFICIENCY
```

Only if source data exists.

## 12.3. Functions

```text
MET-01 List definitions
MET-02 Create project definition
MET-03 Version definition
MET-04 Activate definition
MET-05 Archive definition
MET-06 Compute snapshot
MET-07 View trend
MET-08 Compare releases
MET-09 Threshold alert
MET-10 Export metric data
MET-11 Validate formula/source
MET-12 Pin metric to dashboard
```

---

# 13. P1-C — PRODUCT QUALITY EVALUATION

**Status:** `PARTIAL FOUNDATION FROM QUALITY GATE → TO_BUILD_P1`

## 13.1. Không trùng current QualityDecision

`QualityDecision` = one decision event.

`ProductQualityEvaluation` = controlled artifact assembling evidence.

## 13.2. Entity

```text
ProductQualityEvaluation
_id
project_id
evaluation_key
release_id
build_id
strategy_version_id
snapshot_id
measurement_snapshot_refs[]
gate_evaluation_id

quality_objective_results[]
exit_criteria_results[]
critical_risks[]
unresolved_defects[]
waivers[]

system_recommendation
human_decision
rationale_doc
evidence_refs[]

status
revision
created_by
reviewed_by[]
approved_by
timestamps
```

System recommendation:
```text
GO
GO_WITH_RISK
NO_GO
MORE_TESTING_REQUIRED
INSUFFICIENT_DATA
```

Human decision uses current QualityDecision contract.

## 13.3. Waiver

```text
waiver_id
criterion_or_metric
actual
threshold
reason
risk
owner_id
expiry_at
evidence_refs[]
approved_by
approved_at
```

No indefinite silent waiver.

---

# 14. P1-D — DEFECT PREVENTION / RCA / CAPA

**Status:** `TO_BUILD_P1`

## 14.1. Extend Defect

```text
root_cause_category
root_cause_detail
injected_phase
detected_phase
escape_reason
prevention_candidate
```

## 14.2. Root cause categories

```text
REQUIREMENT
DESIGN
IMPLEMENTATION
CONFIGURATION
TEST_DATA
TEST_CASE_GAP
ENVIRONMENT
INTEGRATION
DEPLOYMENT
PROCESS
THIRD_PARTY
UNKNOWN
```

## 14.3. CausalAnalysis

```text
_id
project_id
analysis_key
defect_ids[]
problem_statement
evidence_refs[]
root_causes[]
contributing_factors[]
five_whys[]
corrective_actions[]
preventive_actions[]
owner_id
effectiveness_review_at
status
revision
```

State:
```text
DRAFT
→ IN_REVIEW
→ APPROVED
→ ACTION_IN_PROGRESS
→ EFFECTIVENESS_REVIEW
→ CLOSED
```

## 14.4. Trigger suggestions

System suggests RCA when:
```text
Blocker
Critical
reopen_count >= configurable threshold
duplicate cluster >= threshold
same root-cause pattern repeats
```

Does not auto-create approved RCA.

## 14.5. Functions

```text
RCA-01 Suggest RCA candidate
RCA-02 Create RCA
RCA-03 Link defects
RCA-04 Add five-whys
RCA-05 Record root cause
RCA-06 Create corrective action
RCA-07 Create preventive action
RCA-08 Assign action
RCA-09 Submit review
RCA-10 Approve
RCA-11 Effectiveness review
RCA-12 Close
```

---

# 15. P1-E — ENVIRONMENT INCIDENT

**Status:** `TO_BUILD_P1`

## 15.1. Entity

```text
EnvironmentIncident
_id
project_id
incident_key
environment_id
build_id
observed_at
severity
type
description
affected_run_ids[]
evidence_refs[]
owner_id
status
resolution
downtime_start
downtime_end
created_by
timestamps
```

Types:
```text
UNAVAILABLE
DEPLOYMENT_FAILURE
TEST_DATA_FAILURE
NETWORK
DEPENDENCY
CONFIGURATION
CAPACITY
CERTIFICATE
ACCESS
OTHER
```

State:
```text
OPEN
→ INVESTIGATING
→ MITIGATED
→ RESOLVED
→ CLOSED
```

Integration:
- Monitoring blocker;
- control action;
- TestRun warning;
- completion report.

---

# 16. P1-F — NON-FUNCTIONAL TEST ARTIFACT NORMALIZATION

**Status:** `PARTIAL → EXTEND P1`

Repo already has:
- security suggestion;
- performance plan draft;
- device matrix;
- automation script.

Do not build scanners.

## 16.1. SecurityTestPlan

```text
scope
requirement_refs
risk_refs
categories
test_conditions
test_cases
tool_refs
environment
evidence
result_summary
residual_risk
```

## 16.2. PerformanceTestPlan

```text
objective
workload_model
baseline
load
stress
spike
soak
concurrency
throughput_target
response_time_target
error_rate_target
environment
data
external_tool_ref
result_summary
```

External evidence imports P2:
```text
k6
JMeter
ZAP
```

---

# 17. P2 — PROCESS IMPROVEMENT

**Status:** `TO_BUILD_P2`

## 17.1. Entity

```text
ProcessImprovementProposal
_id
project_id
source
observed_problem
evidence_refs[]
baseline_metrics[]
proposed_change
expected_effect
experiment_scope
owner_id
status
result_metrics[]
decision
timestamps
```

State:
```text
PROPOSED
→ APPROVED_EXPERIMENT
→ RUNNING
→ EVALUATED
→ ADOPTED | REJECTED
```

Functions:
```text
PIM-01 Create proposal
PIM-02 Link lesson/RCA
PIM-03 Approve experiment
PIM-04 Record baseline
PIM-05 Run/evaluate experiment
PIM-06 Compare result
PIM-07 Adopt
PIM-08 Reject/archive
```

---

# 18. P2 — STATISTICAL QUALITY CONTROL

**Status:** `TO_BUILD_P2`

Only after sufficient historic measurements.

Functions:
```text
SQC-01 Define baseline window
SQC-02 Calculate center line
SQC-03 Calculate control limits
SQC-04 Plot trend/control chart
SQC-05 Detect outlier
SQC-06 Alert process instability
SQC-07 Annotate special cause
SQC-08 Compare before/after improvement
```

Deterministic math only.

AI may explain pattern but not calculate hidden numbers.

---

# 19. ROLE MATRIX V5.1

Legend:
```text
F = full/default
C = contribute
R = read
P = policy-dependent
- = deny
```

| Module | QA Lead | Tester | BA | Developer | Viewer |
|---|---:|---:|---:|---:|---:|
| Test Strategy | F | C | C | R | R |
| Test Plan | F | C | R/C | R | R |
| Test Analysis | F | F | C | R/C | R |
| Test Condition | F | F | C | R | R |
| Monitoring | F | C | R | R | R |
| Quality Decision | F | - | - | - | - |
| Status Report | F | C | C | R | R |
| Completion | F | C | C | C | R |
| Formal Review | F | C | C | C | R |
| Measurement | F | R | R | R | R |
| Quality Evaluation | F | C | C | C | R |
| RCA | F | C | C | C/F assigned | R |
| Environment Incident | F | C | R | C | R |
| Process Improvement | F | C | C | C | R |

## 19.1. Role non-negotiables

```text
Developer cannot record QA PASS/FAIL by default.
Tester cannot approve release by default.
BA cannot approve TestCase by default.
Viewer cannot mutate test artifacts.
System Admin does not automatically become project QA authority.
AI cannot impersonate a role.
```

---

# 20. NAVIGATION V5.1

Recommended top-level Project nav:

```text
Overview
Requirements
Test Analysis
Test Design
Planning & Execution
Traceability
Change & Maintenance
AI Review
Defects
Reports
Knowledge
Settings
```

Nested `Planning & Execution`:

```text
Strategy
Plans
Releases & Builds
Environments
Suites
Runs
Monitoring
```

Nested `Reports`:

```text
Status Reports
Completion
Coverage
Execution
Defects
Quality Evaluation
Measurements
```

P1:
```text
RCA / Improvement
```

Do not add every sub-feature as sidebar item.

---

# 21. UI SCREEN CONTRACTS

## 21.1. Test Strategy screen

Must show:
```text
current approved strategy
draft/in-review versions
version
status
test levels
test types
risk model
entry/exit defaults
automation policy
review state
```

Buttons permission-aware:
```text
New Draft
Edit
Validate
Submit Review
Request Changes
Approve
New Version
Compare
Archive
```

## 21.2. Test Analysis screen

Must show:
```text
basis tree
selected source
testability findings
condition list
risk/priority
trace target
AI candidate indicator
```

## 21.3. Monitoring screen

Must show:
```text
snapshot timestamp
plan-vs-actual
execution
coverage
defects
schedule deviation
maintenance debt
exit criteria
quality gate
control actions
decision history
```

## 21.4. Status Report screen

Must show:
```text
frozen numbers
editable narrative
review state
distribution
export
```

## 21.5. Completion screen

Must show:
```text
final scope
unexecuted scope
coverage
defects
residual risk
exit criteria
handover
lessons learned
sign-off
```

---

# 22. BACKEND FILE PLAN

Do not extend giant files further.

Create:

```text
backend/testing/src/api/
├── test_strategy.py
├── test_analysis.py
├── test_monitoring.py
├── test_status_reports.py
├── test_completion.py
├── review_sessions.py
├── measurements.py
├── product_quality.py
├── defect_prevention.py
└── environment_incidents.py
```

Services:

```text
backend/testing/src/services/
├── test_strategy_service.py
├── test_analysis_service.py
├── test_monitoring_service.py
├── exit_criteria_service.py
├── quality_gate_service.py
├── test_status_report_service.py
├── test_completion_service.py
├── review_session_service.py
├── measurement_service.py
├── product_quality_service.py
├── causal_analysis_service.py
└── environment_incident_service.py
```

Repositories:

```text
backend/testing/src/repositories/
```

Create repository abstractions only where business module is complex.
Do not introduce pointless abstraction for one-line reads.

---

# 23. FRONTEND FILE PLAN

Create:

```text
frontend/features/testing/pages/workspace/
├── TestAnalysisPage.jsx
└── MonitoringPage.jsx
```

Do not create unnecessary top-level pages for every artifact.

Components:

```text
components/governance/
components/analysis/
components/monitoring/
components/reports/
components/reviews/
components/quality/
components/rca/
```

Refactor existing large pages gradually.

---

# 24. DATABASE COLLECTIONS

P0:

```text
test_strategies
test_conditions
test_analysis_findings
test_monitoring_snapshots
quality_gate_evaluations
quality_decisions        # reuse existing store if current implementation has equivalent
test_control_actions
test_status_reports
test_completion_reports
```

P1:

```text
review_sessions
review_findings
measurement_definitions
measurement_snapshots
product_quality_evaluations
causal_analyses
preventive_actions
environment_incidents
```

P2:

```text
process_improvement_proposals
process_control_baselines
```

## 24.1. Index rules

Every project entity:

```text
(project_id, _id)
project_id + business key unique
project_id + status + updated_at
```

Retryable create:
```text
(project_id, idempotency_key) partial unique
```

Versioned:
```text
(parent/business entity id, version) unique
```

---

# 25. ERROR CODE CATALOGUE

Common:
```text
AUTH_REQUIRED
PROJECT_PERMISSION_DENIED
PROJECT_SCOPE_MISMATCH
STALE_REVISION
IDEMPOTENCY_CONFLICT
INVALID_STATE_TRANSITION
ARTIFACT_NOT_FOUND
ARTIFACT_ARCHIVED
CROSS_PROJECT_REFERENCE
```

Strategy:
```text
TEST_STRATEGY_NOT_FOUND
TEST_STRATEGY_NOT_DRAFT
TEST_STRATEGY_INCOMPLETE
TEST_STRATEGY_ACTIVE_CONFLICT
INVALID_RISK_MODEL
```

Analysis:
```text
TEST_BASIS_NOT_FOUND
TEST_CONDITION_NOT_FOUND
TEST_CONDITION_INCOMPLETE
TEST_CONDITION_NOT_APPROVED
ANALYSIS_FINDING_NOT_FOUND
ANALYSIS_FINDING_ALREADY_RESOLVED
```

Monitoring:
```text
MONITORING_SOURCE_INCOMPLETE
MONITORING_SNAPSHOT_NOT_FOUND
QUALITY_GATE_INSUFFICIENT_DATA
QUALITY_GATE_BLOCKED
QUALITY_DECISION_REASON_REQUIRED
QUALITY_GATE_OVERRIDE_NOT_ALLOWED
CONTROL_ACTION_NOT_FOUND
```

Report:
```text
STATUS_REPORT_NOT_FOUND
STATUS_REPORT_IMMUTABLE
COMPLETION_REPORT_NOT_FOUND
COMPLETION_REPORT_NOT_READY
RESIDUAL_RISK_OWNER_REQUIRED
RELEASE_COMPLETION_GATE_FAILED
```

---

# 26. AUDIT EVENT CATALOGUE

P0:

```text
test_strategy_created
test_strategy_submitted
test_strategy_changes_requested
test_strategy_approved
test_strategy_version_created
test_strategy_archived

test_analysis_executed
analysis_finding_created
analysis_finding_resolved
analysis_finding_verified

test_condition_created
test_condition_updated
test_condition_submitted
test_condition_approved
test_condition_archived

monitoring_snapshot_created
exit_criteria_evaluated
control_action_created
control_action_updated
quality_gate_evaluated
quality_decision_recorded
quality_risk_accepted
quality_gate_overridden

status_report_created
status_report_approved
status_report_published

completion_report_created
completion_report_approved
completion_report_closed
residual_risk_accepted
release_close_blocked
release_closed_after_completion
```

P1:
```text
formal_review_started
formal_review_completed
review_finding_created
review_finding_verified
measurement_definition_activated
product_quality_evaluation_approved
causal_analysis_approved
preventive_action_closed
environment_incident_created
environment_incident_closed
```

---

# 27. AI CONTRACT V5.1

## 27.1. AI may

```text
analyze requirement quality
suggest TestConditions
suggest test techniques
generate TestScenario/TestCase draft
summarize monitoring evidence
draft Status Report narrative
summarize Completion evidence
suggest RCA hypotheses
cluster lessons learned
```

## 27.2. AI may not

```text
approve TestStrategy
approve TestCondition
mark quality gate PASS manually
approve release
accept risk
approve Completion
set QA PASS/FAIL
close Defect
confirm RCA as fact without human
```

## 27.3. Every AI result

```text
status
capability
evidence_refs
reason_codes
confidence
provider
model
prompt_version
tool_schema_version
retrieval_version
created_at
degraded_mode
warnings
```

---

# 28. CONCURRENCY & IDEMPOTENCY

Use `expected_revision` for:

```text
Strategy draft update
Condition update
Finding resolution
ControlAction update
StatusReport update
CompletionReport update
ReviewSession update
RCA update
```

Use `idempotency_key` for:

```text
AI analysis request
Monitoring snapshot create
Status report generate
Completion draft generate
Quality decision
RCA candidate generate
Measurement snapshot compute
```

Never silently overwrite a newer revision.

---

# 29. SECURITY REQUIREMENTS

## P0 tests

```text
cross-project IDOR
viewer mutation
developer PASS/FAIL attempt
tester quality decision attempt
admin without membership project artifact access
evidence download permission
AI tool delegated permission
stale JWT/session revoked
secret ref exposure
attachment path/url exposure
```

AI evidence must be project-filtered before retrieval.

---

# 30. REPOSITORY DEVTESTOPS QUALITY GATE

**Status:** `TO_BUILD_P0`

Create:
```text
.github/workflows/ci.yml
```

PR jobs:

```text
backend-lint
backend-fast-tests
testing-contract-tests
authorization-tests
function-id-closure
frontend-lint
frontend-unit
frontend-role-smoke
docker-compose-config
```

Nightly/full:

```text
testing-full-integration
frontend-e2e
AI benchmarks
impact benchmark
duplicate benchmark
security smoke
```

## 30.1. Function closure script

```text
scripts/check_testing_function_registry.py
```

Fail CI when:
```text
mutation route missing permission
route missing x-function-id when required
unknown permission
duplicate function ID
high-impact mutation missing audit
state transition endpoint lacks state validation test
```

## 30.2. Branch protection

Recommended:
```text
Pull Request required
CI required
no merge on failed required checks
```

---

# 31. TEST CASE CATALOGUE — P0 CROSS-MODULE

## Strategy
```text
V51-STR-001 Create draft
V51-STR-002 Submit complete strategy
V51-STR-003 Reject incomplete strategy
V51-STR-004 QA Lead approve
V51-STR-005 Tester approve denied
V51-STR-006 New version after approval
V51-STR-007 Stale update conflict
V51-STR-008 Cross-project denied
```

## Analysis
```text
V51-TAN-001 Analyze baselined requirement
V51-TAN-002 Create manual condition
V51-TAN-003 AI suggest condition
V51-TAN-004 AI unavailable fallback
V51-TAN-005 Finding lifecycle
V51-TAN-006 Strict condition policy
V51-TAN-007 Req version history preserved
V51-TAN-008 uncovered condition report
```

## Monitoring
```text
V51-MON-001 Snapshot
V51-MON-002 Idempotent snapshot
V51-MON-003 Pass-rate formula
V51-MON-004 insufficient denominator
V51-MON-005 gate fail blocker
V51-MON-006 accept risk with reason
V51-MON-007 accept risk without reason denied
V51-MON-008 decision history append-only
V51-MON-009 old snapshot immutable
V51-MON-010 control action lifecycle
```

## Status
```text
V51-TSR-001 Generate from snapshot
V51-TSR-002 facts frozen
V51-TSR-003 edit narrative only
V51-TSR-004 approve/publish
V51-TSR-005 historical export
```

## Completion
```text
V51-TCP-001 generate final report
V51-TCP-002 blocker prevents approval
V51-TCP-003 waiver allows documented risk
V51-TCP-004 unexecuted scope requires reason
V51-TCP-005 release close policy
V51-TCP-006 closed immutable
```

---

# 32. END-TO-END ACCEPTANCE FLOW

## E2E-V51-01 — Full manual lifecycle

```text
1. QA Lead creates Project
2. QA Lead creates Strategy
3. Tester contributes
4. QA Lead approves Strategy v1
5. BA creates/baselines Requirement v1
6. Tester opens Test Analysis
7. System/AI suggests testability finding
8. BA resolves ambiguity in Requirement v2
9. Tester creates TestConditions
10. QA Lead approves conditions
11. Tester creates Scenario/TestCases
12. QA Lead approves TestCaseVersions
13. Tester creates TestPlan linked Strategy v1
14. QA Lead approves Plan
15. Release/Build/Environment selected
16. Tester creates Run exact versions
17. Execute PASS/FAIL
18. Fail step → Defect + evidence
19. Developer fixes
20. Tester retests
21. Monitoring snapshot generated
22. Exit criteria evaluated
23. QA Lead creates control action if needed
24. QA Lead records quality decision
25. Status Report published
26. Requirement changes
27. Impact analysis
28. AI proposal
29. Human applies proposal → TestCaseVersion new
30. Regression run
31. Final snapshot
32. Completion report
33. Residual risk/sign-off
34. Release close
```

## E2E-V51-02 — Quality gate blocked

```text
1. Blocker defect open
2. Snapshot
3. Gate FAIL
4. Approve Release action denied by strict policy
5. QA Lead may Block Release
6. If policy permits risk acceptance, explicit reason/owner/expiry
7. History retains both gate and decision
```

## E2E-V51-03 — AI outage

```text
1. AI service unavailable
2. Requirement manual edit works
3. Manual TestCondition works
4. Manual TestCase works
5. Execution works
6. Monitoring formulas work
7. Completion works
```

---

# 33. P0 BUILD ORDER CHI TIẾT

## Phase 0 — hardening

### PR-01 Domain cleanup
Done when:
```text
migration + tests + RAG reindex
```

### PR-02 Backend/frontend refactor shell
Do not fully refactor all code.
Extract the sections that V5.1 will touch first.

## Phase 1 — governance

### PR-03 TestStrategy domain/backend
### PR-04 TestStrategy UI
### PR-05 TestPlan extension + strategy binding

## Phase 2 — analysis

### PR-06 TestCondition + Finding backend
### PR-07 Analysis UI
### PR-08 Traceability/Coverage extension

## Phase 3 — monitoring

### PR-09 Monitoring snapshot + formula
### PR-10 Exit criteria/gate formalization
### PR-11 Control actions
### PR-12 Integrate current QA Lead dashboard

## Phase 4 — reporting/closure

### PR-13 Status Report
### PR-14 Completion Report
### PR-15 Release close gate

## Phase 5 — quality gate for repository

### PR-16 GitHub Actions
### PR-17 function registry closure
### PR-18 role/E2E smoke

---

# 34. P1 BUILD ORDER

```text
PR-19 Formal Review Sessions
PR-20 Measurement Registry
PR-21 Product Quality Evaluation
PR-22 RCA/CAPA
PR-23 Environment Incident
PR-24 NFR artifact normalization
```

---

# 35. WHAT IS NOT A P0 BLOCKER

Existing advanced features do not need further expansion before P0 closure:

```text
OpenAPI/Postman
automation scripts
automation execution
project connectors
CI/CD integration inside product
webhooks
realtime collaboration
device matrix
AI security suggestion
AI performance draft
bulk operations
advanced notification
```

Only fix blocking bugs/security defects in these while building P0.

---

# 36. DEFINITION OF DONE — ONE FUNCTION

A function is not DONE because button exists.

DONE requires:

```text
[ ] function ID
[ ] permission
[ ] API
[ ] backend validation
[ ] entity persistence
[ ] state rule
[ ] frontend role gating
[ ] success UI
[ ] empty state
[ ] loading state
[ ] error state
[ ] audit if mutation
[ ] concurrency/idempotency if relevant
[ ] permission test
[ ] happy-path integration test
[ ] negative/state test
[ ] E2E where critical
```

---

# 37. DEFINITION OF DONE — V5.1 P0

```text
[ ] No education metadata in testing domain
[ ] TestStrategy version/approval complete
[ ] TestPlan strategy binding and governance fields complete
[ ] Test Analysis workspace complete
[ ] TestCondition complete
[ ] Req→Condition→Scenario→Case trace complete
[ ] MonitoringSnapshot complete
[ ] deterministic ExitCriteriaEvaluation complete
[ ] current Quality Gate normalized
[ ] QualityDecision append-only
[ ] ControlAction complete
[ ] StatusReport complete
[ ] CompletionReport complete
[ ] Release completion gate complete
[ ] role matrix enforced backend + frontend
[ ] new function IDs registered
[ ] audit complete
[ ] CI quality gate complete
[ ] core E2E V51-01 passes
[ ] quality-block E2E V51-02 passes
[ ] AI-outage E2E V51-03 passes
```

---

# 38. STOP CONDITIONS — TRÁNH LẶP LẠI VẤN ĐỀ V4/V5

Sau V5.1, không tạo V5.2 chỉ vì phát hiện một button nhỏ.

Thay đổi nhỏ:
```text
update V5.1 revision/changelog
```

Chỉ tạo V6 khi có **scope/architecture change**, ví dụ:
- multi-organization tenancy;
- enterprise portfolio;
- autonomous execution agent;
- full external ALM federation;
- new research objective.

Một feature request mới phải đi qua:

```text
Does it support registered project objective?
→ Which process activity?
→ Which existing entity/module?
→ Can existing function be extended?
→ Is it P0/P1/P2?
→ Does it duplicate external tool?
```

Không vượt qua gate thì không add.

---

# 39. IMPLEMENTATION STATUS SNAPSHOT

Dựa trên V5 source audit + README hiện tại:

| Capability | Status |
|---|---|
| Requirement CRUD/version/import | IMPLEMENTED |
| AI Requirement assistance | README_IMPLEMENTED |
| Test Scenario/TestCase | IMPLEMENTED |
| Traceability/Coverage | IMPLEMENTED |
| TestPlan basic | IMPLEMENTED |
| Release/Build/Environment | IMPLEMENTED |
| TestRun/Result | IMPLEMENTED |
| Selected TestCaseVersion run | README_IMPLEMENTED |
| Defect/Retest | IMPLEMENTED |
| Fail-step → Defect | README_IMPLEMENTED |
| Defect evidence | README_IMPLEMENTED |
| Requirement Change/Impact | IMPLEMENTED |
| AI Maintenance Proposal | IMPLEMENTED |
| QA Lead quality dashboard | README_IMPLEMENTED |
| Quality decision | README_IMPLEMENTED/PARTIAL formalization |
| TestStrategy | TO_BUILD_P0 |
| Test Analysis/TestCondition | TO_BUILD_P0 |
| Formal MonitoringSnapshot | TO_BUILD_P0 |
| Exit Criteria Engine | TO_BUILD_P0 |
| Control Actions | TO_BUILD_P0 |
| Test Status Report | TO_BUILD_P0 |
| Test Completion | TO_BUILD_P0 |
| Formal ReviewSession | TO_BUILD_P1 |
| Measurement Registry | TO_BUILD_P1 |
| Product Quality Evaluation | TO_BUILD_P1 |
| RCA/CAPA | TO_BUILD_P1 |
| Environment Incident | TO_BUILD_P1 |
| Process Improvement | TO_BUILD_P2 |
| Statistical Quality Control | TO_BUILD_P2 |

`README_IMPLEMENTED` không được đổi sang `IMPLEMENTED` cho đến khi:
```text
runtime/API test pass
permission test pass
state/audit verified
```

---

# 40. FINAL BUILD PRINCIPLE

Không build Veriq theo cách:

```text
có feature list
→ thêm button
→ thêm endpoint
→ xong
```

Build theo:

```text
Process activity
→ controlled artifact
→ state
→ role
→ permission
→ function
→ API
→ UI
→ audit
→ test
```

Đây là tiêu chuẩn dùng cho mọi hạng mục V5.1.


# 41. MODULE BUILD CHECKLISTS

## 41.1. Test Strategy

- [ ] schema/entity + indexes
- [ ] service state machine
- [ ] permission keys
- [ ] function IDs
- [ ] CRUD/review/approval APIs
- [ ] versioning
- [ ] completeness validator
- [ ] UI list/editor/review/version history
- [ ] TestPlan binding
- [ ] audit
- [ ] tests

## 41.2. Test Plan Extension

- [ ] migration/defaults
- [ ] strategy version binding
- [ ] estimation
- [ ] schedule/milestones
- [ ] RACI
- [ ] risk register
- [ ] suspension/resumption
- [ ] quality targets
- [ ] approval completeness validator
- [ ] approved snapshot hash
- [ ] UI
- [ ] tests

## 41.3. Test Analysis

- [ ] TestBasisRef
- [ ] AnalysisFinding
- [ ] TestCondition
- [ ] indexes
- [ ] deterministic checks
- [ ] AI adapter contract
- [ ] finding lifecycle
- [ ] condition lifecycle
- [ ] trace extension
- [ ] coverage extension
- [ ] UI
- [ ] tests

## 41.4. Monitoring & Control

- [ ] snapshot model
- [ ] source fingerprint
- [ ] metric calculator
- [ ] exit criteria engine
- [ ] gate evaluation
- [ ] control action
- [ ] quality decision normalization
- [ ] existing dashboard integration
- [ ] history
- [ ] audit
- [ ] tests

## 41.5. Status Report

- [ ] report model
- [ ] generate from snapshot
- [ ] frozen numeric facts
- [ ] editable narrative
- [ ] review/approval/publish
- [ ] export
- [ ] history
- [ ] tests

## 41.6. Completion

- [ ] completion model
- [ ] final snapshot
- [ ] unexecuted scope
- [ ] residual risks
- [ ] exit criteria
- [ ] testware handover
- [ ] lessons learned
- [ ] sign-off
- [ ] release close gate
- [ ] export
- [ ] tests

## 41.7. Formal Review

- [ ] ReviewSession
- [ ] ReviewFinding
- [ ] checklist
- [ ] roles
- [ ] decision
- [ ] artifact integration
- [ ] metrics
- [ ] audit
- [ ] tests

## 41.8. Measurement

- [ ] definition
- [ ] safe formula
- [ ] snapshot
- [ ] thresholds
- [ ] trend
- [ ] release comparison
- [ ] dashboard pinning
- [ ] tests

## 41.9. RCA/CAPA

- [ ] Defect extensions
- [ ] RCA candidate rules
- [ ] CausalAnalysis
- [ ] five-whys
- [ ] corrective actions
- [ ] preventive actions
- [ ] effectiveness review
- [ ] tests


# 42. ROLE-BY-ROLE V5.1 RESPONSIBILITIES

## 42.1. QA_LEAD

- Own TestStrategy approval and version activation.
- Approve TestPlan and quality governance artifacts.
- Own Monitoring/Control and QualityDecision.
- Approve Completion and release-close gate.
- Can assign review/control/RCA actions.
- Cannot bypass audit or immutable history.

## 42.2. TESTER

- Contribute Strategy/Plan drafts.
- Own Test Analysis, Conditions, Scenario/TestCase design.
- Execute tests, create Defects/evidence, retest.
- Can create Monitoring observations/control suggestions.
- Can contribute Status/Completion evidence.
- Cannot approve release or final Completion by default.

## 42.3. BA

- Own/curate Requirement/Test Basis semantics.
- Resolve requirement testability findings.
- Review TestCondition meaning and traceability.
- Review Status/Completion business risk.
- Cannot record QA execution result.
- Cannot approve TestCase/Release by default.

## 42.4. DEVELOPER

- Read relevant strategy/plan/conditions/cases.
- Review technical feasibility and impact.
- Own assigned Defect fix workflow/evidence.
- Contribute RCA root-cause/corrective action.
- Cannot set QA PASS/FAIL.
- Cannot approve quality gate.

## 42.5. VIEWER

- Read project artifacts permitted by membership.
- Read reports/monitoring where allowed.
- No mutation.
- No defect evidence access unless explicit project policy later adds it.
- No AI mutation tools.


# 43. PR ACCEPTANCE GATE

Mỗi PR V5.1 phải trả lời trong description:

```text
Feature IDs:
Process activity:
Entities changed:
Permissions added/changed:
State transitions:
API added/changed:
Frontend screens:
Audit events:
Migration:
Backward compatibility:
Tests:
AI impact:
Security impact:
```

PR bị xem là chưa hoàn chỉnh nếu:
- chỉ có UI không có backend authorization;
- backend endpoint có nhưng không có state validation;
- mutation không audit;
- new entity không project-scope;
- function ID không đăng ký;
- role matrix backend/frontend lệch;
- AI-generated value được dùng như deterministic fact;
- approved historical artifact bị mutate.

---

# 44. CHANGELOG

## V5.1
- Chuyển V5 gap list thành build-ready contract.
- Đánh dấu các chức năng README báo đã bổ sung để tránh build trùng.
- Tách formal QualityGateEvaluation khỏi human QualityDecision.
- Chi tiết TestStrategy.
- Chi tiết TestPlan extension.
- Chi tiết Test Analysis/TestCondition.
- Chi tiết Monitoring & Control.
- Chi tiết Status Report.
- Chi tiết Test Completion.
- Chi tiết Formal Review, Measurement, Product Quality Evaluation, RCA/CAPA, Environment Incident.
- Khóa role boundaries.
- Khóa error/audit/concurrency/idempotency.
- Thêm PR acceptance gate.
- Thêm E2E acceptance flows.
- Giữ P2 optimization ngoài critical path.

---

# 45. SOURCE OF TRUTH RULE

Trong phạm vi feature mới V5.1:

```text
V5.1 Function/Entity/State/Permission Contract
> V5 prose
> README descriptive summary
```

Nhưng:

```text
runtime code + automated tests
```

mới chứng minh implementation thực tế.

Nếu code hiện tại khác V5.1 vì đã build trước:
1. đối chiếu semantics;
2. giữ implementation nếu tương đương;
3. update mapping;
4. không rename/rebuild vô ích;
5. chỉ sửa khi behavior vi phạm contract.

---

# 46. KẾT LUẬN

P0 hợp lý để build tiếp không phải thêm thật nhiều chức năng ngẫu nhiên.

P0 V5.1 là đóng sáu khoảng trống process chính:

```text
Strategy
Analysis
Plan governance
Monitoring & Control
Status Reporting
Completion
```

cộng:

```text
domain cleanup
architecture refactor
repository CI gate
```

Khi P0 hoàn thành, Veriq có lifecycle:

```text
Govern
→ Plan
→ Analyze
→ Design
→ Implement
→ Execute
→ Monitor/Control
→ Decide
→ Report
→ Complete
→ Learn
```

và vẫn giữ điểm khác biệt:

```text
Requirement change
→ trace + semantic impact
→ Agentic AI proposal
→ human review
→ controlled TestCase version
→ regression
```

Đó là phạm vi đủ chặt để build, demo và giải thích về mặt học thuật mà không biến dự án thành một enterprise ALM vô hạn.
