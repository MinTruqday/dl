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


PROJECT_PERMISSIONS = {
    "project.read",
    "project.update",
    "project.archive",
    "project.members.read",
    "project.members.manage",
    "project.audit.read",
    "requirement.read",
    "requirement.create",
    "requirement.update",
    "requirement.submit_review",
    "requirement.approve",
    "requirement.archive",
    "requirement.version.read",
    "acceptance_criteria.manage",
    "business_rule.manage",
    "testscenario.read",
    "testscenario.create",
    "testscenario.update",
    "testcase.read",
    "testcase.create",
    "testcase.update",
    "testcase.submit_review",
    "testcase.approve",
    "testcase.archive",
    "testcase.version.read",
    "trace.read",
    "trace.create",
    "trace.confirm",
    "trace.revoke",
    "coverage.read",
    "testplan.read",
    "testplan.manage",
    "testsuite.read",
    "testsuite.manage",
    "testrun.read",
    "testrun.create",
    "testrun.manage",
    "testrun.execute",
    "defect.read",
    "defect.create",
    "defect.update",
    "defect.assign",
    "defect.retest",
    "defect.close",
    "impact.read",
    "impact.execute",
    "impact.override",
    "proposal.read",
    "proposal.review",
    "proposal.approve",
    "review.comment",
    "review.read",
    "review.resolve",
    "regression.read",
    "regression.generate",
    "regression.approve",
    "knowledge.read",
    "knowledge.manage",
    "ai.generate_testcase",
    "ai.run_lint",
    "ai.run_impact",
    "ai.create_proposal",
}

ROLE_PERMISSIONS = {
    ProjectRole.QA_LEAD: PROJECT_PERMISSIONS,
    ProjectRole.TESTER: {
        "project.read",
        "project.members.read",
        "requirement.read",
        "requirement.version.read",
        "testscenario.read",
        "testscenario.create",
        "testscenario.update",
        "testcase.read",
        "testcase.create",
        "testcase.update",
        "testcase.submit_review",
        "testcase.version.read",
        "trace.read",
        "trace.create",
        "coverage.read",
        "testplan.read",
        "testsuite.read",
        "testsuite.manage",
        "testrun.read",
        "testrun.execute",
        "defect.read",
        "defect.create",
        "defect.update",
        "defect.retest",
        "impact.read",
        "impact.execute",
        "proposal.read",
        "proposal.review",
        "review.comment",
        "review.read",
        "review.resolve",
        "regression.read",
        "regression.generate",
        "knowledge.read",
        "ai.generate_testcase",
        "ai.run_lint",
        "ai.run_impact",
        "ai.create_proposal",
    },
    ProjectRole.BA: {
        "project.read",
        "project.members.read",
        "requirement.read",
        "requirement.create",
        "requirement.update",
        "requirement.submit_review",
        "requirement.version.read",
        "acceptance_criteria.manage",
        "business_rule.manage",
        "testscenario.read",
        "testcase.read",
        "testcase.version.read",
        "trace.read",
        "trace.create",
        "coverage.read",
        "testplan.read",
        "testsuite.read",
        "testrun.read",
        "defect.read",
        "defect.create",
        "impact.read",
        "proposal.read",
        "proposal.review",
        "review.comment",
        "review.read",
        "review.resolve",
        "regression.read",
        "knowledge.read",
        "knowledge.manage",
        "ai.run_lint",
    },
    ProjectRole.DEVELOPER: {
        "project.read",
        "project.members.read",
        "requirement.read",
        "requirement.version.read",
        "testscenario.read",
        "testcase.read",
        "testcase.version.read",
        "trace.read",
        "coverage.read",
        "testplan.read",
        "testsuite.read",
        "testrun.read",
        "defect.read",
        "defect.create",
        "impact.read",
        "proposal.read",
        "proposal.review",
        "review.comment",
        "review.read",
        "review.resolve",
        "regression.read",
        "knowledge.read",
    },
    ProjectRole.VIEWER: {
        "project.read",
        "project.members.read",
        "requirement.read",
        "requirement.version.read",
        "testscenario.read",
        "testcase.read",
        "testcase.version.read",
        "trace.read",
        "coverage.read",
        "testplan.read",
        "testsuite.read",
        "testrun.read",
        "defect.read",
        "impact.read",
        "proposal.read",
        "review.read",
        "regression.read",
        "knowledge.read",
    },
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
}

READ_PERMISSIONS = {
    permission
    for permission in PROJECT_PERMISSIONS
    if permission.endswith(".read") or permission in {"coverage.read", "knowledge.read"}
}


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
    if settings.QA_ALLOW_TEST_IDENTITY and x_test_user_id:
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
