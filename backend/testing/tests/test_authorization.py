from src.core.auth import PROJECT_PERMISSIONS, ProjectRole, permissions_for_role


def test_qa_lead_has_complete_permission_catalogue():
    assert permissions_for_role(ProjectRole.QA_LEAD) == PROJECT_PERMISSIONS


def test_viewer_is_read_only():
    permissions = permissions_for_role(ProjectRole.VIEWER)
    assert permissions
    assert all(permission.endswith(".read") for permission in permissions)


def test_tester_approval_and_policy_permissions_are_denied_by_default():
    permissions = permissions_for_role(ProjectRole.TESTER)
    assert "testcase.approve" not in permissions
    assert "requirement.approve" not in permissions
    assert "testrun.create" not in permissions
    assert "defect.close" not in permissions
    assert "knowledge.manage" not in permissions


def test_tester_policy_can_grant_only_configured_permissions():
    permissions = permissions_for_role(
        ProjectRole.TESTER,
        {
            "tester_can_create_run": True,
            "tester_can_close_defect": True,
        },
    )
    assert "testrun.create" in permissions
    assert "defect.close" in permissions
    assert "impact.override" not in permissions


def test_tester_run_management_policy_grants_assignment_and_state_transitions():
    permissions = permissions_for_role(
        ProjectRole.TESTER,
        {"tester_can_manage_runs": True},
    )
    assert {
        "testrun.update",
        "testrun.assign",
        "testrun.start",
        "testrun.complete",
        "testrun.abort",
    } <= permissions


def test_collaborators_can_remove_only_unreferenced_attachments():
    for role in (ProjectRole.QA_LEAD, ProjectRole.TESTER, ProjectRole.BA):
        assert "attachment.delete_own_unreferenced" in permissions_for_role(role)
    assert "attachment.delete_own_unreferenced" not in permissions_for_role(ProjectRole.DEVELOPER)


def test_ba_permissions_follow_v4_defaults_and_policies():
    defaults = permissions_for_role(ProjectRole.BA)
    assert "requirement.create" in defaults
    assert "requirement.update" in defaults
    assert "testcase.create" not in defaults
    assert "requirement.approve" not in defaults
    assert "trace.confirm" not in defaults
    configured = permissions_for_role(
        ProjectRole.BA,
        {
            "ba_can_approve_requirements": True,
            "ba_can_confirm_trace": True,
            "ba_can_revoke_trace": True,
            "ba_can_update_defect": True,
        },
    )
    assert "requirement.approve" in configured
    assert "trace.confirm" in configured
    assert "trace.revoke" in configured
    assert "defect.update" in configured


def test_developer_does_not_receive_unscoped_defect_update():
    permissions = permissions_for_role(ProjectRole.DEVELOPER)
    assert "defect.create" in permissions
    assert "defect.update" not in permissions
    assert "defect.transition.developer" not in permissions
    assert "impact.review" in permissions
    assert "proposal.review" in permissions


def test_v43_canonical_permission_catalogue_is_complete():
    expected = {
        "project.restore",
        "requirement_document.confirm_extraction",
        "requirement.version.create",
        "testplan.approve",
        "testscenario.clone",
        "testcase.version.create",
        "testsuite.clone",
        "coverage.snapshot.create",
        "impact.override",
        "proposal.approve",
        "regression.approve",
        "testrun.assign",
        "testresult.correct",
        "defect.transition.developer",
        "ai.result_metadata.read",
        "comment.moderate",
        "attachment.delete_own_unreferenced",
    }
    assert expected <= PROJECT_PERMISSIONS


def test_ba_and_developer_defect_creation_defaults_follow_v42():
    assert "defect.create" in permissions_for_role(ProjectRole.BA)
    assert "defect.create" in permissions_for_role(ProjectRole.DEVELOPER)


def test_ba_and_developer_defect_creation_can_be_limited_by_project_policy():
    assert "defect.create" not in permissions_for_role(
        ProjectRole.BA, {"ba_can_create_defect": False}
    )
    assert "defect.create" not in permissions_for_role(
        ProjectRole.DEVELOPER, {"developer_can_create_defect": False}
    )


def test_permission_overrides_are_limited_to_known_catalogue():
    permissions = permissions_for_role(
        ProjectRole.VIEWER,
        {
            "permission_overrides": {
                "VIEWER": {
                    "allow": ["testcase.create", "unknown.permission"],
                    "deny": ["project.read"],
                }
            }
        },
    )
    assert "testcase.create" in permissions
    assert "project.read" not in permissions
    assert "unknown.permission" not in permissions


def test_unknown_role_has_no_permissions():
    assert permissions_for_role("OWNER") == set()
