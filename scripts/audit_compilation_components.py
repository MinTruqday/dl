import json
import pathlib
import re
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "frontend/features/compilation/components"
EDITOR = COMPONENTS / "StandardEditor.tsx"
CATALOG = COMPONENTS / "document-command-catalog.generated.json"
ENGINE = COMPONENTS / "document-command-engine.ts"


def main():
    issues = []
    component_files = sorted(COMPONENTS.glob("DocLib*.ts"))
    editor_source = EDITOR.read_text(encoding="utf-8")
    engine_source = ENGINE.read_text(encoding="utf-8")
    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        catalog = []
        issues.append("catalog_invalid")
    ids = [entry.get("id") for entry in catalog]
    if len(component_files) != 2449:
        issues.append(f"component_count:{len(component_files)}")
    if len(catalog) != 2296:
        issues.append(f"command_count:{len(catalog)}")
    if len(ids) != len(set(ids)):
        issues.append("duplicate_command_id")
    missing = [command_id for command_id in ids if not (COMPONENTS / f"{command_id}.ts").is_file()]
    if missing:
        issues.append(f"missing_command_files:{len(missing)}")
    if "DocumentCommandPalette" not in (COMPONENTS / "EditorWorkspace.tsx").read_text(encoding="utf-8"):
        issues.append("command_palette_unreachable")
    if "documentCommandState" not in editor_source:
        issues.append("command_state_not_persisted")
    event_names = set(re.findall(r'CustomEvent\("(doclib-[^"]+)"', "\n".join(path.read_text(encoding="utf-8") for path in component_files)))
    missing_events = sorted(event for event in event_names if f'"{event}"' not in engine_source)
    if missing_events:
        issues.append(f"unhandled_events:{','.join(missing_events)}")
    result = subprocess.run(
        ["node", "scripts/audit-document-components.mjs"],
        cwd=ROOT / "frontend",
        capture_output=True,
        text=True,
    )
    if result.returncode:
        issues.append(result.stderr.strip() or "runtime_audit_failed")
    if issues:
        print("\n".join(issues))
        return 1
    print(f"compilation_component_audit_passed components={len(component_files)} commands={len(catalog)} events={len(event_names)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
