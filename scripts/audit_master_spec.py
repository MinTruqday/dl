from collections import Counter
import ast
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "AGENTIC_AI_TEST_MANAGEMENT_MASTER_SPEC.md"
BEGIN = "<!-- MASTER_FUNCTION_REGISTRY:BEGIN -->"
END = "<!-- MASTER_FUNCTION_REGISTRY:END -->"
LAYERS = {"ACCOUNT", "ACCOUNT↔PROJECT", "SYSTEM_ADMIN", "PROJECT"}
PRIORITIES = {"P0", "P1", "P2"}
RISKS = {"READ", "MUTATION", "DERIVED/AI", "HUMAN_GATE"}
NO_GRANT = {"", "—", "SERVICE"}
ROLE_SECTIONS = {
    "Lead": ("## MR.3.1. QA_LEAD", "## MR.3.2. TESTER", 7),
    "Tester": ("## MR.3.2. TESTER", "## MR.3.3. BA", 8),
    "BA": ("## MR.3.3. BA", "## MR.3.4. DEVELOPER", 9),
    "Dev": ("## MR.3.4. DEVELOPER", "## MR.3.5. VIEWER", 10),
    "Viewer": ("## MR.3.5. VIEWER", "# MR.4.", 11),
}


def fail(message):
    raise SystemExit(f"master_spec_audit_failed {message}")


def section(text, start, end):
    if text.count(start) != 1:
        fail(f"section_marker={start!r} count={text.count(start)}")
    value = text.split(start, 1)[1]
    if end:
        if end not in value:
            fail(f"section_end_missing={end!r}")
        value = value.split(end, 1)[0]
    return value


def cells(line):
    return [value.strip() for value in line.strip().strip("|").split("|")]


def table_rows(value):
    rows = []
    for line in value.splitlines():
        if not line.startswith("| ") or line.startswith("| ---"):
            continue
        row = cells(line)
        if row[0] in {"ID", "Metric", "Check", "Scope ID", "Entity/Read Model", "Entity"}:
            continue
        rows.append(row)
    return rows


def catalog_rows(value, known_ids):
    return [row for row in table_rows(value) if row[0] in known_ids]


def assert_equal(actual, expected, name):
    if actual != expected:
        fail(f"{name} expected={expected!r} actual={actual!r}")


def assert_id_references(value, ids, owner):
    for reference in value.split(";"):
        token = reference.strip().strip("`")
        if not token:
            fail(f"empty_function_reference owner={owner}")
        if token.endswith("*"):
            prefix = token[:-1]
            if not any(function_id.startswith(prefix) for function_id in ids):
                fail(f"unknown_function_family owner={owner} family={token}")
        elif token not in ids:
            fail(f"unknown_function_id owner={owner} id={token}")


def summary_table(value):
    result = {}
    for row in table_rows(value):
        if len(row) >= 2:
            result[row[0]] = row[1]
    return result


def main():
    if not SPEC.is_file():
        fail("canonical_file_missing")
    duplicates = sorted(
        path.name
        for path in ROOT.glob("AGENTIC_AI_TEST_MANAGEMENT_MASTER_SPEC*.md")
        if path.name != SPEC.name
    )
    if duplicates:
        fail(f"noncanonical_spec_files={duplicates}")
    text = SPEC.read_text(encoding="utf-8")
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        fail("registry_markers_invalid")
    registry_value = text.split(BEGIN, 1)[1].split(END, 1)[0]
    rows = table_rows(registry_value)
    assert_equal(len(rows), 402, "registry_rows")
    if any(len(row) != 17 for row in rows):
        fail("registry_column_count")
    ids = [row[0] for row in rows]
    id_set = set(ids)
    assert_equal(len(id_set), 402, "unique_ids")
    invalid_ids = [value for value in ids if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+", value)]
    if invalid_ids:
        fail(f"invalid_ids={invalid_ids}")
    if any(row[1] not in LAYERS for row in rows):
        fail("invalid_layer")
    if any(not row[5].strip("`") for row in rows):
        fail("empty_permission")
    if any(row[12] not in PRIORITIES for row in rows):
        fail("invalid_priority")
    if any(row[13] not in RISKS for row in rows):
        fail("invalid_risk")
    project_rows = [row for row in rows if row[1] == "PROJECT"]
    if any(all(grant in {"", "—"} for grant in row[7:12]) for row in project_rows):
        fail("project_function_without_grant")
    forbidden_api = []
    for row in rows:
        api_family = row[15]
        if re.search(r"/(?:api|v1)(?:/|\b)", api_family):
            forbidden_api.append((row[0], api_family))
        if re.search(
            r"/(?:projects|membership|test-projects|security-tests|performance-plans)(?:/|\b)",
            api_family,
        ):
            forbidden_api.append((row[0], api_family))
    if forbidden_api:
        fail(f"forbidden_api_families={forbidden_api}")
    by_id = {row[0]: row for row in rows}
    catalog_ids = set()
    catalog_files = sorted(ROOT.glob("backend/*/src/core/function_ids.py"))
    if not catalog_files:
        fail("implementation_function_catalog_missing")
    for function_catalog in catalog_files:
        catalog_tree = ast.parse(
            function_catalog.read_text(encoding="utf-8"), filename=str(function_catalog)
        )
        assignments = [
            node
            for node in catalog_tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id in {"FUNCTION_IDS", "ROUTE_NAME_FUNCTION_IDS"}
                for target in node.targets
            )
        ]
        if not assignments:
            fail(f"implementation_function_catalog_invalid={function_catalog}")
        for assignment in assignments:
            catalog = ast.literal_eval(assignment.value)
            catalog_ids.update(value for values in catalog.values() for value in values)
        service_main = function_catalog.parents[1] / "main.py"
        if not service_main.is_file() or "apply_function_ids(app)" not in service_main.read_text(
            encoding="utf-8"
        ):
            fail(f"implementation_function_catalog_not_applied={function_catalog}")
    unknown_catalog_ids = sorted(catalog_ids - id_set)
    if unknown_catalog_ids:
        fail(f"unknown_implementation_function_ids={unknown_catalog_ids}")
    missing_required_implementation_ids = sorted(
        row[0] for row in rows if row[12] in {"P0", "P1"} and row[0] not in catalog_ids
    )
    if missing_required_implementation_ids:
        fail(f"missing_required_implementation_ids={missing_required_implementation_ids}")
    missing_extension_ids = sorted(
        row[0] for row in rows if row[12] == "P2" and row[0] not in catalog_ids
    )
    layer_counts = Counter(row[1] for row in rows)
    priority_counts = Counter(row[12] for row in rows)
    risk_counts = Counter(row[13] for row in rows)
    role_counts = {
        name: sum(row[column] not in NO_GRANT for row in rows)
        for name, (_, _, column) in ROLE_SECTIONS.items()
    }
    expected_summary = {
        "Total canonical Function IDs": "402",
        "Unique Function IDs": "402",
        "Account/Public actions": str(layer_counts["ACCOUNT"] + layer_counts["ACCOUNT↔PROJECT"]),
        "System Admin actions": str(layer_counts["SYSTEM_ADMIN"]),
        "Project actions": str(layer_counts["PROJECT"]),
        "P0 actions": str(priority_counts["P0"]),
        "P1 actions": str(priority_counts["P1"]),
        "P2 actions": str(priority_counts["P2"]),
        "QA_LEAD derived actions": str(role_counts["Lead"]),
        "TESTER derived actions": str(role_counts["Tester"]),
        "BA derived actions": str(role_counts["BA"]),
        "DEVELOPER derived actions": str(role_counts["Dev"]),
        "VIEWER derived actions": str(role_counts["Viewer"]),
    }
    summary_value = section(text, "## MR.0.4. Registry summary", "## MR.1.")
    assert_equal(summary_table(summary_value), expected_summary, "registry_summary")
    account_value = section(text, "## MR.2. Account/Public/Membership self-service", "# MR.3.")
    account_rows = catalog_rows(account_value, id_set)
    expected_account_ids = {
        row[0] for row in rows if row[1] in {"ACCOUNT", "ACCOUNT↔PROJECT"}
    }
    assert_equal({row[0] for row in account_rows}, expected_account_ids, "account_catalog_ids")
    for row in account_rows:
        source = by_id[row[0]]
        assert_equal(row[5].strip("`"), source[5].strip("`"), f"account_permission_{row[0]}")
        assert_equal(row[7], source[12], f"account_priority_{row[0]}")
    admin_value = section(text, "## MR.3.0. SYSTEM_ADMIN", "## MR.3.1.")
    admin_rows = catalog_rows(admin_value, id_set)
    expected_admin_ids = {row[0] for row in rows if row[1] == "SYSTEM_ADMIN"}
    assert_equal({row[0] for row in admin_rows}, expected_admin_ids, "admin_catalog_ids")
    for row in admin_rows:
        source = by_id[row[0]]
        assert_equal(row[4].strip("`"), source[5].strip("`"), f"admin_permission_{row[0]}")
        assert_equal(row[5], source[12], f"admin_priority_{row[0]}")
        assert_equal(row[6], source[13], f"admin_risk_{row[0]}")
    for role, (start, end, column) in ROLE_SECTIONS.items():
        value = section(text, start, end)
        catalog = catalog_rows(value, id_set)
        expected_ids = {row[0] for row in rows if row[column] not in NO_GRANT}
        assert_equal({row[0] for row in catalog}, expected_ids, f"{role}_catalog_ids")
        for row in catalog:
            source = by_id[row[0]]
            assert_equal(row[3].strip("`"), source[5].strip("`"), f"{role}_permission_{row[0]}")
            assert_equal(row[4], source[column], f"{role}_grant_{row[0]}")
            assert_equal(row[5], source[12], f"{role}_priority_{row[0]}")
    scope_rows = table_rows(section(text, "# MR.4.", "# MR.5."))
    assert_equal(len(scope_rows), 44, "declared_scope_count")
    for row in scope_rows:
        assert_equal(row[4], "PASS", f"scope_status_{row[0]}")
        assert_equal(row[5], "", f"scope_missing_{row[0]}")
        assert_id_references(row[3], id_set, row[0])
    entity_rows = table_rows(section(text, "# MR.5.", "# MR.6."))
    assert_equal(len(entity_rows), 25, "entity_closure_count")
    for row in entity_rows:
        assert_equal(row[3], "PASS", f"entity_status_{row[0]}")
        assert_equal(row[4], "", f"entity_missing_{row[0]}")
        assert_id_references(row[1], id_set, row[0])
    state_rows = table_rows(section(text, "# MR.6.", "# MR.7."))
    assert_equal(len(state_rows), 12, "state_closure_count")
    for row in state_rows:
        assert_equal(row[3], "PASS", f"state_status_{row[0]}")
        assert_id_references(row[2], id_set, row[0])
    gate_rows = table_rows(
        section(text, "# MR.10. AUTOMATED COMPLETENESS GATE — CURRENT RESULT", "### MR.10.1.")
    )
    gate = {row[0]: row[1:] for row in gate_rows}
    expected_gate = {
        "Registry rows": ["402", "PASS"],
        "Unique IDs": ["402", "PASS"],
        "Duplicate IDs": ["0", "PASS"],
        "Empty permissions": ["0", "PASS"],
        "Invalid priorities": ["0", "PASS"],
        "Project rows without any grant": ["0", "PASS"],
        "Declared scope capabilities checked": ["44", "PASS"],
        "Declared scope failures": ["0", "PASS"],
        "Entity closure failures": ["0", "PASS"],
        "State closure failures": ["0", "PASS"],
        "Unmapped cross-cutting permission tokens from prior canonical AJ": ["0", "PASS"],
    }
    assert_equal(gate, expected_gate, "documented_gate_result")
    print(
        "master_spec_audit_passed "
        f"registry={len(rows)} scope={len(scope_rows)} entities={len(entity_rows)} "
        f"states={len(state_rows)} implemented={len(catalog_ids)} "
        f"missing_p2={len(missing_extension_ids)} risks={dict(sorted(risk_counts.items()))}"
    )


if __name__ == "__main__":
    main()
