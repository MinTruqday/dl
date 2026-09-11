# ĐẶC TẢ V5 — TESTING DOCUMENT & QUALITY WORKFLOW PLATFORM
## Audit repository hiện tại và kế hoạch hoàn thiện theo tham chiếu công khai FPT Software + TMMi + ISTQB + ISO/IEC/IEEE 29119

**Repository audit:** `MinTruqday/dl`  
**Branch:** `main`  
**Commit baseline:** `484a56d571142010bff3b7afdea7b17ce60ae823`  
**Commit message:** `562 commit`  
**Ngày audit:** 10/09/2026  
**Trạng thái tài liệu:** BUILD SPEC AFTER LIVE REPOSITORY AUDIT  
**Tên sản phẩm:** chưa khóa; code hiện tại đang dùng tiêu đề `Veriq`, nhưng tài liệu này không xem đó là quyết định branding chính thức.

---

# 0. TUYÊN BỐ PHẠM VI VÀ CÁCH ĐỌC V5

## 0.1. V5 không phải tài liệu mô tả quy trình nội bộ bí mật của FPT Software

Không có cơ sở để khẳng định repository phải sao chép một quy trình nội bộ cụ thể của FPT Software nếu quy trình đó không được FPT công khai.

V5 dùng ba lớp đối chiếu:

1. **Thông tin công khai của FPT Software**
   - FPT Software công khai dịch vụ `Digital Assurance & Quality Engineering` theo hướng end-to-end.
   - FPT công khai DevTestOps, Automation Testing, Quality Engineering xuyên vòng đời.
   - FPT công khai TMMi Level 5, CMMI Development Level 5 và các chứng nhận/chương trình chất lượng khác trong nhiều tài liệu chính thức.
2. **TMMi**
   - dùng để kiểm tra độ trưởng thành của các process area kiểm thử.
3. **ISTQB + ISO/IEC/IEEE 29119**
   - dùng làm baseline quy trình test có thể áp dụng quốc tế.

Do đó câu chính xác là:

> Hệ thống được thiết kế để hỗ trợ một quy trình QA/Test Management tương thích với các nguyên tắc quốc tế mà FPT Software công khai theo đuổi, chứ không tuyên bố sao chép quy trình nội bộ của FPT Software.

## 0.2. Tài liệu này bảo vệ sự hợp lý của đề tài

Đề tài ban đầu là hệ thống quản lý và soạn thảo tài liệu thông minh tích hợp AI.

Vì vậy V5 không biến sản phẩm thành:
- một Jira clone;
- một full ALM enterprise suite;
- một HR/training system để quản lý chứng chỉ tester;
- một TMMi assessment tool;
- một full CI/CD platform;
- một vulnerability scanner;
- một performance testing platform hoàn chỉnh.

Cách định vị phù hợp nhất với code hiện tại là:

> **Nền tảng quản lý và soạn thảo tài liệu kiểm thử thông minh tích hợp AI, hỗ trợ toàn bộ vòng đời kiểm thử từ Requirement/Test Basis đến Test Design, Execution, Defect, Monitoring, Completion và bảo trì Test Case khi Requirement thay đổi.**

Các artifact kiểm thử chính vẫn là **tài liệu có cấu trúc**:
- Requirement Document;
- Requirement;
- Acceptance Criterion;
- Test Strategy;
- Test Plan;
- Test Condition;
- Test Scenario;
- Test Case;
- Test Suite;
- Test Run / Test Result;
- Defect;
- Change/Impact Analysis;
- Test Status Report;
- Test Completion Report;
- Review Report;
- Quality Measurement Snapshot.

AI là lớp hỗ trợ khai thác, phân tích và bảo trì các tài liệu đó.

---

# 1. NGUỒN THAM CHIẾU CHÍNH

## 1.1. FPT Software

### Digital Assurance & Quality Engineering
Nguồn:
`https://fptsoftware.com/services/it-services/digital-assurance-and-quality-engineering-service`

Điểm dùng để đối chiếu:
- end-to-end digital assurance;
- Quality Engineering;
- automated testing;
- testing ở nhiều level/activity/type;
- DevTestOps & Automation;
- quality assurance xuyên product lifecycle.

### FPT Software TMMi Level 5
Nguồn:
`https://fptsoftware.com/newsroom/news-and-press-releases/press-release/fpt-software-first-company-in-vietnam-to-achieve-tmmi-level-5`

Điểm dùng để đối chiếu:
- FPT Software công khai TMMi Level 5;
- continuous improvement;
- defect prevention;
- quality control;
- test process optimization;
- hỗ trợ cả V-model và Agile.

### FPT Software Company Brochure 2026
Nguồn:
`https://fptsoftware.com/-/media/Project/FPT%20Software/FSO/FSoft_Brochure_Jan-2026`

Điểm dùng để đối chiếu:
- TMMi maturity Level 5 Optimization;
- CMMI Development;
- ISO 9001;
- ISO/IEC 27001;
- quality management theo chuẩn hóa toàn cầu.

### FPT Digital Assurance / Automation materials
Nguồn tham khảo:
`https://fptsoftware.com/-/media/project/fpt-software/fso/pages/nha-trang-sfx/booth-3/1-ivs-automation-testing-2025-updated.pdf`

Điểm dùng để đối chiếu:
- End-to-End Digital Assurance;
- DevTestOps;
- automation implementation & maintenance;
- automated performance/regression;
- Quality First Development;
- AI-augmented testing;
- end-to-end testing management.

## 1.2. ISTQB

Nguồn:
`https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf`

Test process chuẩn được dùng trong V5:

```text
Test Planning
→ Test Monitoring & Control
→ Test Analysis
→ Test Design
→ Test Implementation
→ Test Execution
→ Test Completion
```

Các activity có thể chạy lặp hoặc song song tùy SDLC.

Nguồn Test Management:
`https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTAL-TM_Syllabus_v3.0_zKjKsaN.pdf`

## 1.3. ISO/IEC/IEEE 29119

Nguồn:
`https://www.iso.org/standard/79428.html`

ISO/IEC/IEEE 29119-2:2021 định nghĩa các test process có thể dùng để govern, manage và implement software testing cho nhiều SDLC.

## 1.4. TMMi

Nguồn:
`https://www.tmmi.org/tmmi-model/`

Mapping dùng trong audit:

```text
LEVEL 2 — MANAGED
- Test Policy and Strategy
- Test Planning
- Test Monitoring and Control
- Test Design and Execution
- Test Environment

LEVEL 3 — DEFINED
- organizational standardization
- training
- lifecycle integration
- non-functional testing
- reviews

LEVEL 4 — MEASURED
- test measurement
- product quality evaluation

LEVEL 5 — OPTIMIZATION
- defect prevention
- quality control
- test process optimization
```

V5 chỉ đánh giá **feature/process support** của sản phẩm.
Không được nói hệ thống này "đạt TMMi Level X" nếu chưa qua appraisal chính thức.

---

# 2. KẾT LUẬN AUDIT TỔNG QUÁT

## 2.1. Kết luận ngắn

Repository hiện tại **đã tiến rất xa và không còn thiếu các khối Test Management cơ bản**.

Các phần đã tương đối mạnh:
- Project + ProjectMembership + RBAC;
- Requirement authoring/import/extraction/versioning;
- Test Plan;
- Test Scenario;
- Test Case + versioning;
- Test Suite;
- Traceability + Coverage;
- Release / Build / Test Environment;
- Test Run / Result / Defect / Retest;
- Requirement change / Impact Analysis;
- AI maintenance proposals;
- Risk ranking;
- Test data;
- Test Case templates;
- OpenAPI/Postman;
- automation scripts/execution;
- connector/CI-CD/collaboration/notification/webhook;
- review comments;
- audit;
- reports/analytics;
- Agentic AI tools.

Nhưng repository **chưa kín quy trình kiểm thử quốc tế** vì còn thiếu hoặc chưa đủ formal ở các activity:

```text
1. Test Policy / Test Strategy
2. Test Analysis / Test Conditions
3. Test Monitoring & Control
4. Formal Test Status Reporting
5. Test Completion / Closure
6. Formal Peer Review Session
7. Measurement Definition / Product Quality Evaluation
8. Defect Prevention / Root Cause Analysis
9. Process Improvement
10. Repository-level DevTestOps quality gates
```

Đây là phần V5 tập trung hoàn thiện.

---

# 3. BASELINE REPOSITORY — NHỮNG GÌ ĐÃ CÓ THẬT

## 3.1. Backend bounded contexts

Tại commit audit, backend root có:

```text
backend/
├── ai/
├── authentication/
├── cloud/
├── content/
├── notification/
├── testing/
└── worker/
```

`backend/testing` là bounded context chính cho Test Management.

## 3.2. Testing routers hiện có

`backend/testing/src/main.py` đã register:

```text
projects
requirements
reviews
data_sets
device_matrices
design_suggestions
templates
test_design
traceability
changes
execution
execution_context
risk
analytics
automation_scripts
connectors
automation_execution
cicd
collaboration
attachments
api_artifacts
bulk
internal_jobs
jobs
notifications
webhooks
operations
```

Đây là điểm mạnh: breadth của product hiện tại đủ lớn để không cần tạo một dự án mới từ đầu.

## 3.3. Authorization đã đúng hướng

`backend/testing/src/core/auth.py` hiện có:

```text
SystemRole:
- USER
- ADMIN

ProjectRole:
- QA_LEAD
- TESTER
- BA
- DEVELOPER
- VIEWER
```

Và backend dùng permission catalogue khá rộng.

Giữ invariant:

```text
System ADMIN != QA_LEAD
```

Platform ADMIN không được tự động trở thành Project QA authority.

## 3.4. Test Planning hiện đã có nền tốt

`TestPlanCreate` hiện có:

```text
name
objective
scope_in
scope_out
environment / environment_id
entry_criteria
exit_criteria
risks
test_types
members
release / release_id
build / build_id
```

Có state:

```text
DRAFT
→ IN_REVIEW
→ APPROVED
→ ARCHIVED
```

Có clone.

Điều này đủ tốt để **mở rộng**, không cần thay TestPlan bằng entity mới.

## 3.5. Execution Context đã có

Có entity/index cho:
- Release;
- Build;
- TestEnvironment;
- DeviceMatrix.

TestRun freeze:
- test plan;
- suites;
- exact TestCaseVersion IDs;
- release/build/environment;
- device matrix snapshot.

Đây là behavior đúng hướng vì lịch sử execution phải reproducible.

## 3.6. Các entity nâng cao đã có

Database hiện đã có collections/indexes cho:
- DataSet/DataSetVersion;
- TestCaseTemplate;
- CoverageSnapshot;
- ChangeSet;
- ImpactAnalysis;
- MaintenanceProposal;
- RegressionRecommendation;
- notification subscriptions/rules/preferences;
- security test suggestions;
- performance plan drafts;
- webhooks;
- automation script drafts;
- project connectors;
- automation executions;
- CI/CD bindings/runs;
- collaboration sessions/conflicts;
- bulk operations;
- audit events;
- review comments;
- attachments.

Không build lại các capability này ở V5 nếu implementation hiện tại hoạt động đúng contract.

---

# 4. GAP P0-0 — CLEAN DOMAIN LEGACY TRƯỚC KHI NÓI HỆ THỐNG QA ĐÃ SẠCH

## 4.1. Vấn đề hiện tại

Trong `backend/testing/src/domain/schemas.py`, Requirement/Knowledge vẫn còn vocabulary cũ của education domain:

```text
teacher_material
official_textbook
curriculum

teacher_id
subject
grade

authority:
teacher
official
supplemental
reference
```

Đây là technical debt rõ ràng.

Nếu hệ thống là Test Management / Testing Document Platform thì metadata này:
- gây sai ngữ nghĩa domain;
- làm RAG authority ranking khó hiểu;
- có thể leak các field cũ sang frontend/API;
- làm khóa luận/demo trông như refactor chưa xong.

## 4.2. Build location

Backend:
```text
backend/testing/src/domain/schemas.py
backend/testing/src/api/requirements.py
backend/testing/src/api/analytics.py
backend/testing/src/services/project_knowledge.py
backend/testing/src/core/database.py
```

Frontend:
```text
frontend/features/testing/pages/workspace/RequirementsPage.jsx
frontend/features/testing/pages/workspace/KnowledgePage.jsx
```

Migration:
```text
scripts/migrate_testing_knowledge_metadata_v5.py
```

## 4.3. Canonical source types mới

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

## 4.4. Canonical authority

```text
APPROVED_SOURCE
CONTROLLED_SOURCE
PROJECT_REFERENCE
SUPPLEMENTAL
DRAFT
UNVERIFIED
```

## 4.5. Fields

Thay:

```text
teacher_id
subject
grade
```

bằng:

```text
owner_id
module
component
product_area
release_id
external_source_id
approval_status
approved_by
approved_at
source_version
effective_from
tags
```

## 4.6. Acceptance criteria

```text
[ ] Không còn teacher_material/official_textbook/curriculum trong testing domain.
[ ] Không còn teacher_id/subject/grade trong API QA.
[ ] Existing data migration không mất document.
[ ] RAG metadata được reindex.
[ ] Authority order dùng vocabulary testing.
[ ] Search/AI evidence vẫn trả đúng provenance.
```

**Priority:** P0.

---

# 5. GAP P0-1 — TEST POLICY & TEST STRATEGY

## 5.1. Vì sao cần

TMMi Level 2 bắt đầu từ `Test Policy and Strategy`.

Repo hiện có TestPlan, nhưng chưa có một artifact chuẩn để trả lời:

```text
Project này test theo nguyên tắc nào?
Test level nào bắt buộc?
Test type nào bắt buộc?
Risk-based testing được áp dụng thế nào?
Khi nào dùng manual/automation?
Automation target bao nhiêu?
Requirement nào cần security/performance?
Defect severity/prioritization policy là gì?
Suspension/resumption rule mặc định là gì?
Quality objective là gì?
```

Không nên nhét tất cả vào `Project.settings` dạng dict vì sẽ:
- khó version;
- khó review/approve;
- khó audit;
- không thể chứng minh plan nào đang theo strategy version nào.

## 5.2. Entity mới

```text
TestStrategy
├── _id
├── project_id
├── key
├── name
├── version
├── status
├── objective
├── test_levels[]
├── test_types[]
├── approach
├── risk_model
├── technique_policy
├── automation_policy
├── environment_policy
├── test_data_policy
├── defect_policy
├── review_policy
├── entry_criteria_defaults[]
├── exit_criteria_defaults[]
├── suspension_criteria[]
├── resumption_criteria[]
├── deliverables[]
├── reporting_policy
├── quality_objectives[]
├── standards_refs[]
├── tailoring_rationale
├── created_by
├── reviewed_by[]
├── approved_by
├── approved_at
├── revision
└── timestamps
```

## 5.3. State machine

```text
DRAFT
→ IN_REVIEW
→ APPROVED
→ SUPERSEDED
→ ARCHIVED
```

Approved strategy version immutable.

Update sau approval:

```text
Strategy v1 APPROVED
→ create Strategy v2 DRAFT
```

## 5.4. Sub-features

### STR-01 Repository
- list;
- search;
- filter status/version;
- active strategy badge;
- version history.

### STR-02 Strategy Editor
- objectives;
- test levels;
- test types;
- test approach;
- risk model;
- technique rules;
- automation policy;
- environment policy;
- entry/exit defaults;
- suspension/resumption;
- reporting cadence;
- deliverables.

### STR-03 Risk Model
Fields:
```text
probability scale
impact scale
risk exposure formula
thresholds
mandatory test depth
regression priority rules
```

### STR-04 Review
- assign reviewers;
- comments;
- findings;
- request changes.

### STR-05 Approve
- QA_LEAD only by default;
- immutable snapshot;
- audit.

### STR-06 Plan binding
TestPlan phải lưu:

```text
strategy_id
strategy_version
strategy_snapshot_hash
```

## 5.5. Permissions

```text
teststrategy.read
teststrategy.create
teststrategy.update
teststrategy.submit_review
teststrategy.review
teststrategy.approve
teststrategy.version.read
teststrategy.archive
```

Default:

| Role | Quyền |
|---|---|
| QA_LEAD | full + approve |
| TESTER | read + create/update draft + submit/review |
| BA | read + review |
| DEVELOPER | read |
| VIEWER | read |
| ADMIN | không mặc định truy cập project artifact |

## 5.6. Backend build

```text
backend/testing/src/api/test_strategy.py
backend/testing/src/services/test_strategy_service.py
backend/testing/src/repositories/test_strategy_repository.py
backend/testing/src/domain/test_strategy.py
```

Update:
```text
backend/testing/src/main.py
backend/testing/src/core/auth.py
backend/testing/src/core/function_ids.py
backend/testing/src/core/database.py
backend/testing/src/domain/schemas.py
```

## 5.7. Frontend build

```text
frontend/features/testing/pages/workspace/TestGovernancePage.jsx
frontend/features/testing/components/TestStrategyEditor.jsx
frontend/features/testing/components/RiskModelEditor.jsx
frontend/features/testing/components/StrategyVersionHistory.jsx
```

Route:
```text
/du-an/{project_id}/quan-tri-kiem-thu
```

## 5.8. APIs

```text
GET    /kiem-thu/du-an/{p}/chien-luoc
POST   /kiem-thu/du-an/{p}/chien-luoc
GET    /kiem-thu/chien-luoc/{id}
PATCH  /kiem-thu/chien-luoc/{id}
POST   /kiem-thu/chien-luoc/{id}/gui-ra-soat
POST   /kiem-thu/chien-luoc/{id}/yeu-cau-chinh-sua
POST   /kiem-thu/chien-luoc/{id}/phe-duyet
POST   /kiem-thu/chien-luoc/{id}/tao-phien-ban
POST   /kiem-thu/chien-luoc/{id}/luu-tru
```

## 5.9. Acceptance criteria

```text
[ ] Project có tối đa một active approved TestStrategy version.
[ ] Plan mới có thể bind exact StrategyVersion.
[ ] Approved strategy immutable.
[ ] Strategy change không rewrite plan cũ.
[ ] Risk model có version và explainable thresholds.
[ ] Permission tests đủ 5 project roles.
[ ] Audit mọi transition.
```

**Priority:** P0.

---

# 6. GAP P0-2 — MỞ RỘNG TEST PLAN CHO ĐÚNG TEST MANAGEMENT

## 6.1. Giữ TestPlan hiện tại, không rebuild

Các field hiện tại tốt và phải giữ.

Bổ sung:

```text
strategy_version_id
test_level
test_approach
assumptions[]
constraints[]
dependencies[]
stakeholders[]
responsibility_matrix[]
estimation
schedule
milestones[]
deliverables[]
tools[]
suspension_criteria[]
resumption_criteria[]
monitoring_metrics[]
quality_targets[]
risk_register[]
communication_plan
approval_history
baseline_hash
```

## 6.2. Estimation

```json
{
  "method": "expert_judgment|three_point|historical|custom",
  "planned_effort_hours": 120,
  "planned_people": 3,
  "planned_start": "...",
  "planned_end": "...",
  "notes": ""
}
```

Không cần financial budget module.

## 6.3. Responsibility matrix

```text
Activity                   Responsible      Reviewer
Requirement analysis       BA + Tester      QA Lead
Test design                Tester           QA Lead
Execution                  Tester           QA Lead
Defect fix                 Developer        -
Retest                     Tester           QA Lead
Release recommendation     QA Lead          Stakeholder
```

## 6.4. Suspension/resumption criteria

Ví dụ:

```text
Suspend:
- blocker environment incident;
- >30% critical test data unavailable;
- build cannot deploy;
- blocker defect prevents remaining scope.

Resume:
- environment restored and verified;
- replacement build registered;
- blocking incident closed/accepted.
```

## 6.5. TestPlan baseline

Current APPROVED record đang được khóa update khá tốt.

V5 thêm:

```text
approved_snapshot_hash
approved_at
approved_by
strategy_version_id
```

P1 mới cân nhắc `TestPlanVersion` nếu thật sự cần nhiều revision lịch sử.

**Priority:** P0.

---

# 7. GAP P0-3 — TEST ANALYSIS / TEST CONDITION

## 7.1. Gap hiện tại

Repo có:
- Requirement;
- Acceptance Criteria;
- Scenario;
- TestCase.

Nhưng chưa có layer formal trả lời câu hỏi ISTQB:

> **What to test?**

TestScenario hiện tại gần Test Condition nhưng đang dùng như high-level scenario và đi thẳng sang TestCase.

V5 chọn **không phá TestScenario**.

Thêm explicit `TestCondition`.

## 7.2. Canonical flow

```text
Test Basis
   ↓
Test Analysis
   ↓
Test Condition
   ↓
Test Scenario
   ↓
Test Case
```

## 7.3. Test Basis

Không cần entity duplicate file.

`TestBasisRef` có thể trỏ:

```text
RequirementVersion
AcceptanceCriterion
ApiOperation
Architecture/Design KnowledgeSource
BusinessRule
RiskRanking
Defect history
Regulation
```

## 7.4. TestCondition entity

```text
TestCondition
├── _id
├── project_id
├── condition_key
├── title
├── description_doc
├── basis_refs[]
├── coverage_item
├── test_level
├── test_type
├── risk
├── priority
├── technique_candidates[]
├── testability_status
├── analysis_findings[]
├── status
├── created_by
├── reviewed_by
├── revision
└── timestamps
```

## 7.5. Analysis findings

Tester/BA phải ghi được:

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
MISSING_NON_FUNCTIONAL_CRITERIA
```

Mỗi finding:

```text
severity
source_ref
description
suggestion
status OPEN/RESOLVED/ACCEPTED_RISK
resolved_by
resolution_ref
```

## 7.6. Sub-features

### TAN-01 Analysis workspace
- chọn Requirement/RequirementVersion;
- hiển thị basis;
- AI + rule engine gợi ý condition;
- tester tạo condition thủ công.

### TAN-02 Condition extraction
- functional behavior;
- negative behavior;
- boundaries;
- state transitions;
- permissions;
- integrations;
- data;
- error handling;
- non-functional.

### TAN-03 Testability review
- phát hiện requirement không test được;
- thiếu measurable expected behavior.

### TAN-04 Coverage items
Ví dụ:
```text
REQ-AUTH-01
→ valid credential
→ invalid credential
→ locked account
→ expired password
→ permission denied
```

### TAN-05 Prioritize
Dựa:
- requirement risk;
- business priority;
- defect history;
- change volatility.

### TAN-06 Approve analysis
Condition được review trước khi dùng làm official design source nếu project policy yêu cầu.

### TAN-07 Trace
```text
RequirementVersion
→ TestCondition
→ TestScenario
→ TestCaseVersion
```

## 7.7. AI role

AI được:
- suggest conditions;
- detect missing testability;
- suggest techniques;
- suggest risk.

AI không được:
- tự approve condition;
- tự sửa Requirement baseline.

## 7.8. Permissions

```text
testcondition.read
testcondition.create
testcondition.update
testcondition.review
testcondition.approve
testcondition.archive
testanalysis.run_ai
testanalysis.resolve_finding
```

## 7.9. Backend

```text
backend/testing/src/api/test_analysis.py
backend/testing/src/services/test_analysis_service.py
backend/testing/src/repositories/test_condition_repository.py
backend/testing/src/domain/test_analysis.py
```

Update traceability service/schema.

## 7.10. Frontend

```text
frontend/features/testing/pages/workspace/TestAnalysisPage.jsx
frontend/features/testing/components/TestBasisPanel.jsx
frontend/features/testing/components/TestConditionTable.jsx
frontend/features/testing/components/TestConditionEditor.jsx
frontend/features/testing/components/TestabilityFindingsPanel.jsx
```

Route:
```text
/du-an/{project_id}/phan-tich-kiem-thu
```

## 7.11. Acceptance criteria

```text
[ ] Mỗi TestCondition phải có ít nhất một basis_ref.
[ ] Cross-project ref bị reject.
[ ] Requirement baseline thay đổi không rewrite condition history.
[ ] Condition có priority/risk.
[ ] AI suggestion chỉ là candidate.
[ ] Coverage matrix có thể hiển thị Req→Condition→Case.
[ ] Uncovered condition được report.
```

**Priority:** P0.

---

# 8. GAP P0-4 — TEST MONITORING & CONTROL

## 8.1. Gap hiện tại

Dashboard hiện có:
- coverage;
- current runs;
- result count;
- open defects;
- stale tests;
- impact/proposal backlog.

Đây là **analytics**.

Nhưng Test Monitoring & Control cần thêm:

```text
PLAN
vs
ACTUAL
→ deviation
→ threshold
→ control action
→ stakeholder status report
```

## 8.2. Entity

### TestMonitoringSnapshot

```text
TestMonitoringSnapshot
├── _id
├── project_id
├── test_plan_id
├── release_id
├── snapshot_at
├── plan_revision
├── planned
├── actual
├── metrics
├── exit_criteria_evaluation[]
├── deviations[]
├── risks[]
├── blockers[]
├── quality_gate_status
├── source_fingerprint
└── created_by/system
```

### TestControlAction

```text
TestControlAction
├── _id
├── project_id
├── plan_id
├── snapshot_id
├── type
├── title
├── description
├── owner_id
├── due_at
├── priority
├── status
├── decision_reason
├── evidence_refs[]
└── audit
```

## 8.3. Metrics P0

### Progress
```text
planned_test_count
executed_test_count
execution_percent
not_run
in_progress
pass
fail
blocked
skipped
not_applicable
```

### Coverage
```text
requirement_coverage
acceptance_criteria_coverage
test_condition_coverage
risk_coverage
```

### Defect
```text
open_blocker
open_critical
new_defects
resolved
reopened
defect_aging
```

### Change/Maintenance
```text
changed_requirements
stale_testcases
impact_pending
proposal_pending
```

### Schedule
```text
planned_start
planned_end
actual_start
expected_completion
schedule_variance
```

### Effort
Chỉ khi team nhập effort:
```text
planned_effort
actual_effort
effort_variance
```

## 8.4. Exit criteria evaluator

Không để QA Lead nhìn dashboard rồi tự nhẩm.

Mỗi criterion:

```json
{
  "criterion": "Không có Blocker mở",
  "type": "OPEN_DEFECT_MAX",
  "threshold": 0,
  "actual": 1,
  "status": "FAIL",
  "evidence_refs": ["BUG-..."]
}
```

Supported rule examples:

```text
EXECUTION_PERCENT_MIN
PASS_RATE_MIN
OPEN_BLOCKER_MAX
OPEN_CRITICAL_MAX
REQUIREMENT_COVERAGE_MIN
CONDITION_COVERAGE_MIN
STALE_TESTCASE_MAX
REQUIRED_RUNS_COMPLETED
CUSTOM_MANUAL_GATE
```

## 8.5. Control actions

```text
PAUSE_EXECUTION
RESUME_EXECUTION
REQUEST_RETEST
CREATE_ADDITIONAL_TEST_SCOPE
REQUEST_NEW_BUILD
BLOCK_RELEASE
ACCEPT_RISK
ESCALATE_DEFECT
REPRIORITIZE_REGRESSION
EXTEND_TEST_WINDOW
```

Nguyên tắc:

> Không mutate scope của một TestRun đã freeze. Nếu cần thêm scope, tạo run/scope revision mới.

## 8.6. State

ControlAction:

```text
OPEN
→ IN_PROGRESS
→ DONE
→ CANCELLED
```

## 8.7. Permissions

```text
testmonitor.read
testmonitor.snapshot.create
testmonitor.control.create
testmonitor.control.assign
testmonitor.control.update
testmonitor.exit_criteria.override
testmonitor.report.create
```

Default:
- QA_LEAD: full.
- TESTER: read, create observation/control suggestion.
- BA: read.
- DEVELOPER: read relevant defect/control actions.
- VIEWER: read.
- Override exit criterion: QA_LEAD only + reason + audit.

## 8.8. Backend

```text
backend/testing/src/api/test_monitoring.py
backend/testing/src/services/test_monitoring_service.py
backend/testing/src/services/exit_criteria_service.py
backend/testing/src/repositories/test_monitoring_repository.py
```

## 8.9. Frontend

```text
frontend/features/testing/pages/workspace/MonitoringPage.jsx
frontend/features/testing/components/TestProgressBoard.jsx
frontend/features/testing/components/PlanVsActualPanel.jsx
frontend/features/testing/components/ExitCriteriaPanel.jsx
frontend/features/testing/components/TestControlActionPanel.jsx
frontend/features/testing/components/QualityGateBadge.jsx
```

Route:
```text
/du-an/{project_id}/giam-sat-kiem-thu
```

## 8.10. Acceptance criteria

```text
[ ] Snapshot reproducible từ exact plan/release/run data.
[ ] Exit criteria deterministic.
[ ] Override bắt buộc reason.
[ ] Blocker threshold fail hiển thị release risk.
[ ] Historical snapshot không đổi khi result sau đó đổi/correct.
[ ] Control action có owner/status/due date.
[ ] Monitoring không cho sửa frozen TestRun scope.
```

**Priority:** P0.

---

# 9. GAP P0-5 — TEST STATUS REPORT

## 9.1. Tại sao không dùng mỗi Dashboard

Dashboard là live view.
Status Report là **point-in-time communication artifact**.

Một QA Lead cần có thể nói:

```text
Status report ngày 10/09
- kế hoạch nào
- build nào
- scope nào
- tiến độ
- coverage
- defects
- deviations
- risks
- control actions
- recommendation
```

Và tuần sau report cũ vẫn giữ nguyên.

## 9.2. Entity

```text
TestStatusReport
├── _id
├── project_id
├── test_plan_id
├── release_id
├── build_id
├── reporting_period
├── snapshot_id
├── executive_summary
├── progress_summary
├── coverage_summary
├── defect_summary
├── deviations[]
├── blockers[]
├── risks[]
├── control_actions[]
├── forecast
├── recommendation
├── distribution[]
├── status
├── created_by
├── approved_by
└── timestamps
```

## 9.3. Recommendation enum

```text
ON_TRACK
AT_RISK
BLOCKED
CONTINUE_TESTING
READY_WITH_RISK
NOT_READY
```

## 9.4. Features

```text
Generate from snapshot
Edit narrative
Attach evidence
Review
Approve/publish
Export PDF/DOCX/CSV as applicable
History
Compare status reports
```

## 9.5. Build

Backend:
```text
backend/testing/src/api/test_status_reports.py
backend/testing/src/services/test_status_report_service.py
```

Frontend:
```text
frontend/features/testing/components/TestStatusReportPanel.jsx
```

Đặt trong Monitoring/Reports, không cần thêm top-level nav riêng.

**Priority:** P0/P1 boundary; V5 khuyến nghị P0 nếu mục tiêu là quy trình enterprise.

---

# 10. GAP P0-6 — TEST COMPLETION / TEST CLOSURE

## 10.1. Gap hiện tại

Current TestRun có COMPLETE.
Release có close.

Nhưng:

```text
Run COMPLETED
!=
Testing COMPLETED
```

Test Completion cần tổng kết toàn test scope.

## 10.2. Entity

```text
TestCompletionReport
├── _id
├── project_id
├── test_plan_id
├── release_id
├── strategy_version_id
├── scope_snapshot
├── completed_run_ids[]
├── execution_summary
├── coverage_summary
├── defect_summary
├── unresolved_items[]
├── residual_risks[]
├── exit_criteria_evaluation[]
├── deviations[]
├── testware_handover[]
├── archived_artifacts[]
├── environment_closure[]
├── lessons_learned[]
├── improvement_actions[]
├── recommendation
├── sign_offs[]
├── status
├── revision
└── timestamps
```

## 10.3. State

```text
DRAFT
→ IN_REVIEW
→ APPROVED
→ CLOSED
```

Không chỉnh sửa APPROVED report in-place.

## 10.4. Completion checklist

### Scope
- planned vs executed;
- omitted cases + reasons;
- scope changes.

### Coverage
- requirement;
- condition;
- risk;
- API;
- non-functional if applicable.

### Defects
- closed;
- deferred;
- accepted risk;
- open critical/blocker.

### Testware
- TestCases archived/current;
- reusable datasets;
- automation scripts;
- reports/evidence;
- environment state.

### Lessons learned
- what worked;
- what failed;
- recurring blockers;
- improvement proposal.

### Sign-off
- QA Lead;
- optional BA/Product/Project stakeholder.

## 10.5. Release gate

Project policy:

```text
require_completion_report_before_release_close = true|false
```

Nếu true:

```text
Release ACTIVE
→ close
→ require APPROVED TestCompletionReport
```

## 10.6. Backend

```text
backend/testing/src/api/test_completion.py
backend/testing/src/services/test_completion_service.py
backend/testing/src/repositories/test_completion_repository.py
```

## 10.7. Frontend

```text
frontend/features/testing/pages/workspace/CompletionPage.jsx
frontend/features/testing/components/CompletionReportEditor.jsx
frontend/features/testing/components/ResidualRiskPanel.jsx
frontend/features/testing/components/LessonsLearnedPanel.jsx
frontend/features/testing/components/TestwareHandoverPanel.jsx
```

Có thể đặt dưới:
```text
Reports → Completion
```

không bắt buộc top-level nav.

## 10.8. Acceptance criteria

```text
[ ] Completion report trỏ exact plan/release/build/run versions.
[ ] Report giữ snapshot.
[ ] Exit criteria được đánh giá lại.
[ ] Open critical defect được liệt kê.
[ ] Residual risk có owner/acceptance.
[ ] Release close gate theo policy.
[ ] Lessons learned không bị mất sau archive project.
```

**Priority:** P0.

---

# 11. GAP P1-1 — FORMAL PEER REVIEW, KHÔNG CHỈ COMMENT

## 11.1. Current repo

`reviews.py` hiện đã có:
- create comment;
- reply;
- anchor;
- update/delete;
- resolve;
- reopen;
- audit.

Giữ nguyên.

Nhưng comment thread không phải một **formal review session**.

## 11.2. Entity

### ReviewSession

```text
ReviewSession
├── _id
├── project_id
├── review_type
├── artifact_type
├── artifact_id
├── artifact_version_id
├── objective
├── checklist_version
├── moderator_id
├── author_id
├── reviewers[]
├── scribe_id
├── planned_at
├── started_at
├── completed_at
├── decision
├── status
└── metrics
```

### ReviewFinding

```text
ReviewFinding
├── review_session_id
├── category
├── severity
├── anchor
├── description
├── suggested_action
├── owner_id
├── status
└── resolution
```

## 11.3. Review types

```text
REQUIREMENT_REVIEW
TEST_STRATEGY_REVIEW
TEST_PLAN_REVIEW
TEST_CONDITION_REVIEW
TEST_CASE_REVIEW
IMPACT_REVIEW
COMPLETION_REVIEW
```

## 11.4. Findings

```text
MAJOR
MINOR
QUESTION
IMPROVEMENT
```

Category:
```text
CORRECTNESS
COMPLETENESS
CONSISTENCY
TESTABILITY
TRACEABILITY
SECURITY
PERFORMANCE
MAINTAINABILITY
```

## 11.5. Decision

```text
ACCEPTED
ACCEPTED_WITH_ACTIONS
REWORK_REQUIRED
REJECTED
```

## 11.6. Backend/Frontend

Backend:
```text
backend/testing/src/api/review_sessions.py
backend/testing/src/services/review_session_service.py
```

Frontend:
```text
frontend/features/testing/components/FormalReviewPanel.jsx
frontend/features/testing/components/ReviewChecklist.jsx
frontend/features/testing/components/ReviewFindingsTable.jsx
```

Tích hợp vào detail pages thay vì tạo app riêng.

**Priority:** P1.

---

# 12. GAP P1-2 — TEST MEASUREMENT

## 12.1. Vấn đề

Current analytics có metric.
Nhưng mature process cần biết:

```text
metric này đo để làm gì?
formula gì?
data source gì?
target gì?
threshold gì?
period gì?
owner ai?
```

Không được để mỗi page tự tính một metric khác nhau.

## 12.2. Entity

```text
MeasurementDefinition
├── key
├── name
├── objective
├── formula
├── unit
├── data_sources[]
├── dimensions[]
├── aggregation
├── period
├── target
├── warning_threshold
├── critical_threshold
├── owner_role
├── status
└── version
```

```text
MeasurementSnapshot
├── measurement_definition_version
├── project_id
├── release_id
├── value
├── dimensions
├── source_fingerprint
└── measured_at
```

## 12.3. Metric catalogue P1

```text
Requirement Coverage
Acceptance Criterion Coverage
Test Condition Coverage
Execution Progress
Pass Rate
Blocked Rate
Defect Reopen Rate
Critical Defect Aging
Mean Time to Retest
Stale Test Ratio
Requirement Volatility
Impact Proposal Acceptance Rate
Regression Effectiveness
Automation Coverage
Automation Pass Stability
Escaped Defect Rate        -- chỉ khi có production incident data
Defect Removal Efficiency  -- chỉ khi denominator/source đủ
```

Không fake metric khi không có data.

## 12.4. Backend

```text
backend/testing/src/api/measurements.py
backend/testing/src/services/measurement_service.py
backend/testing/src/domain/measurement.py
```

## 12.5. Frontend

Mở rộng:
```text
frontend/features/testing/pages/workspace/ReportsPage.jsx
```

Components:
```text
QualityMetricCard
MetricDefinitionPanel
MetricTrendChart
ThresholdStatus
```

**Priority:** P1.

---

# 13. GAP P1-3 — PRODUCT QUALITY EVALUATION / RELEASE QUALITY GATE

## 13.1. Mục tiêu

Biến dữ liệu test thành quyết định có kiểm soát.

Entity:

```text
ProductQualityEvaluation
├── project_id
├── release_id
├── build_id
├── measurement_snapshot_refs[]
├── exit_criteria_snapshot
├── critical_risks[]
├── unresolved_defects[]
├── waivers[]
├── recommendation
├── rationale
├── evidence_refs[]
├── reviewed_by[]
├── approved_by
└── status
```

## 13.2. Recommendation

```text
GO
GO_WITH_RISK
NO_GO
MORE_TESTING_REQUIRED
```

AI có thể:
- summarize evidence;
- point out conflicting indicators.

AI không được:
- quyết định GO/NO_GO một mình.

## 13.3. Waiver

```text
metric/criterion
reason
risk
owner
expiry
approved_by
evidence
```

## 13.4. UI

```text
Reports → Release Quality
```

Panel:
- exit gates;
- trends;
- unresolved defects;
- residual risk;
- recommendation;
- sign-off.

**Priority:** P1.

---

# 14. GAP P1-4 — DEFECT PREVENTION / ROOT CAUSE ANALYSIS

## 14.1. Current gap

Defect workflow đã tốt:
- create;
- triage;
- assign;
- resolve;
- retest;
- reopen;
- duplicate.

Nhưng chưa có process hỗ trợ học từ defect.

## 14.2. Bổ sung Defect

Fields P1:

```text
root_cause_category
root_cause_detail
injected_phase
detected_phase
escape_reason
prevention_candidate
```

Category:
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
UNKNOWN
```

## 14.3. CausalAnalysis entity

Tạo khi:
- Blocker/Critical;
- defect reopen nhiều lần;
- duplicate cluster lớn;
- recurring pattern.

```text
CausalAnalysis
├── defect_ids[]
├── problem_statement
├── evidence
├── root_causes[]
├── contributing_factors[]
├── five_whys
├── corrective_actions[]
├── preventive_actions[]
├── owner
├── due_dates
├── effectiveness_review_at
└── status
```

## 14.4. CAPA state

```text
OPEN
→ IN_PROGRESS
→ IMPLEMENTED
→ EFFECTIVENESS_REVIEW
→ CLOSED
```

## 14.5. AI

AI:
- cluster patterns;
- suggest root-cause hypotheses;
- retrieve similar historical defect;
- suggest missing TestCondition/TestCase.

Human:
- confirm root cause;
- approve preventive action.

## 14.6. Build

Backend:
```text
backend/testing/src/api/defect_prevention.py
backend/testing/src/services/causal_analysis_service.py
```

Frontend:
```text
frontend/features/testing/components/CausalAnalysisPanel.jsx
frontend/features/testing/components/PreventiveActionTable.jsx
```

**Priority:** P1.

---

# 15. GAP P2-1 — TEST PROCESS OPTIMIZATION

Không bắt buộc cho MVP/khóa luận.

Entity:

```text
ProcessImprovementProposal
├── source
├── observed_problem
├── baseline_metric
├── proposed_change
├── expected_effect
├── experiment_scope
├── owner
├── status
├── result_metrics
└── decision
```

Flow:

```text
PROPOSED
→ APPROVED_EXPERIMENT
→ RUNNING
→ EVALUATED
→ ADOPTED | REJECTED
```

Sources:
- lessons learned;
- RCA;
- repeated control actions;
- AI analytics;
- process metrics.

Đây mới là nơi hợp lý để nói tới TMMi optimization support.

**Priority:** P2.

---

# 16. GAP P2-2 — STATISTICAL QUALITY CONTROL

Chỉ build khi có đủ lịch sử data.

Không cần cho MVP.

Feature:
- control chart;
- baseline distribution;
- outlier detection;
- process stability;
- alert when metric exceeds control limit.

Không dùng AI-generated number.

Formula deterministic.

**Priority:** P2/Research extension.

---

# 17. TEST ENVIRONMENT — HIỆN TẠI TỐT NHƯNG CẦN THÊM ENVIRONMENT INCIDENT

## 17.1. Current strength

Repo đã có:
- TestEnvironment;
- availability;
- capabilities;
- secret refs;
- DeviceMatrix;
- run binding.

## 17.2. Add EnvironmentIncident

TMMi Test Environment nhấn mạnh việc quản lý incident môi trường.

```text
EnvironmentIncident
├── environment_id
├── build_id
├── observed_at
├── severity
├── type
├── description
├── affected_run_ids[]
├── evidence_refs[]
├── owner_id
├── status
├── resolution
└── downtime
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
OTHER
```

State:
```text
OPEN
→ INVESTIGATING
→ RESOLVED
→ CLOSED
```

Integrate Monitoring:
- blocker incident can fail exit criteria or pause execution;
- downtime tracked.

Build:
```text
backend/testing/src/api/environment_incidents.py
frontend/features/testing/components/EnvironmentIncidentPanel.jsx
```

**Priority:** P1.

---

# 18. NON-FUNCTIONAL TESTING — KHÔNG BIẾN THÀNH TOOL KHỔNG LỒ

Repo hiện đã có:
- security test suggestion;
- performance plan draft;
- device matrix;
- automation script generation.

V5 không yêu cầu tự viết full security scanner/JMeter clone.

Đủ hợp lý:

## P1
- Security Test Plan artifact;
- Performance Test Plan artifact;
- test cases/conditions;
- external execution evidence import;
- result summary;
- traceability.

## P2
Adapters:
```text
k6
JMeter
OWASP ZAP result import
Playwright performance measurements
```

Không chạy destructive security testing mặc định.

---

# 19. ROLE ALIGNMENT SAU V5

## 19.1. QA_LEAD

Core:
```text
Test Strategy approval
Test Plan approval
Test Monitoring & Control
Quality Gate
Test Status Report approval
Test Completion approval
Release recommendation
Impact/Proposal final approval
Defect triage/closure policy
Measurement governance
```

## 19.2. TESTER

Core:
```text
Test Analysis
TestCondition
Scenario
TestCase
Test Data
Test Suite
Execution
Evidence
Defect
Retest
Impact review
Monitoring observations
Control action suggestions
Completion evidence contribution
```

Không mặc định:
```text
GO/NO-GO
Strategy final approval
Completion final approval
Quality gate override
```

## 19.3. BA / PRODUCT

```text
Requirement/Test Basis
Acceptance Criteria
Business Rules
Testability review
TestCondition semantic review
Trace review
Requirement change review
Completion residual business risk review
```

## 19.4. DEVELOPER

```text
read Test Basis/TestCase
formal technical review
assigned Defect
fix evidence
RCA contribution
environment/CI evidence read
```

Không ghi QA PASS/FAIL.

## 19.5. VIEWER

Read-only theo ProjectMembership/policy.

## 19.6. SYSTEM ADMIN

Platform only:
- users;
- platform config;
- providers/integrations;
- operations;
- system audit;
- service health.

Không mặc định duyệt project test artifact.

---

# 20. ROLE PERMISSIONS MỚI V5

```text
teststrategy.read
teststrategy.create
teststrategy.update
teststrategy.submit_review
teststrategy.review
teststrategy.approve
teststrategy.archive
teststrategy.version.read

testcondition.read
testcondition.create
testcondition.update
testcondition.review
testcondition.approve
testcondition.archive
testanalysis.run_ai
testanalysis.resolve_finding

testmonitor.read
testmonitor.snapshot.create
testmonitor.control.create
testmonitor.control.assign
testmonitor.control.update
testmonitor.exit_criteria.override

teststatusreport.read
teststatusreport.create
teststatusreport.update
teststatusreport.review
teststatusreport.approve
teststatusreport.export

testcompletion.read
testcompletion.create
testcompletion.update
testcompletion.review
testcompletion.approve
testcompletion.close

reviewsession.read
reviewsession.create
reviewsession.update
reviewsession.finding.manage
reviewsession.complete

measurement.read
measurement.manage
measurement.snapshot.create

qualityevaluation.read
qualityevaluation.create
qualityevaluation.review
qualityevaluation.approve
qualityevaluation.waiver.approve

causalanalysis.read
causalanalysis.create
causalanalysis.update
causalanalysis.approve
preventionaction.manage

environmentincident.read
environmentincident.create
environmentincident.update
environmentincident.close
```

Update:
```text
backend/testing/src/core/auth.py
backend/testing/src/core/function_ids.py
```

Mọi endpoint mới phải có x-function-id.

---

# 21. NAVIGATION V5

Current navigation đang thiên artifact:

```text
Requirements
Test Design
Traceability
Changes
Execution
AI Review
Defects
Reports
Knowledge
Settings
```

V5 khuyến nghị:

```text
Project
├── Overview
├── Requirements
├── Test Analysis           NEW
├── Test Design
├── Planning & Execution
│   ├── Strategy            NEW
│   ├── Test Plans
│   ├── Suites
│   ├── Runs
│   ├── Environments
│   └── Monitoring          NEW
├── Traceability
├── Change & Maintenance
├── AI Review
├── Defects
├── Reports
│   ├── Status Reports      NEW
│   ├── Completion          NEW
│   ├── Coverage
│   ├── Execution
│   ├── Defects
│   ├── Quality Evaluation  NEW P1
│   └── Measurements        NEW P1
├── Knowledge
└── Settings
```

Không tạo 20 top-level menu.

---

# 22. BACKEND REFACTOR BẮT BUỘC TRƯỚC KHI FILE TIẾP TỤC PHÌNH

Current audit thấy các file rất lớn:
- `requirements.py` khoảng 124 KB;
- `execution.py` khoảng 82 KB;
- `changes.py` khoảng 61 KB.

Frontend:
- `RequirementsPage.jsx` khoảng 91 KB;
- `TestDesignPage.jsx` khoảng 90 KB;
- `ExecutionPage.jsx` khoảng 52 KB.

Không nên thêm V5 trực tiếp vào các file này.

## 22.1. Target backend structure

```text
backend/testing/src/
├── api/
│   ├── requirements/
│   │   ├── documents.py
│   │   ├── requirements.py
│   │   ├── versions.py
│   │   └── transformations.py
│   ├── test_design/
│   │   ├── conditions.py
│   │   ├── scenarios.py
│   │   ├── testcases.py
│   │   ├── suites.py
│   │   └── templates.py
│   ├── execution/
│   │   ├── planning.py
│   │   ├── runs.py
│   │   ├── results.py
│   │   ├── defects.py
│   │   └── environments.py
│   ├── monitoring/
│   ├── completion/
│   └── measurement/
├── services/
├── repositories/
└── domain/
```

Không cần microservice mới.

Giữ `backend/testing` là một bounded context.

## 22.2. Rule

```text
API router
→ auth/input
→ domain service
→ repository
```

API file không chứa hàng trăm dòng business logic.

AI service không được ghi trực tiếp Testing MongoDB.

---

# 23. FRONTEND REFACTOR

Không tiếp tục nhét thêm JSX vào page 90 KB.

Ví dụ Requirement:

```text
RequirementsPage
├── RequirementListPanel
├── RequirementDetailPanel
├── RequirementEditor
├── RequirementImportDialog
├── ExtractionReviewPanel
├── RequirementVersionPanel
├── RequirementDiffPanel
├── TestabilityPanel
└── hooks/
```

Test Design:

```text
TestDesignPage
├── ConditionWorkspace
├── ScenarioRepository
├── TestCaseRepository
├── TestCaseEditor
├── TemplatePanel
├── TestDataPanel
└── hooks/
```

Execution:

```text
ExecutionPage
├── StrategyPanel
├── PlanPanel
├── EnvironmentPanel
├── SuitePanel
├── RunPanel
├── Runner
├── MonitoringPanel
└── hooks/
```

Rule:
- page = orchestration;
- components = presentation;
- hooks/services = data fetching/mutation;
- permission helper = centralized;
- state transition button = centralized domain UI rule.

---

# 24. REPO-LEVEL DEVTESTOPS / QUALITY GATE

## 24.1. Current gap

Tại baseline audit:
- không thấy `.github/workflows`;
- `main` không protected;
- required status checks đang off.

Một product có CI/CD feature bên trong nhưng source repo lại merge không gate thì chưa hợp lý với tư duy DevTestOps.

## 24.2. Build `.github/workflows/ci.yml`

Jobs:

```text
backend-lint
backend-unit
testing-integration
ai-tool-contract
frontend-lint
frontend-unit
frontend-e2e-smoke
security-static-check
docker-compose-config
function-id-closure
```

## 24.3. Backend gate

```bash
ruff check
pytest backend/testing/tests
pytest backend/ai/tests
```

Nếu test quá dài:
- PR: fast P0 contract/smoke;
- nightly: full integration/benchmark.

## 24.4. Frontend gate

```text
eslint
unit/component tests
Playwright smoke
role permission smoke
```

## 24.5. Function-ID closure CI

Script:

```text
scripts/check_testing_function_registry.py
```

Check:
```text
every route has function ID where required
every function ID exists in permission catalogue
no duplicate function ID
every mutation has permission
every high-impact endpoint has audit
```

## 24.6. Branch protection

Recommended:
- PR required;
- CI required;
- no direct merge when gate fails;
- at least one review if possible.

**Priority:** P0 repository hardening.

---

# 25. CURRENT TEST PROCESS COVERAGE — AUDIT ESTIMATE

Đây là **architecture/process-support estimate**, không phải code coverage và không phải TMMi appraisal.

| ISTQB Activity | Hiện tại | Kết luận |
|---|---:|---|
| Test Planning | 70% | Có Plan/entry/exit/risk/release/env, thiếu Strategy/estimate/schedule/reporting detail |
| Monitoring & Control | 35% | Có dashboard, chưa có plan-vs-actual/deviation/control/status snapshot |
| Test Analysis | 45% | Có Requirement/Scenario/AI lint, chưa có formal Test Basis/TestCondition |
| Test Design | 90% | TestCase/Scenario/data/template/technique/AI khá mạnh |
| Test Implementation | 85% | Suite/data/env/automation có nhiều capability |
| Test Execution | 90% | Run snapshot/result/evidence/defect/retest tốt |
| Test Completion | 25% | Run complete/release close có, thiếu closure report/lessons learned/handover |

## 25.1. TMMi process support estimate

Không được gọi đây là "TMMi level đạt được".

| Process Area | Support hiện tại | V5 |
|---|---|---|
| Test Policy & Strategy | RED | P0 Strategy |
| Test Planning | YELLOW/GREEN | P0 extend |
| Test Monitoring & Control | RED/YELLOW | P0 |
| Test Design & Execution | GREEN | giữ/hardening |
| Test Environment | GREEN | P1 incident management |
| Lifecycle Integration | GREEN | đã có requirement/change/CI/connectors |
| Non-functional Testing | YELLOW | formalize artifact + external adapters |
| Peer Reviews | YELLOW | P1 ReviewSession |
| Test Measurement | YELLOW | P1 MeasurementDefinition |
| Product Quality Evaluation | RED/YELLOW | P1 Quality Gate |
| Defect Prevention | RED | P1 RCA/CAPA |
| Quality Control | RED | P2 statistical |
| Test Process Optimization | RED | P2 improvement loop |

---

# 26. V5 SIGNATURE WORKFLOW

Sau khi build P0:

```text
PROJECT
  ↓
APPROVED TEST STRATEGY
  ↓
REQUIREMENT / TEST BASIS
  ↓
TESTABILITY REVIEW
  ↓
TEST CONDITIONS
  ↓
TEST SCENARIO
  ↓
TEST CASE
  ↓
TRACEABILITY
  ↓
APPROVED TEST PLAN
  ↓
RELEASE + BUILD + ENVIRONMENT
  ↓
TEST SUITE
  ↓
TEST RUN
  ↓
EXECUTION
  ↓
DEFECT / RETEST
  ↓
MONITORING SNAPSHOT
  ↓
EXIT CRITERIA EVALUATION
  ↓
CONTROL ACTIONS
  ↓
STATUS REPORT
  ↓
REQUIREMENT CHANGE
  ↓
CHANGE FACT
  ↓
IMPACT ANALYSIS
  ↓
AI MAINTENANCE PROPOSAL
  ↓
HUMAN APPROVAL
  ↓
TESTCASE VERSION NEW
  ↓
REGRESSION RUN
  ↓
PRODUCT QUALITY EVALUATION
  ↓
TEST COMPLETION REPORT
  ↓
RELEASE CLOSE
  ↓
LESSONS LEARNED / RCA / IMPROVEMENT
```

Đây là workflow vừa:
- bám test process quốc tế;
- tận dụng code hiện có;
- vẫn giữ novelty change-aware Agentic AI;
- không làm mất bản chất quản lý/soạn thảo tài liệu.

---

# 27. AI TRONG V5 — DÙNG Ở ĐÂU VÀ KHÔNG DÙNG Ở ĐÂU

## 27.1. AI hợp lý

```text
Requirement lint
Testability finding suggestion
TestCondition suggestion
Test technique suggestion
TestCase generation
Duplicate detection
Project Q&A
Semantic retrieval
Requirement diff semantic classification
Impact analysis
Maintenance proposal
Regression recommendation
Bug trace suggestion
RCA hypothesis
Status/Completion narrative draft
Lessons-learned clustering
```

## 27.2. Deterministic

Không giao LLM:
```text
coverage %
pass rate
exit criterion threshold
permission
state transition
version creation
run snapshot
defect state
release state
metric formulas
```

## 27.3. Human-only

```text
approve Strategy
approve Requirement baseline
approve TestCase version
override quality gate
GO/NO-GO recommendation acceptance
close critical Defect by policy
apply maintenance proposal
approve Completion Report
accept residual risk
```

## 27.4. Agentic flow

Không chạy ReAct cho CRUD.

Chỉ dùng multi-step agent khi cần nhiều evidence/tool:

```text
Requirement changed
→ inspect change facts
→ inspect direct trace
→ semantic candidate retrieval
→ inspect TestCase versions
→ inspect bug/execution history
→ technique/risk rules
→ classify impact
→ proposal
→ human gate
```

---

# 28. QUALITY DOCUMENT RELATIONSHIP

Để giữ đúng đề tài "quản lý và soạn thảo tài liệu", toàn product có thể trình bày bằng document graph:

```text
RequirementDocument
    ↓
RequirementVersion
    ↓
TestCondition
    ↓
TestScenario
    ↓
TestCaseVersion
    ↓
TestPlan / TestSuite
    ↓
TestRun Evidence
    ↓
Defect
    ↓
TestStatusReport
    ↓
TestCompletionReport
```

Cross-cutting:

```text
TraceLink
ReviewSession
Attachment
AuditEvent
ChangeSet
ImpactAnalysis
AIProposal
MeasurementSnapshot
```

Như vậy sản phẩm không phải "một mớ module tester", mà là:

> **structured intelligent testing document lifecycle platform**.

---

# 29. P0 BUILD ORDER — KHÔNG BUILD LAN MAN

## PR-V5-01 — Domain cleanup
- remove education vocabulary;
- migration + RAG reindex;
- tests.

## PR-V5-02 — Test Strategy
- entity/API/permission/state;
- TestPlan binding;
- frontend editor.

## PR-V5-03 — Test Plan extension
- estimation;
- schedule;
- suspension/resumption;
- reporting/quality targets.

## PR-V5-04 — Test Analysis
- TestBasisRef;
- TestCondition;
- testability findings;
- trace integration.

## PR-V5-05 — Monitoring
- snapshot;
- plan-vs-actual;
- exit criteria evaluator;
- control actions.

## PR-V5-06 — Status Report
- immutable snapshot report;
- export.

## PR-V5-07 — Completion
- completion report;
- residual risk;
- lessons learned;
- release close gate.

## PR-V5-08 — Architecture refactor
Có thể bắt đầu song song từ PR-01, nhưng chốt trước khi file tiếp tục phình.

## PR-V5-09 — CI quality gates
- GitHub Actions;
- function ID closure;
- branch protection.

Sau 9 PR này, lifecycle P0 mới đủ chắc để demo như một quy trình QA trưởng thành.

---

# 30. P1 BUILD ORDER

```text
PR-V5-10 Formal ReviewSession
PR-V5-11 Measurement Definition/Snapshot
PR-V5-12 Product Quality Evaluation
PR-V5-13 Defect RCA / CAPA
PR-V5-14 Environment Incident
PR-V5-15 NFR artifact normalization
```

---

# 31. P2 — KHÔNG BLOCK KHÓA LUẬN

```text
Process Improvement experiments
Statistical process/quality control
Advanced external performance/security adapters
Advanced portfolio-level test governance
```

Không build Test Organization/Training Program như TMMi enterprise HR process.
Đó không phù hợp core product.

---

# 32. ENDPOINT/API CONVENTION

Current API dùng tiếng Việt.
Không bắt buộc rewrite toàn bộ chỉ để "quốc tế".

Ưu tiên:
- contract ổn định;
- OpenAPI rõ;
- function-id;
- permission;
- versioning;
- error code English/canonical;
- UI label có thể Vietnamese.

Nếu đổi URL sang English:
- làm versioned migration;
- giữ aliases tạm thời;
- không phá frontend trong một PR khổng lồ.

---

# 33. FUNCTION-ID V5 ĐỀ XUẤT

```text
STR-01..STR-08       Test Strategy
TAN-01..TAN-08       Test Analysis/TestCondition
MON-01..MON-10       Monitoring & Control
TSR-01..TSR-07       Test Status Report
TCP-01..TCP-09       Test Completion
RVS-01..RVS-08       Formal Review
MET-01..MET-07       Measurement
PQE-01..PQE-08       Product Quality Evaluation
RCA-01..RCA-08       Causal Analysis/Defect Prevention
ENVINC-01..ENVINC-06 Environment Incident
PIM-01..PIM-07       Process Improvement
```

Mỗi Function ID phải map:

```text
Function ID
→ Role
→ Permission
→ Endpoint
→ Screen
→ Entity
→ State
→ Audit
→ Idempotency
→ Acceptance test
```

---

# 34. DATABASE COLLECTIONS V5

P0:

```text
test_strategies
test_conditions
test_analysis_findings
test_monitoring_snapshots
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

Required indexes:
- every project-owned collection starts with `project_id`;
- immutable report/version identity unique;
- idempotency key where retryable create;
- status + date indexes for queues;
- artifact refs validate same project.

---

# 35. SECURITY / DATA GOVERNANCE

## P0
```text
project isolation
IDOR tests
permission tests
JWT/session revoke
secret:// refs
attachment privacy
prompt-injection handling
AI delegated authorization
audit high-impact mutation
immutable approved artifacts
```

Current repo đã có nền tốt; giữ và mở rộng cho V5 entities.

## Quality Gate
Không cho AI:
- override permission;
- set gate PASS;
- approve residual risk;
- close test process;
- rewrite approved report.

---

# 36. TESTING STRATEGY CHO CHÍNH V5

## Unit
```text
strategy state
test condition validation
exit criteria evaluator
monitoring metric formula
control action state
completion gate
measurement formula
RCA state
```

## Permission
Mỗi function mới:
```text
QA_LEAD
TESTER
BA
DEVELOPER
VIEWER
ADMIN-no-membership
```

## Integration
```text
Strategy→Plan
Requirement→Condition
Condition→Case trace
Run→MonitoringSnapshot
Monitoring→StatusReport
Completion→ReleaseClose
Defect→RCA
Measurement→QualityEvaluation
```

## E2E

```text
Create project
→ Approve Strategy
→ Baseline Requirement
→ Analyze/Test Conditions
→ Approve Test Cases
→ Approve Plan
→ Create Build/Environment
→ Execute
→ Fail→Defect
→ Retest
→ Monitoring
→ exit criteria
→ Status report
→ requirement change
→ impact/proposal
→ regression
→ Completion
→ close release
```

## Negative
```text
cross-project refs
invalid state
stale revision
double submit
double approval
AI unavailable
RAG unavailable
environment unavailable
blocked exit criterion
admin without membership
last QA lead removal
```

---

# 37. DEFINITION OF DONE P0 V5

```text
[ ] education metadata removed from testing domain
[ ] TestStrategy approved/versioned
[ ] TestPlan references Strategy
[ ] TestPlan has schedule/estimate/suspension/resumption/reporting
[ ] TestCondition implemented
[ ] Testability findings implemented
[ ] Req→Condition→Scenario→Case trace
[ ] Monitoring snapshot
[ ] plan-vs-actual
[ ] exit criteria evaluator
[ ] control actions
[ ] Test Status Report
[ ] Test Completion Report
[ ] residual risk
[ ] lessons learned
[ ] release close gate
[ ] new V5 permissions
[ ] new V5 function IDs
[ ] audit/idempotency/concurrency
[ ] frontend role gates
[ ] integration tests
[ ] E2E test process
[ ] GitHub Actions
[ ] required status checks / branch protection
[ ] large API/page files refactor underway or closed
```

---

# 38. NHỮNG GÌ KHÔNG NÊN BUILD THÊM

Để dự án không tiếp tục đi quá xa đề tài:

```text
DO NOT BUILD NOW
- employee training management
- tester certification management
- organization-wide TMMi assessment workflow
- finance/budget ERP
- Jira clone
- source code hosting
- custom CI engine
- vulnerability scanner
- full performance load engine
- full device farm
- incident management ITSM clone
- production observability platform
```

Integration với external tools là đủ.

---

# 39. ĐỊNH VỊ ĐỀ TÀI SAU V5

Tên học thuật phù hợp:

> **Xây dựng hệ thống quản lý và soạn thảo tài liệu kiểm thử thông minh tích hợp Agentic AI hỗ trợ truy vết yêu cầu, phân tích tác động thay đổi và bảo trì Test Case.**

Nếu bắt buộc giữ tên đã đăng ký:

> **Xây dựng hệ thống quản lý và soạn thảo tài liệu thông minh tích hợp AI**

thì mô tả:

> Hệ thống được chuyên môn hóa cho tài liệu kiểm thử phần mềm. Người dùng quản lý và soạn thảo Requirement, Test Strategy, Test Plan, Test Condition, Test Case, Test Report và Defect; AI hỗ trợ tìm kiếm, hỏi đáp, kiểm tra chất lượng tài liệu, sinh Test Case và phân tích tác động khi Requirement thay đổi.

Cách này giải thích được vì sao project hiện tại đi từ Document Management sang QA domain mà vẫn không mất gốc đề tài.

---

# 40. ĐÁNH GIÁ CUỐI CÙNG

## 40.1. Có cần làm lại dự án không?

**Không.**

Current repository có breadth tốt và nhiều feature đã vượt MVP.

## 40.2. Có thể nói đã bám đủ quy trình FPT/international chưa?

**Chưa.**

Chính xác hơn:

- bám tốt phần execution-oriented Test Management;
- bám tốt automation/DevTestOps integration;
- bám tốt requirement traceability và change-aware maintenance;
- thiếu formal test governance/analysis/monitoring/completion;
- thiếu maturity feedback loop ở measurement/defect prevention/optimization.

## 40.3. P0 thực sự cần làm

```text
1. Clean education legacy metadata
2. Test Strategy
3. Test Plan extension
4. Test Analysis + TestCondition
5. Test Monitoring & Control
6. Test Status Report
7. Test Completion
8. Refactor fat modules/pages
9. CI/PR quality gates
```

Nếu build xong 9 nhóm P0 này, dự án sẽ có một vertical process hợp lý:

```text
Govern
→ Plan
→ Analyze
→ Design
→ Implement
→ Execute
→ Monitor/Control
→ Complete
→ Learn
```

và Agentic AI vẫn nằm ở đúng nơi tạo giá trị:

```text
Analyze evidence
→ discover affected tests
→ propose maintenance
→ human review
→ new controlled version
```

Đây là phiên bản kiến trúc hợp lý hơn việc tiếp tục thêm ngẫu nhiên nhiều feature.

---

# 41. AUDIT EVIDENCE — REPOSITORY PATHS

Baseline evidence reviewed:

```text
backend/testing/src/main.py
backend/testing/src/core/auth.py
backend/testing/src/core/database.py
backend/testing/src/domain/schemas.py
backend/testing/src/api/execution.py
backend/testing/src/api/analytics.py
backend/testing/src/api/reviews.py
backend/testing/src/api/requirements.py
backend/testing/src/api/changes.py
backend/testing/src/api/test_design.py
backend/testing/src/api/api_artifacts.py
backend/testing/src/api/automation_execution.py
backend/testing/src/api/automation_scripts.py
backend/testing/src/api/cicd.py
backend/testing/src/api/connectors.py
backend/testing/src/api/collaboration.py
backend/testing/src/api/data_sets.py
backend/testing/src/api/design_suggestions.py
backend/testing/src/api/device_matrices.py
backend/testing/src/api/notifications.py
backend/testing/src/api/risk.py
backend/testing/src/api/templates.py
backend/testing/src/api/traceability.py
backend/testing/src/api/webhooks.py

backend/ai/src/agents/react/
backend/ai/src/agents/workflow/
backend/ai/src/tools/testing.py

frontend/features/testing/
frontend/features/testing/pages/ProjectWorkspacePage.jsx
frontend/features/testing/pages/workspace/RequirementsPage.jsx
frontend/features/testing/pages/workspace/TestDesignPage.jsx
frontend/features/testing/pages/workspace/ExecutionPage.jsx
frontend/features/testing/pages/workspace/ChangesPage.jsx
frontend/features/testing/pages/workspace/ReviewQueuePage.jsx
frontend/features/testing/pages/workspace/DefectsPage.jsx
frontend/features/testing/pages/workspace/ReportsPage.jsx
frontend/features/testing/pages/workspace/KnowledgePage.jsx
frontend/features/testing/pages/workspace/SettingsPage.jsx
frontend/features/testing/routes.js

backend/testing/tests/
frontend/e2e/
docker-compose.yml
docker-compose.test.yml
prometheus.yml
ruff.toml
```

Observed baseline:
- `main` commit: `484a56d571142010bff3b7afdea7b17ce60ae823`.
- branch protection/status checks were not enabled at audit time.
- `.github/workflows` was not present at the audited commit.
- this audit is source-based; it does not claim all tests passed in a fresh runtime unless CI/local execution proves that separately.

---

# 42. V5 CHANGE POLICY

Từ V5 trở đi không dùng câu:

> "đã đầy đủ 100% theo FPT/TMMi".

Chỉ được dùng:

```text
Implemented
Partially Implemented
Not Implemented
Out of Product Scope
Needs Runtime Verification
```

Một process area chỉ chuyển sang Implemented khi:
- entity/domain contract có;
- backend API có;
- permission có;
- frontend flow có;
- audit có;
- tests có;
- runtime verification pass.

Tài liệu này là **build-gap specification sau source audit**, không phải chứng nhận chất lượng của repository.
