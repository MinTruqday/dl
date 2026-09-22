# VERIQ — AI TESTING AGENT SYSTEM
## Final Architecture & Implementation Specification

> **Status:** FINAL DESIGN SPEC  
> **Repository:** `MinTruqday/dl`  
> **Current audited reference:** `e244fdd4f6920701f8e52363a88ffe1e2fc95dd2` (`567 commit`)  
> **Core principle:** **One unified agent workflow** coordinated by a Supervisor, with bounded specialist agents.  
> **Scope:** Software Testing only.  

---

# 1. Final Architecture Decision

Veriq uses **one canonical workflow**:

```text
User/Event
→ Load Context
→ Supervisor Understand
→ Plan
→ Select/Delegate Specialist
→ Specialist Agent Execution
→ Collect Result
→ Supervisor Re-evaluate
→ Aggregate + Propose
→ Human Approval if required
→ Apply if required
→ Verify
→ End
```

Specialist agents are not separate system workflows. Each specialist runs the same internal agent loop:

```text
Observe
→ Reason
→ Act
→ Observation
→ Re-evaluate
→ Continue or Return Result
```

Target specialists:

```text
Requirement Agent
Test Design Agent
Analysis Agent
Execution Agent
Reporting Agent
```

---

# 2. Human Roles

Actual project roles:

```text
QA
TESTER
BA
DEVELOPER
VIEWER
```

System roles:

```text
USER
ADMIN
```

Human roles are RBAC identities, not AI-agent identities.

---

# 3. High-Level Architecture

```text
┌──────────────────────────────────────────────┐
│ 1. USER INTERFACE                           │
│ QA / TESTER / BA / DEVELOPER / VIEWER │
│                                              │
│ Generate Test Cases                         │
│ Analyze Requirement                         │
│ Analyze Impact                              │
│ Review Coverage                             │
│ Analyze Execution / Failure                 │
│ Project Q&A                                 │
│ Reports                                     │
│ Approve / Apply                             │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ 2. BACKEND / API LAYER                      │
│ FastAPI                                      │
│ Auth + RBAC                                  │
│ Project Context Loader                       │
│ Agent Run API                                │
│ Approval API                                 │
│ Response Formatter                           │
│ Audit / Metrics                              │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ 3. AI AGENT LAYER                           │
│                                              │
│              SUPERVISOR AGENT                │
│                                              │
│ Understand → Plan → Delegate                 │
│ Collect → Re-evaluate → Aggregate            │
│                                              │
│ Requirement Agent                            │
│ Test Design Agent                            │
│ Analysis Agent                               │
│ Execution Agent                              │
│ Reporting Agent                              │
│                                              │
│ Specialist loop:                             │
│ Observe → Reason → Act → Observation         │
│ → Re-evaluate                                │
│                                              │
│ Runtime: LangGraph                           │
│ Memory: Short-term + Long-term Project       │
│ Control: RBAC + Tool Policy + Limits         │
│          Approval + Verification             │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ 4. TOOLS & DATA SOURCES                     │
│ Project Database                             │
│ Project Documents                            │
│ Qdrant Vector Store                          │
│ Neo4j Knowledge Graph [TARGET / NEW]         │
│ Testing APIs / Tools                         │
│ Structured AI Skills                         │
└──────────────────────────────────────────────┘
```

---

# 4. Current Code vs Target

## KEEP

```text
backend/testing/src/services/design_assistance.py
backend/ai/src/api/inference.py
backend/ai/src/tools/testing.py
Qdrant vector/search infrastructure
Embeddings
Semantic/vector retrieval
Deterministic validation
Auth / RBAC
Metrics / audit
Testing domain APIs
```

## REFACTOR

```text
backend/ai/src/agents/react/*
backend/ai/src/agents/workflow/*
backend/ai/src/agents/memory/*
generic supervisor/orchestration
generic agent state
```

## BUILD

```text
Testing-domain Supervisor Agent
Requirement Agent
Test Design Agent
Analysis Agent
Execution Agent
Reporting Agent

Agent Run State
Agent Task / Agent Result
Tool Policy Registry
Project-scoped Long-term Memory
Neo4j Graph Layer
Hybrid Evidence Retrieval
Approval Interrupt / Resume
Apply + Verify
```

## REMOVE LATER ONLY AFTER REACHABILITY AUDIT

```text
generic chat/work/goal/learn/plan behavior
unused generic interaction route
unused generic semantic router
unused generic web-search specialist
unused personal-assistant memory behavior
unused generic document/mindmap/instruction wrappers
```

---

# 5. Canonical Unified Agent Workflow

```text
START
  │
  ▼
1. RECEIVE OBJECTIVE
  │  user request / event
  │  project_id
  │  target artifact/context
  │  constraints
  ▼
2. LOAD CONTEXT
  │  Auth + RBAC
  │  Project Context
  │  Source-of-truth data
  │  Short-term run memory
  │  Relevant long-term project memory
  ▼
3. PLAN
  │  Understand intent
  │  Determine evidence needed
  │  Select specialist(s)
  │  Define success criteria
  ▼
4. SELECT / DELEGATE
  │
  ▼
┌───────────────────────────────────────┐
│ 5. SPECIALIST AGENT EXECUTION         │
│                                       │
│ Observe                               │
│   ↓                                   │
│ Reason                                │
│   ↓                                   │
│ Act                                   │
│   ↓                                   │
│ Observation                           │
│   ↓                                   │
│ Re-evaluate                           │
│   ├── Need more → Observe             │
│   └── Done → Specialist Result        │
└───────────────────┬───────────────────┘
                    │
                    ▼
6. COLLECT RESULT
  │
  ▼
7. SUPERVISOR RE-EVALUATE
  │
  ├── More work needed?
  │      └── YES → back to 4. SELECT / DELEGATE
  │
  └── Goal satisfied
          │
          ▼
8. AGGREGATE + PROPOSE
          │
          ▼
9. APPROVAL REQUIRED?
          │
          ├── NO ───────────────────────┐
          │                             │
          └── YES                       │
                 │                      │
                 ▼                      │
          HUMAN APPROVAL                │
          ├── Reject → Supervisor Re-evaluate
          └── Approve                   │
                 │                      │
                 ▼                      │
10. APPLY (if mutation required)        │
                 │                      │
                 └──────────────────────┤
                                        ▼
11. VERIFY
  │
  ▼
END
```

Only one final `END`.

---

# 6. Specialist Agent Loop

The agent loop lives inside Step 5.

## Observe

Collects:

```text
Project context
Current run state
Relevant project memory
Source-of-truth records
Qdrant semantic results
Neo4j relationships
Previous observations
Tool results
```

Observer is not a separate agent.

## Reason

Decides the next bounded action.

## Act

Calls one allowed tool or structured AI skill.

## Observation

Receives the structured tool/skill result.

## Re-evaluate

Checks:

```text
Enough evidence?
Sub-goal complete?
Need another tool?
Evidence conflict?
Limit reached?
```

---

# 7. Supervisor Agent

Responsibilities:

```text
Understand objective
Load project + role + permission context
Create bounded plan
Select specialist
Delegate task
Collect specialist result
Re-evaluate global goal
Request more work when needed
Aggregate evidence
Build structured proposal
Trigger human approval
Ensure final verification
```

The Supervisor orchestrates. Deep domain work belongs to specialists.

---

# 8. Requirement Agent

Owns:

```text
Requirement quality
Requirement ambiguity
Acceptance Criteria
Requirement versions
Testability
Requirement evidence
Requirement traceability context
```

Reuse:

```text
get_requirement_version
compare_requirement_versions
get_acceptance_criteria
search_project_knowledge
requirement_quality_analysis
```

---

# 9. Test Design Agent

Owns:

```text
Test conditions
Test scenarios
Test cases
Coverage analysis
Duplicate detection
Security test design
Performance test planning
Test maintenance proposals
```

Reuse:

```text
search_test_cases
find_near_duplicates
calculate_coverage
scenario_generation
test_generation
test_condition_generation
security_test_generation
performance_plan_generation
create_test_case_draft
propose_testcase_revision
```

---

# 10. Analysis Agent

Owns:

```text
Change impact
Traceability analysis
Regression scope
Historical defect analysis
Causal analysis
Risk patterns
Maintenance recommendations
```

Reuse:

```text
get_trace_links
get_execution_history
get_historical_defects
analyze_change_impact
impact_analysis
causal_analysis
suggest_regression_scope
create_impact_analysis
create_maintenance_proposal
create_regression_recommendation
```

---

# 11. Execution Agent

Owns:

```text
Execution context
Test result analysis
Failure triage
Execution history
Automation assistance
```

Reuse:

```text
get_test_results
get_test_case_version
get_execution_history
automation_script_generation
execution-related APIs
```

It must not fabricate execution state.

---

# 12. Reporting Agent

Owns:

```text
Project Q&A
Status reports
Completion reports
Quality summaries
Lessons learned
Evidence-backed summaries
```

Reuse:

```text
project_question
status_report_narrative
completion_report_narrative
lessons_learned_clustering
```

---

# 13. Structured AI Skills

Current structured capabilities remain useful as skills:

```text
project_question
requirement_quality_analysis
scenario_generation
test_generation
impact_analysis
security_test_generation
performance_plan_generation
automation_script_generation
test_condition_generation
causal_analysis
status_report_narrative
completion_report_narrative
lessons_learned_clustering
```

Pattern:

```text
Agent decides
→ calls structured skill
→ receives typed result
→ uses it as Observation
→ re-evaluates
```

---

# 14. Agent Run State

```python
class VeriqRunState(BaseModel):
    run_id: str
    project_id: str
    user_id: str
    role: str
    permissions: list[str]

    objective: str
    intent: str

    supervisor_plan: list[dict]
    active_task: dict | None
    completed_tasks: list[dict]
    specialist_results: list[dict]

    observations: list[dict]
    evidence_refs: list[str]
    tool_calls: list[dict]

    proposal: dict | None
    approval_status: str | None

    current_step: int
    status: str
    error_code: str | None
```

Do not persist hidden chain-of-thought.

---

# 15. Agent Task Contract

```python
class AgentTask(BaseModel):
    task_id: str
    run_id: str
    project_id: str

    specialist: Literal[
        "requirement",
        "test_design",
        "analysis",
        "execution",
        "reporting",
    ]

    objective: str
    evidence_refs: list[str] = []
    constraints: dict = {}
```

---

# 16. Agent Result Contract

```python
class AgentResult(BaseModel):
    task_id: str

    status: Literal[
        "COMPLETED",
        "INSUFFICIENT_EVIDENCE",
        "FAILED",
        "LIMIT_REACHED",
    ]

    summary: str
    evidence_refs: list[str]
    reason_codes: list[str]
    proposals: list[dict]
    warnings: list[str]
```

---

# 17. Short-Term Memory

Stores the current run only:

```text
run_id
project_id
objective
current plan
current specialist
observations
tool results
evidence refs
proposal
approval status
errors/retries
```

Recommended:

```text
LangGraph state
+ Redis ephemeral runtime/cache
+ MongoDB checkpoint only if durable resume is needed
```

---

# 18. Long-Term Project Memory

Project-scoped validated memory:

```text
Accepted proposals
Rejected proposals + reason
Validated analyses
Recurring defect patterns
Lessons learned
Historical risks
Project decisions
Previously verified outcomes
```

Correct write path:

```text
AI Proposal
→ Human Approval or Objective Verification
→ Applied / Verified Outcome
→ Long-Term Project Memory
```

Unverified AI statements must not become trusted project knowledge.

---

# 19. Source of Truth

Authoritative data remains:

```text
Requirements
Requirement Versions
Acceptance Criteria
Test Cases
Test Case Versions
Traceability
Executions
Results
Defects
Project Documents
Project Metadata
```

If project memory conflicts with current source-of-truth data:

```text
Source of Truth wins
```

---

# 20. Qdrant

Qdrant is a concrete knowledge component for:

```text
Vector storage
Embeddings
Semantic similarity
Semantic retrieval
Project knowledge lookup
Relevant project-memory lookup
```

---

# 21. Neo4j [TARGET / NEW]

Neo4j is a target addition, not a current assumption.

Purpose:

```text
Explicit artifact relationships
Multi-hop traceability
Change impact paths
Requirement → Test Case → Execution → Defect relationships
```

Suggested graph:

```text
(Project)-[:HAS_REQUIREMENT]->(Requirement)
(Requirement)-[:HAS_VERSION]->(RequirementVersion)
(RequirementVersion)-[:HAS_AC]->(AcceptanceCriterion)

(TestCase)-[:COVERS]->(Requirement)
(TestCase)-[:COVERS_AC]->(AcceptanceCriterion)
(TestCase)-[:HAS_VERSION]->(TestCaseVersion)

(TestExecution)-[:EXECUTES]->(TestCaseVersion)
(TestExecution)-[:PRODUCED]->(TestResult)

(TestResult)-[:RELATED_TO]->(Defect)
(Defect)-[:AFFECTS]->(Requirement)

(Change)-[:CHANGES]->(RequirementVersion)
(Change)-[:IMPACTS]->(TestCase)

(Document)-[:DESCRIBES]->(Requirement)
```

Project DB remains authoritative.

---

# 22. Hybrid Evidence Retrieval

Target retrieval combines:

```text
Project Database
+ Qdrant semantic/vector search
+ Neo4j relationship traversal
+ Validated project memory
```

Pipeline:

```text
Agent information need
→ Exact/domain lookup
→ Qdrant semantic search
→ Neo4j graph traversal
→ Normalize
→ Deduplicate
→ Filter by project/authority
→ Rerank
→ Evidence Package
→ Agent
```

Evidence item:

```text
artifact_type
artifact_id
artifact_version_id
source
authority
score
text/snippet
relationship_path (optional)
```

---

# 23. Tool Policy

Every tool defines:

```text
Name
Allowed specialist(s)
Action type
Required permission
Project scope
Approval requirement
```

Example:

```python
ToolPolicy(
    name="get_requirement_version",
    specialists={"requirement", "analysis"},
    action="READ",
    permission="requirement.read",
    requires_approval=False,
)
```

Mutation:

```python
ToolPolicy(
    name="apply_test_case_revision",
    specialists={"test_design"},
    action="MUTATE",
    permission="test_case.update",
    requires_approval=True,
)
```

---

# 24. Human Approval

Approval is policy-based.

Typical approval-required actions:

```text
Apply test case revision
Confirm traceability link
Baseline requirement version
Approve test case version
Mark test case obsolete
Other persistent domain mutations
```

Flow:

```text
Proposal
→ Permission Check
→ Human Review
→ Reject / Edit / Approve
→ Resume Workflow
→ Apply
→ Verify
```

Read-only results may bypass approval.

---

# 25. Verification

Verify is mandatory before trusted completion.

Checks may include:

```text
Was data saved?
Correct project?
Expected revision?
Traceability intact?
Schema/domain validation passed?
Evidence refs resolvable?
Metrics match source-of-truth?
Unsupported claims absent?
```

Only verified outcomes may be written to trusted long-term memory.

---

# 26. Bounded Autonomy

Define:

```text
MAX_SUPERVISOR_STEPS
MAX_SPECIALIST_STEPS
MAX_TOOL_CALLS_PER_TASK
MAX_TOOL_ERRORS
MAX_RETRIES
RUN_TIMEOUT_SECONDS
TASK_TIMEOUT_SECONDS
MAX_EVIDENCE_ITEMS
```

---

# 27. Standard Failure States

```text
INSUFFICIENT_EVIDENCE
CONFLICTING_EVIDENCE
PERMISSION_DENIED
APPROVAL_REQUIRED
APPROVAL_REJECTED
AGENT_LIMIT_REACHED
TOOL_UNAVAILABLE
TOOL_FAILED
AI_PROVIDER_UNAVAILABLE
KNOWLEDGE_UNAVAILABLE
GRAPH_UNAVAILABLE
VALIDATION_FAILED
VERIFICATION_FAILED
```

---

# 28. Degraded Behavior

Examples:

```text
LLM unavailable
→ deterministic rules + manual review

Neo4j unavailable
→ DB + Qdrant where safe
→ GRAPH_UNAVAILABLE

Qdrant unavailable
→ exact DB + Neo4j where safe
→ KNOWLEDGE_UNAVAILABLE

Specialist fails
→ Supervisor retry/fallback
→ otherwise structured degraded result
```

Never silently pretend a knowledge source succeeded.

---

# 29. Audit & Observability

Record:

```text
run_id
project_id
initiating user/event
role/permission snapshot
objective
supervisor plan
specialist assignment
tool name
safe tool arguments
tool status/latency
evidence refs
specialist result
proposal
approval decision
applied action
verification result
model/provider metadata
token/cost if available
errors/retries
timestamps
```

Do not log secrets or hidden chain-of-thought.

---

# 30. Example — Generate Test Cases

```text
User requests test cases for REQ-105
→ Supervisor loads project + permission + requirement context
→ Supervisor plans
→ Requirement Agent validates requirement + AC
→ Supervisor collects result
→ Test Design Agent checks existing tests
→ Qdrant semantic retrieval
→ Neo4j relationships when available
→ Generate candidate tests
→ Duplicate check
→ Coverage check
→ Supervisor re-evaluates
→ Aggregate + Proposal
→ Human review if persistent write is requested
→ Apply
→ Verify saved tests + traceability
→ END
```

---

# 31. Example — Requirement Change Impact

```text
Requirement changed
→ Supervisor
→ Requirement Agent compares versions + AC
→ Analysis Agent reads DB + semantic evidence + graph paths
→ Supervisor re-evaluates
→ Test Design Agent if test maintenance is needed
→ Aggregate impact
→ Regression / maintenance proposal
→ Human approval
→ Apply
→ Verify
→ END
```

---

# 32. Example — Execution Failure Analysis

```text
Execution failure
→ Supervisor
→ Execution Agent reads execution context/result
→ Analysis Agent reads defects + requirement links + similar failures
→ Causal / risk findings
→ Supervisor aggregate
→ Proposal / report
→ Verify evidence
→ END
```

---

# 33. Existing Code Reuse Strategy

Reuse before rewrite:

```text
backend/ai/src/agents/react/
backend/ai/src/agents/workflow/
backend/ai/src/agents/memory/
backend/ai/src/tools/testing.py
backend/ai/src/api/inference.py
backend/testing/src/services/design_assistance.py
```

Strategy:

```text
Reuse
→ Refactor
→ Integrate
→ Test
→ Migrate product flow
→ Remove unreachable legacy last
```

---

# 34. Migration Plan

## Phase 0 — Baseline

```text
Inventory AI endpoints
Inventory agent callers/imports
Inventory tools
Inventory memory consumers
Inventory vector/search use
Record current behavior
Add smoke/regression tests
```

## Phase 1 — Shared Schemas

```text
VeriqRunState
AgentTask
AgentResult
EvidencePackage
ToolPolicy
ApprovalState
```

## Phase 2 — Tool Registry

Add:

```text
Specialist allowlist
Permission requirement
Action type
Approval policy
Project scope
```

## Phase 3 — Specialist Agents

```text
Requirement Agent
Test Design Agent
Analysis Agent
Execution Agent
Reporting Agent
```

Reuse current tools + structured skills.

## Phase 4 — Memory

```text
Short-term → run/project scoped
Long-term → validated project memory
```

## Phase 5 — Neo4j

```text
client
schema
sync
project isolation
graph query tools
```

## Phase 6 — Hybrid Evidence

```text
DB lookup
Qdrant semantic search
Neo4j traversal
merge
deduplicate
rerank
Evidence Package
```

## Phase 7 — Supervisor Workflow

Refactor current LangGraph orchestration into the canonical workflow.

## Phase 8 — Approval / Apply / Verify

```text
approval interrupt
resume
apply
verify
validated memory write
```

## Phase 9 — Product Migration

```text
Requirement analysis
Generate test cases
Change impact
Regression recommendation
Execution/failure analysis
Reporting / Project Q&A
```

## Phase 10 — Legacy Cleanup

Delete only after callers are verified and replacement tests pass.

---

# 35. Proposed Target Source Structure

```text
backend/ai/src/
├── api/
│   ├── inference.py
│   ├── agents.py
│   └── approvals.py
│
├── agents/
│   ├── supervisor/
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── policy.py
│   ├── requirement/
│   ├── test_design/
│   ├── analysis/
│   ├── execution/
│   └── reporting/
│
├── runtime/
│   ├── state.py
│   ├── task.py
│   ├── limits.py
│   └── dispatcher.py
│
├── memory/
│   ├── short_term.py
│   ├── project_memory.py
│   └── policy.py
│
├── knowledge/
│   ├── evidence.py
│   ├── hybrid.py
│   ├── vector.py
│   └── graph/
│       ├── client.py
│       ├── repository.py
│       ├── schema.py
│       ├── queries.py
│       └── sync.py
│
├── tools/
│   ├── testing.py
│   ├── registry.py
│   └── policy.py
│
└── services/
    └── existing inference / indexing / retrieval services
```


---

# 36. Suggested Implementation Commits

```text
AI-01 Baseline tests + inventory
AI-02 Shared schemas/state
AI-03 Tool registry + policies
AI-04 Requirement Agent
AI-05 Test Design Agent
AI-06 Analysis Agent
AI-07 Execution Agent
AI-08 Reporting Agent
AI-09 Short-term run memory
AI-10 Long-term project memory
AI-11 Neo4j client/schema
AI-12 Neo4j sync
AI-13 Hybrid evidence retrieval
AI-14 Supervisor LangGraph workflow
AI-15 Approval interrupt/resume
AI-16 Apply + Verify
AI-17 Backend integration
AI-18 Frontend agent run/proposal UI
AI-19 Evaluation/benchmark
AI-20 Legacy reachability audit
AI-21 Legacy cleanup
```

---

# 37. Definition of Done

## Workflow

- [ ] One unified workflow.
- [ ] Supervisor can understand, plan, delegate, collect, re-evaluate.
- [ ] Specialists use Observe → Reason → Act → Observation → Re-evaluate.
- [ ] More work loops to delegation.
- [ ] Goal completion proceeds to Aggregate + Propose.
- [ ] Approval is conditional.
- [ ] Apply is conditional.
- [ ] Verify is explicit.
- [ ] One final End only.

## Agents

- [ ] Requirement Agent.
- [ ] Test Design Agent.
- [ ] Analysis Agent.
- [ ] Execution Agent.
- [ ] Reporting Agent.
- [ ] Bounded tool access.
- [ ] Structured task/result contracts.

## Knowledge

- [ ] Project DB remains authoritative.
- [ ] Qdrant semantic/vector search works.
- [ ] Neo4j relationship traversal implemented.
- [ ] Evidence refs preserved.
- [ ] Cross-project isolation tested.

## Memory

- [ ] Short-term memory is run/project scoped.
- [ ] Long-term memory is project scoped.
- [ ] Unverified AI statements are not trusted memory.
- [ ] Verified outcomes can be persisted.

## Control

- [ ] RBAC.
- [ ] Tool allowlists.
- [ ] Step/time/tool limits.
- [ ] Human approval for controlled mutations.
- [ ] Apply then Verify.
- [ ] Audit trail.
- [ ] Secret isolation.

## Existing Code

- [ ] Structured inference preserved.
- [ ] Testing tools reused where possible.
- [ ] LangGraph reused/refactored.
- [ ] Qdrant/vector search preserved.
- [ ] Deterministic validations preserved.
- [ ] Legacy removed only after reachability audit.

---

# 38. Final Canonical Summary

```text
User / Event
    │
    ▼
Backend
Auth + RBAC + Project Context
    │
    ▼
Supervisor Agent
Understand
→ Plan
→ Select / Delegate
    │
    ▼
Specialist Agent
Observe
→ Reason
→ Act
→ Observation
→ Re-evaluate
    │
    ▼
Specialist Result
    │
    ▼
Supervisor
Collect
→ Re-evaluate
    │
    ├── More work → Delegate again
    │
    └── Goal reached
            │
            ▼
Aggregate + Propose
            │
            ▼
Approval if required
            │
            ▼
Apply if required
            │
            ▼
Verify
            │
            ▼
END
```

Supporting knowledge:

```text
Project Database
+
Project Documents
+
Qdrant Semantic/Vector Search
+
Neo4j Knowledge Graph [TARGET]
+
Short-term Run Memory
+
Long-term Project Memory
```

This is the final architecture to implement and to use for the Veriq architecture poster.
