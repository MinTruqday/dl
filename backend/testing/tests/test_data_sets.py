from src.api.data_sets import expand_variables, public_data_set_version


def test_expand_variables_is_bounded_and_reports_truncation():
    rows, truncated = expand_variables({"role": ["lead", "tester"], "active": [True, False]}, 3)
    assert rows == [
        {"active": True, "role": "lead"},
        {"active": True, "role": "tester"},
        {"active": False, "role": "lead"},
    ]
    assert truncated is True


def test_expand_variables_does_not_mark_exact_limit_as_truncated():
    rows, truncated = expand_variables({"value": [1, 2]}, 2)
    assert rows == [{"value": 1}, {"value": 2}]
    assert truncated is False


def test_public_data_set_version_redacts_secret_references():
    value = public_data_set_version(
        {
            "_id": "version-1",
            "variables": {"email": "tester@example.test"},
            "secret_refs": {"password": "secret://vault/project/password"},
        }
    )
    assert value["variable_names"] == ["email"]
    assert value["secret_names"] == ["password"]
    assert value["secret_refs"] == {"password": "[BÍ MẬT]"}
