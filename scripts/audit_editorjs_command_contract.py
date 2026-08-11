import importlib.util
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
CAPABILITIES = (
    ROOT / "backend/compilation/src/engines/editorjs_capabilities.py"
)
FRONTEND_ENGINE = (
    ROOT / "frontend/features/compilation/components/document-command-engine.ts"
)
AGENTIC_TOOL = ROOT / "backend/agentic_ai/src/tools/document.py"


def load_capabilities_module():
    spec = importlib.util.spec_from_file_location(
        "doclib_editorjs_capabilities", CAPABILITIES
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Không thể nạp contract compilation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_typescript_set(source: str, name: str):
    match = re.search(
        rf"const {re.escape(name)} = new Set\(\[(.*?)\]\);",
        source,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"Không tìm thấy registry {name}")
    return set(re.findall(r'"(DocLib[A-Za-z0-9]+)"', match.group(1)))


def main():
    issues = []
    module = load_capabilities_module()
    frontend_source = FRONTEND_ENGINE.read_text(encoding="utf-8")
    agentic_source = AGENTIC_TOOL.read_text(encoding="utf-8")
    backend_ids = set(module.VERIFIED_PERSISTENT_COMMANDS)
    backend_structure_ids = set(module.VERIFIED_STRUCTURE_COMMANDS)
    backend_text_ids = set(module.VERIFIED_TEXT_COMMANDS)
    backend_block_ids = set(module.VERIFIED_BLOCK_COMMANDS)
    backend_analysis_ids = set(module.VERIFIED_ANALYSIS_COMMANDS)
    frontend_persistent = extract_typescript_set(
        frontend_source, "verifiedPersistentCommands"
    )
    frontend_interactive = extract_typescript_set(
        frontend_source, "verifiedInteractiveCommands"
    )
    if backend_ids != frontend_persistent:
        issues.append("persistent_registry_mismatch")
    if not frontend_persistent <= frontend_interactive:
        issues.append("persistent_command_not_interactive")
    if not backend_structure_ids <= frontend_interactive:
        issues.append("structure_command_not_interactive")
    if not backend_text_ids <= frontend_interactive:
        issues.append("text_command_not_interactive")
    if not backend_analysis_ids <= frontend_interactive:
        issues.append("analysis_command_not_interactive")
    expected_frontend_interactive = (
        backend_ids
        | backend_structure_ids
        | backend_text_ids
        | backend_analysis_ids
        | {"DocLibReadAloud"}
    )
    if frontend_interactive != expected_frontend_interactive:
        issues.append("frontend_interactive_registry_not_exact")
    highlight_commands = {
        command_id
        for command_id in backend_text_ids
        if "highlight" in command_id.lower()
    }
    if highlight_commands != {"DocLibTextHighlightColorPicker"}:
        issues.append("highlight_commands_are_duplicated")
    if "import(`./${command.id}`)" in frontend_source:
        issues.append("frontend_dynamic_command_bridge_present")
    if "Đã thực hiện ${command.title}" in frontend_source:
        issues.append("frontend_unverified_success_message_present")
    if "document_command_not_verified" not in agentic_source:
        issues.append("agentic_verification_gate_missing")
    if (
        '"persistent_document_command"' not in agentic_source
        or '"document_structure_command"' not in agentic_source
    ):
        issues.append("agentic_execution_kind_gate_missing")

    valid_payload = {
        "documentCommandState": {
            "schemaVersion": 1,
            "commands": {
                "DocLibColumnsTwo": {
                    "mode": "ColumnsTwo",
                    "enabled": True,
                    "appliedAt": 1,
                    "parameters": {"count": 2},
                },
                "DocLibDraftView": {
                    "mode": "DraftView",
                    "enabled": True,
                    "appliedAt": 2,
                },
                "DocLibLineSpacing": {
                    "mode": "LineSpacing",
                    "enabled": True,
                    "appliedAt": 3,
                    "parameters": {"value": 2},
                },
                "DocLibOrientation": {
                    "mode": "Orientation",
                    "enabled": True,
                    "appliedAt": 4,
                    "parameters": {"value": "landscape"},
                },
                "DocLibPaperSize": {
                    "mode": "PaperSize",
                    "enabled": True,
                    "appliedAt": 5,
                    "parameters": {"value": "Legal"},
                },
            },
        }
    }
    state = module.validate_document_command_state(valid_payload)
    if set(state["commands"]) != {
        "DocLibColumnsTwo",
        "DocLibLineSpacing",
        "DocLibOrientation",
        "DocLibPaperSize",
    }:
        issues.append("legacy_unverified_command_not_pruned")
    invalid_payload = {
        "documentCommandState": {
            "commands": {
                "DocLibColumnsTwo": {
                    "mode": "ColumnsTwo",
                    "enabled": True,
                    "appliedAt": 1,
                    "parameters": {"count": 3},
                }
            }
        }
    }
    try:
        module.validate_document_command_state(invalid_payload)
        issues.append("invalid_command_parameters_accepted")
    except ValueError:
        pass

    if issues:
        print("\n".join(issues))
        return 1
    print(
        "editorjs_command_contract_audit_passed "
        f"persistent={len(backend_ids)} structure={len(backend_structure_ids)} "
        f"text={len(backend_text_ids)} block={len(backend_block_ids)} "
        f"analysis={len(backend_analysis_ids)} "
        f"interactive={len(frontend_interactive)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
