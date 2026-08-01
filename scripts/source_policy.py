import ast
import io
import json
import pathlib
import re
import subprocess
import sys
import tokenize


ROOT = pathlib.Path(__file__).resolve().parents[1]
PYTHON_SUFFIXES = {".py"}
WEB_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".css", ".scss"}
CONFIG_SUFFIXES = {".yaml", ".yml", ".sh"}
TEXTUAL_ELLIPSIS = "." * 3
UNICODE_ELLIPSIS = chr(0x2026)


def tracked_files():
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    for raw_name in result.stdout.split(b"\0"):
        if not raw_name:
            continue
        path = ROOT / raw_name.decode()
        if path.is_file():
            yield path


def is_emoji(character):
    value = ord(character)
    return (
        0x1F000 <= value <= 0x1FAFF
        or 0x2600 <= value <= 0x27BF
        or value == 0xFE0F
    )


def add_text_issues(path, line, text, issues):
    if TEXTUAL_ELLIPSIS in text or UNICODE_ELLIPSIS in text:
        issues.append((path, line, "textual_ellipsis"))
    if any(is_emoji(character) for character in text):
        issues.append((path, line, "emoji"))


def scan_python(path, source, issues):
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type == tokenize.COMMENT:
                issues.append((path, token.start[0], "comment"))
    except tokenize.TokenError as error:
        issues.append((path, 1, f"tokenize_error:{error}"))
        return
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        issues.append((path, error.lineno or 1, "syntax_error"))
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            add_text_issues(path, node.lineno, node.value, issues)
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {
            "debug",
            "info",
            "warning",
            "error",
            "exception",
            "critical",
        }:
            continue
        if not node.args:
            continue
        message = node.args[0]
        if (
            len(node.args) == 1
            and isinstance(message, ast.Constant)
            and isinstance(message.value, str)
            and "{" in message.value
        ):
            issues.append((path, message.lineno, "uninterpolated_log"))
        try:
            rendered = ast.unparse(message)
        except Exception:
            rendered = ""
        lowered = rendered.lower()
        if "successfully" in lowered:
            issues.append((path, message.lineno, "verbose_success_log"))
        if "str(" in rendered and "error" in lowered:
            issues.append((path, message.lineno, "raw_exception_log"))


def scan_web(path, source, issues):
    index = 0
    line = 1
    length = len(source)
    while index < length:
        character = source[index]
        following = source[index + 1] if index + 1 < length else ""
        if character == "\n":
            line += 1
            index += 1
            continue
        if character == "/" and following == "/":
            issues.append((path, line, "comment"))
            index += 2
            while index < length and source[index] != "\n":
                index += 1
            continue
        if character == "/" and following == "*":
            issues.append((path, line, "comment"))
            index += 2
            while index < length:
                if source[index] == "\n":
                    line += 1
                if source[index] == "*" and index + 1 < length and source[index + 1] == "/":
                    index += 2
                    break
                index += 1
            continue
        if character == "/" and following not in {"", "/", "*"}:
            prior_index = index - 1
            while prior_index >= 0 and source[prior_index].isspace():
                prior_index -= 1
            prior = source[prior_index] if prior_index >= 0 else ""
            if prior in {"", "(", "=", ",", "[", "!", "?", ":", ";", "{"}:
                index += 1
                in_character_class = False
                while index < length:
                    character = source[index]
                    if character == "\\":
                        index += 2
                        continue
                    if character == "[":
                        in_character_class = True
                    elif character == "]":
                        in_character_class = False
                    elif character == "/" and not in_character_class:
                        index += 1
                        while index < length and source[index].isalpha():
                            index += 1
                        break
                    if character == "\n":
                        break
                    index += 1
                continue
        if character in {'"', "'", "`"}:
            if character == "'" and index > 0 and source[index - 1].isalnum():
                index += 1
                continue
            delimiter = character
            string_line = line
            value = []
            index += 1
            while index < length:
                character = source[index]
                if character == "\\":
                    if index + 1 < length:
                        value.extend((character, source[index + 1]))
                        index += 2
                        continue
                if character == delimiter:
                    index += 1
                    break
                if character == "\n":
                    line += 1
                value.append(character)
                index += 1
            add_text_issues(path, string_line, "".join(value), issues)
            continue
        index += 1
    for line_number, text in enumerate(source.splitlines(), 1):
        if UNICODE_ELLIPSIS in text or any(is_emoji(character) for character in text):
            add_text_issues(path, line_number, text, issues)


def scan_config(path, source, issues):
    for line_number, text in enumerate(source.splitlines(), 1):
        if text.lstrip().startswith("#"):
            issues.append((path, line_number, "comment"))
        add_text_issues(path, line_number, text, issues)


def scan_compilation_registry(issues):
    component_root = (
        ROOT / "frontend" / "features" / "compilation" / "components"
    )
    editor_path = component_root / "StandardEditor.tsx"
    if not editor_path.is_file():
        issues.append((editor_path.relative_to(ROOT), 1, "editor_registry_missing"))
        return
    source = editor_path.read_text(encoding="utf-8")
    relative_editor = editor_path.relative_to(ROOT)
    if "require as any" in source or ".context(" in source:
        issues.append((relative_editor, 1, "unbounded_component_registry"))
    if "WORD_COMMAND_TOOLS" not in source:
        issues.append((relative_editor, 1, "word_command_tools_not_registered"))
    component_names = set(
        re.findall(r'await import\("\./(DocLib[^"/]+)"\)', source)
    )
    for component_name in sorted(component_names):
        component_path = component_root / f"{component_name}.ts"
        if not component_path.is_file():
            issues.append(
                (
                    relative_editor,
                    1,
                    f"registered_component_missing:{component_name}",
                )
            )
            continue
        component_source = component_path.read_text(encoding="utf-8")
        if "export default" not in component_source:
            issues.append(
                (
                    component_path.relative_to(ROOT),
                    1,
                    "component_default_export_missing",
                )
            )
        if "implements BlockTool" in component_source:
            for contract in ("toolbox", "render(", "save("):
                if contract not in component_source:
                    issues.append(
                        (
                            component_path.relative_to(ROOT),
                            1,
                            f"block_tool_contract_missing:{contract}",
                        )
                    )
        if "implements InlineTool" in component_source:
            for contract in ("render(", "surround("):
                if contract not in component_source:
                    issues.append(
                        (
                            component_path.relative_to(ROOT),
                            1,
                            f"inline_tool_contract_missing:{contract}",
                        )
                    )
        if "implements BlockTune" in component_source:
            for contract in ("render(", "save("):
                if contract not in component_source:
                    issues.append(
                        (
                            component_path.relative_to(ROOT),
                            1,
                            f"block_tune_contract_missing:{contract}",
                        )
                    )
        if (
            "implements BlockTool" not in component_source
            and "implements InlineTool" not in component_source
            and "implements BlockTune" not in component_source
            and "render(" not in component_source
            and "destroy(" not in component_source
        ):
            issues.append(
                (
                    component_path.relative_to(ROOT),
                    1,
                    "component_behavior_contract_missing",
                )
            )
        if (
            "private data: { content: string }" in component_source
            and len(component_source.splitlines()) < 60
        ):
            issues.append(
                (
                    component_path.relative_to(ROOT),
                    1,
                    "generic_component_registered",
                )
            )
    catalog_path = component_root / "word-command-catalog.ts"
    if not catalog_path.is_file():
        issues.append(
            (
                catalog_path.relative_to(ROOT),
                1,
                "word_command_catalog_missing",
            )
        )
        return
    catalog_source = catalog_path.read_text(encoding="utf-8")
    command_imports = re.findall(
        r'^import (DocLib[A-Za-z0-9]+) from "\./(DocLib[A-Za-z0-9]+)";$',
        catalog_source,
        re.M,
    )
    command_names = [name for name, target in command_imports if name == target]
    mismatched_imports = len(command_imports) - len(command_names)
    command_entries = re.findall(
        r"^wordCommandClasses\.push\((DocLib[A-Za-z0-9]+)\);$",
        catalog_source,
        re.M,
    )
    duplicate_commands = len(command_names) - len(set(command_names))
    overlap = component_names.intersection(command_names)
    feature_names = {
        path.stem for path in component_root.glob("DocLib*.ts")
    }
    registered_features = component_names.union(command_names)
    total_features = len(feature_names)
    if len(component_names) != 153:
        issues.append(
            (
                relative_editor,
                1,
                f"editor_component_count:{len(component_names)}",
            )
        )
    if len(command_names) != 2296:
        issues.append(
            (
                catalog_path.relative_to(ROOT),
                1,
                f"word_command_count:{len(command_names)}",
            )
        )
    if mismatched_imports:
        issues.append(
            (
                catalog_path.relative_to(ROOT),
                1,
                f"word_command_import_mismatch:{mismatched_imports}",
            )
        )
    if len(command_entries) != 2296 or set(command_entries) != set(command_names):
        issues.append(
            (
                catalog_path.relative_to(ROOT),
                1,
                f"word_command_registry_mismatch:{len(command_entries)}",
            )
        )
    if duplicate_commands:
        issues.append(
            (
                catalog_path.relative_to(ROOT),
                1,
                f"word_command_duplicates:{duplicate_commands}",
            )
        )
    if overlap:
        issues.append(
            (
                catalog_path.relative_to(ROOT),
                1,
                f"word_feature_overlap:{len(overlap)}",
            )
        )
    if total_features != 2449:
        issues.append(
            (
                catalog_path.relative_to(ROOT),
                1,
                f"word_feature_total:{total_features}",
            )
        )
    if registered_features != feature_names:
        issues.append(
            (
                catalog_path.relative_to(ROOT),
                1,
                f"word_feature_file_registry_mismatch:{len(feature_names.symmetric_difference(registered_features))}",
            )
        )
    for command_name in sorted(set(command_names)):
        command_path = component_root / f"{command_name}.ts"
        if not command_path.is_file():
            issues.append(
                (
                    catalog_path.relative_to(ROOT),
                    1,
                    f"word_command_file_missing:{command_name}",
                )
            )
            continue
        command_source = command_path.read_text(encoding="utf-8")
        command_contracts = (
            'import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";',
            f"export default class {command_name}",
            "implements BlockTool",
            "static get toolbox()",
            f'readonly id = "{command_name}";',
            "readonly title = ",
            "readonly category = ",
            "readonly mode = ",
            "readonly requiresSelection = ",
            "constructor(",
            "render()",
            "save(blockContent: HTMLElement)",
            "validate(savedData: BlockToolData)",
            "async execute(editor: any)",
        )
        for contract in command_contracts:
            if contract not in command_source:
                issues.append(
                    (
                        command_path.relative_to(ROOT),
                        1,
                        f"word_command_file_contract:{contract}",
                    )
                )
        if (
            'from "./word-command-engine"' in command_source
            or "createWordCommand" in command_source
        ):
            issues.append(
                (
                    command_path.relative_to(ROOT),
                    1,
                    "word_command_wrapper_import",
                )
            )
        if len(command_source.splitlines()) < 60:
            issues.append(
                (
                    command_path.relative_to(ROOT),
                    1,
                    "word_command_file_behavior_missing",
                )
            )
    manifest_path = component_root / "word-feature-manifest.json"
    if not manifest_path.is_file():
        issues.append(
            (
                manifest_path.relative_to(ROOT),
                1,
                "word_feature_manifest_missing",
            )
        )
        return
    try:
        manifest_source = manifest_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_source)
        records = manifest["features"]
    except (json.JSONDecodeError, KeyError, TypeError):
        issues.append(
            (
                manifest_path.relative_to(ROOT),
                1,
                "word_feature_manifest_invalid",
            )
        )
        return
    backend_manifest_path = (
        ROOT
        / "backend"
        / "compilation"
        / "src"
        / "resources"
        / "word-feature-manifest.json"
    )
    if (
        not backend_manifest_path.is_file()
        or backend_manifest_path.read_text(encoding="utf-8") != manifest_source
    ):
        issues.append(
            (
                backend_manifest_path.relative_to(ROOT),
                1,
                "word_feature_backend_manifest_mismatch",
            )
        )
    record_ids = [record.get("id") for record in records]
    record_titles = [record.get("title") for record in records]
    record_icons = [record.get("icon") for record in records]
    command_records = [
        record
        for record in records
        if record.get("toolKey") is not None
    ]
    if len(records) != 2449 or set(record_ids) != feature_names:
        issues.append(
            (
                manifest_path.relative_to(ROOT),
                1,
                f"word_feature_manifest_count:{len(records)}",
            )
        )
    if len(set(record_ids)) != 2449:
        issues.append(
            (
                manifest_path.relative_to(ROOT),
                1,
                "word_feature_manifest_duplicate_id",
            )
        )
    if (
        len(set(record_icons)) != 2449
        or any(not isinstance(icon, str) or "<svg" not in icon for icon in record_icons)
    ):
        issues.append(
            (
                manifest_path.relative_to(ROOT),
                1,
                "word_feature_icons_not_unique",
            )
        )
    if any(
        not isinstance(title, str) or not title.startswith("DocLib ")
        for title in record_titles
    ):
        issues.append(
            (
                manifest_path.relative_to(ROOT),
                1,
                "word_feature_title_prefix_missing",
            )
        )
    if any(record.get("product") != "doclib" for record in records):
        issues.append(
            (
                manifest_path.relative_to(ROOT),
                1,
                "word_feature_product_mismatch",
            )
        )
    legacy_fields = {
        "microsoftControlId",
        "microsoftInteractiveControlCount",
        "controlType",
        "tab",
        "group",
        "source",
        "sourceSha256",
    }
    if legacy_fields.intersection(manifest) or any(
        legacy_fields.intersection(record) for record in records
    ):
        issues.append(
            (
                manifest_path.relative_to(ROOT),
                1,
                "word_feature_legacy_metadata",
            )
        )
    if (
        len(command_records) != 2296
        or len({record.get("toolKey") for record in command_records}) != 2296
        or any(not record.get("mode") for record in command_records)
    ):
        issues.append(
            (
                manifest_path.relative_to(ROOT),
                1,
                f"word_feature_tool_mapping:{len(command_records)}",
            )
        )
    for record in records:
        feature_path = component_root / f"{record.get('id')}.ts"
        if not feature_path.is_file():
            continue
        feature_source = feature_path.read_text(encoding="utf-8")
        for marker, issue in (
            ("static readonly feature = ", "word_feature_metadata_missing"),
            (record.get("title"), "word_feature_title_mismatch"),
            (record.get("icon"), "word_feature_icon_mismatch"),
        ):
            if not marker or marker not in feature_source:
                issues.append(
                    (
                        feature_path.relative_to(ROOT),
                        1,
                        issue,
                    )
                )


def scan_fail_open_contracts(issues):
    forbidden = {
        "issued_fallback": "fabricated_security_success",
        "Fingerprint verified fallback": "fabricated_security_success",
        "DRM AES key HTTP fallback": "fabricated_security_success",
        "DRM trust profile HTTP fallback": "fabricated_security_success",
        "DRM document risk HTTP fallback": "fabricated_security_success",
        "Redis idempotency lock bypass": "financial_lock_bypass",
        "[Dịch tự động": "fabricated_ai_result",
        '"replies": ["Đã rõ thông tin"': "fabricated_ai_result",
    }
    roots = [
        ROOT / "backend" / "agentic_ai" / "src",
        ROOT / "backend" / "drm" / "src",
        ROOT / "backend" / "finance" / "src",
        ROOT / "backend" / "messaging" / "src",
    ]
    for root in roots:
        for path in root.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            for marker, issue in forbidden.items():
                if marker in source:
                    line = source[: source.index(marker)].count("\n") + 1
                    issues.append((path.relative_to(ROOT), line, issue))
def main():
    issues = []
    for path in tracked_files():
        suffix = path.suffix.lower()
        if suffix not in PYTHON_SUFFIXES | WEB_SUFFIXES | CONFIG_SUFFIXES and not path.name.startswith("Dockerfile"):
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative_path = path.relative_to(ROOT)
        if suffix in PYTHON_SUFFIXES:
            scan_python(relative_path, source, issues)
        elif suffix in WEB_SUFFIXES:
            scan_web(relative_path, source, issues)
        else:
            scan_config(relative_path, source, issues)
    scan_fail_open_contracts(issues)
    for path, line, issue in sorted(set(issues), key=lambda item: (str(item[0]), item[1], item[2])):
        print(f"{path}:{line}:{issue}")
    if issues:
        return 1
    print("source_policy_passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
