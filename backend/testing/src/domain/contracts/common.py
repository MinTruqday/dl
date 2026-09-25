from typing import Literal, TypeAlias


def empty_doc():
    return {"type": "doc", "content": []}


KnowledgeSourceType = Literal[
    "SRS",
    "BRD",
    "USER_STORY",
    "ACCEPTANCE_CRITERIA",
    "BUSINESS_RULE",
    "API_SPEC",
    "UI_SPEC",
    "ARCHITECTURE",
    "MEETING_NOTE",
    "RELEASE_NOTE",
    "BUG_HISTORY",
    "TEST_ARTIFACT",
    "REGULATION",
    "REFERENCE",
    "OTHER",
]
KnowledgeAuthority = Literal[
    "APPROVED_SOURCE",
    "CONTROLLED_SOURCE",
    "PROJECT_REFERENCE",
    "SUPPLEMENTAL",
    "DRAFT",
    "UNVERIFIED",
]
KnowledgeApprovalStatus = Literal["DRAFT", "IN_REVIEW", "APPROVED", "REJECTED"]

TestOutcome: TypeAlias = Literal[
    "PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"
]
TestExecutionStatus: TypeAlias = Literal[
    "PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE", "IN_PROGRESS", "NOT_RUN"
]
NOT_APPLICABLE_OUTCOME = "NOT_APPLICABLE"
FAILED_OUTCOME = "FAIL"
