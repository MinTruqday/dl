from enum import Enum

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

from src.core.configuration import settings


class SystemRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class ProjectRole(str, Enum):
    QA_LEAD = "QA_LEAD"
    TESTER = "TESTER"
    BA = "BA"
    DEVELOPER = "DEVELOPER"
    VIEWER = "VIEWER"


PROJECT_PERMISSIONS = set(
    """
project.read project.create project.update project.archive project.restore project.settings.manage
project.members.read project.members.manage project.audit.read
requirement_document.read requirement_document.download requirement_document.upload
requirement_document.extract requirement_document.review_extraction
requirement_document.confirm_extraction requirement_document.archive requirement_document.restore
requirement.read requirement.create requirement.update requirement.review requirement.submit_review
requirement.approve requirement.archive requirement.restore requirement.version.create
requirement.version.read requirement.diff.read acceptance_criteria.manage business_rule.manage
requirement_dependency.manage
testplan.read testplan.create testplan.update testplan.submit_review testplan.approve testplan.archive
testscenario.read testscenario.create testscenario.update testscenario.clone testscenario.archive
testcase.read testcase.create testcase.update testcase.review testcase.clone testcase.import
testcase.export testcase.lint testcase.duplicate_check testcase.submit_review testcase.approve
testcase.version.create testcase.version.read testcase.archive testcase.restore
testsuite.read testsuite.create testsuite.update testsuite.clone testsuite.archive
trace.read trace.create trace.review trace.confirm trace.revoke trace.recover
coverage.read coverage.snapshot.create
changeset.read changeset.create changeset.review
impact.read impact.execute impact.review impact.override impact.close
proposal.read proposal.review proposal.reject proposal.approve
regression.read regression.generate regression.approve
testrun.read testrun.create testrun.update testrun.assign testrun.start testrun.execute
testrun.complete testrun.abort testresult.correct
defect.read defect.create defect.update defect.trace.manage defect.assign defect.triage
defect.transition.developer defect.retest defect.close defect.duplicate_check
knowledge.read knowledge.manage ai.ask_project ai.generate_scenario ai.generate_testcase
ai.run_lint ai.run_duplicate_check ai.run_impact ai.create_proposal ai.generate_regression
ai.result_metadata.read analytics.read analytics.ai.read report.read report.export
comment.read comment.create comment.update_own comment.delete_own comment.moderate
attachment.read attachment.upload attachment.delete_own_unreferenced attachment.moderate
notification.read notification.mark_read notification.preferences.manage
testplan.manage testsuite.manage testrun.manage review.comment review.read review.resolve
""".split()
)

READ_ONLY_PERMISSIONS = {
    "project.read",
    "project.members.read",
    "requirement_document.read",
    "requirement.read",
    "requirement.version.read",
    "requirement.diff.read",
    "testplan.read",
    "testscenario.read",
    "testcase.read",
    "testcase.version.read",
    "testsuite.read",
    "trace.read",
    "coverage.read",
    "changeset.read",
    "impact.read",
    "proposal.read",
    "regression.read",
    "testrun.read",
    "defect.read",
    "knowledge.read",
    "ai.result_metadata.read",
    "analytics.read",
    "report.read",
    "comment.read",
    "attachment.read",
    "notification.read",
    "review.read",
}

COLLABORATOR_PERMISSIONS = {
    "comment.read",
    "comment.create",
    "comment.update_own",
    "comment.delete_own",
    "attachment.read",
    "attachment.upload",
    "notification.read",
    "notification.mark_read",
    "notification.preferences.manage",
    "review.comment",
    "review.read",
    "review.resolve",
}

TESTER_PERMISSIONS = READ_ONLY_PERMISSIONS | COLLABORATOR_PERMISSIONS | set(
    """
testplan.create testplan.update testplan.submit_review testplan.manage
testscenario.create testscenario.update testscenario.clone testscenario.archive
testcase.create testcase.update testcase.review testcase.clone testcase.import testcase.export
testcase.lint testcase.duplicate_check testcase.submit_review testcase.version.create
requirement_document.download
testsuite.create testsuite.update testsuite.clone testsuite.archive testsuite.manage
trace.create trace.review trace.recover changeset.create changeset.review
impact.execute impact.review proposal.review regression.generate
testrun.execute defect.create defect.update defect.triage defect.retest defect.duplicate_check
ai.ask_project ai.generate_scenario ai.generate_testcase ai.run_lint ai.run_duplicate_check
ai.run_impact ai.create_proposal ai.generate_regression analytics.ai.read report.export
""".split()
)

BA_PERMISSIONS = READ_ONLY_PERMISSIONS | COLLABORATOR_PERMISSIONS | set(
    """
requirement_document.download requirement_document.upload requirement_document.extract
requirement_document.review_extraction requirement_document.confirm_extraction
requirement_document.archive requirement_document.restore
requirement.create requirement.update requirement.review requirement.submit_review
requirement.version.create acceptance_criteria.manage business_rule.manage requirement_dependency.manage
trace.create trace.review changeset.create changeset.review impact.review proposal.review
testcase.export testcase.lint testcase.duplicate_check defect.create
knowledge.manage ai.ask_project ai.run_lint ai.run_duplicate_check analytics.ai.read report.export
""".split()
)

DEVELOPER_PERMISSIONS = READ_ONLY_PERMISSIONS | COLLABORATOR_PERMISSIONS | {
    "requirement_document.download",
    "impact.review",
    "proposal.review",
    "defect.create",
    "defect.transition.developer",
    "defect.duplicate_check",
    "ai.ask_project",
}

ROLE_PERMISSIONS = {
    ProjectRole.QA_LEAD: PROJECT_PERMISSIONS,
    ProjectRole.TESTER: TESTER_PERMISSIONS,
    ProjectRole.BA: BA_PERMISSIONS,
    ProjectRole.DEVELOPER: DEVELOPER_PERMISSIONS,
    ProjectRole.VIEWER: READ_ONLY_PERMISSIONS,
}

POLICY_PERMISSIONS = {
    "ba_can_approve_requirements": (ProjectRole.BA, "requirement.approve"),
    "ba_can_confirm_trace": (ProjectRole.BA, "trace.confirm"),
    "ba_can_revoke_trace": (ProjectRole.BA, "trace.revoke"),
    "ba_can_update_defect": (ProjectRole.BA, "defect.update"),
    "tester_can_confirm_trace": (ProjectRole.TESTER, "trace.confirm"),
    "tester_can_revoke_trace": (ProjectRole.TESTER, "trace.revoke"),
    "tester_can_create_run": (ProjectRole.TESTER, "testrun.create"),
    "tester_can_override_impact": (ProjectRole.TESTER, "impact.override"),
    "tester_can_close_defect": (ProjectRole.TESTER, "defect.close"),
    "tester_can_manage_knowledge": (ProjectRole.TESTER, "knowledge.manage"),
    "tester_can_manage_runs": (ProjectRole.TESTER, "testrun.update"),
    "tester_can_start_runs": (ProjectRole.TESTER, "testrun.start"),
    "tester_can_complete_runs": (ProjectRole.TESTER, "testrun.complete"),
    "tester_can_abort_runs": (ProjectRole.TESTER, "testrun.abort"),
    "tester_can_correct_results": (ProjectRole.TESTER, "testresult.correct"),
    "tester_can_approve_regression": (ProjectRole.TESTER, "regression.approve"),
    "tester_can_create_coverage_snapshot": (ProjectRole.TESTER, "coverage.snapshot.create"),
    "tester_can_review_testcase_changes": (ProjectRole.TESTER, "testcase.review"),
    "ba_can_archive_requirements": (ProjectRole.BA, "requirement.archive"),
    "ba_can_restore_requirements": (ProjectRole.BA, "requirement.restore"),
    "viewer_can_use_ai_qna": (ProjectRole.VIEWER, "ai.ask_project"),
    "viewer_can_download_sources": (ProjectRole.VIEWER, "requirement_document.download"),
    "viewer_can_export": (ProjectRole.VIEWER, "report.export"),
    "developer_can_export": (ProjectRole.DEVELOPER, "report.export"),
}

READ_PERMISSIONS = READ_ONLY_PERMISSIONS


class CurrentUser(BaseModel):
    id: str = Field(alias="_id")
    email: str = ""
    system_role: SystemRole = SystemRole.USER

    @property
    def is_system_admin(self):
        return self.system_role == SystemRole.ADMIN


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/xac-thuc/dang-nhap", auto_error=False)


def permissions_for_role(role: ProjectRole | str, settings_value: dict | None = None):
    try:
        normalized = role if isinstance(role, ProjectRole) else ProjectRole(str(role).upper())
    except ValueError:
        return set()
    permissions = set(ROLE_PERMISSIONS[normalized])
    project_settings = settings_value or {}
    for key, (policy_role, permission) in POLICY_PERMISSIONS.items():
        if normalized == policy_role and project_settings.get(key) is True:
            permissions.add(permission)
    overrides = project_settings.get("permission_overrides", {}).get(normalized.value, {})
    permissions.update(item for item in overrides.get("allow", []) if item in PROJECT_PERMISSIONS)
    permissions.difference_update(overrides.get("deny", []))
    return permissions


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    x_test_user_id: str | None = Header(default=None),
    x_test_system_role: str = Header(default="USER"),
):
    if settings.TESTING_ALLOW_TEST_IDENTITY and x_test_user_id:
        try:
            system_role = SystemRole(x_test_system_role.upper())
        except ValueError:
            system_role = SystemRole.USER
        return CurrentUser(
            _id=x_test_user_id,
            email=f"{x_test_user_id}@test.local",
            system_role=system_role,
        )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_REQUIRED"},
        )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("uid") or payload.get("sub")
        email = payload.get("email") or payload.get("sub", "")
        if not user_id:
            raise ValueError
        role_value = payload.get("system_role")
        if not role_value:
            role_value = "ADMIN" if str(payload.get("role", "")).lower() == "admin" else "USER"
        return CurrentUser(
            _id=str(user_id),
            email=str(email),
            system_role=SystemRole(str(role_value).upper()),
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED"},
        )
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_INVALID"},
        )


def require_authenticated(user: CurrentUser = Depends(get_current_user)):
    return user
