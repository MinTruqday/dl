import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "frontend/features/compilation/components"
EDITOR = COMPONENTS / "StandardEditor.tsx"
PLUGINS = {"DocLibDragDrop", "DocLibMultiBlockSelection", "DocLibUndo"}
VIETNAMESE = re.compile(r"[À-ỹ]")


def component_source(name):
    for suffix in (".ts", ".tsx"):
        path = COMPONENTS / f"{name}{suffix}"
        if path.is_file():
            return path, path.read_text(encoding="utf-8")
    return None, ""


def main():
    issues = []
    files = sorted([*COMPONENTS.glob("*.ts"), *COMPONENTS.glob("*.tsx")])
    editor_source = EDITOR.read_text(encoding="utf-8")
    imports = re.findall(
        r'const (DocLib\w+) = \(await import\("\./(DocLib\w+)"\)\)',
        editor_source,
    )
    imported_names = [name for name, module in imports]
    imported_modules = [module for name, module in imports]
    wired = set(
        re.findall(
            r"tools\.\w+\s*=\s*(?:\{\s*class:\s*)?(DocLib\w+)",
            editor_source,
        )
    )
    wired.update(re.findall(r"new (DocLib\w+)", editor_source))
    tool_keys = re.findall(r"tools\.(\w+)\s*=", editor_source)
    component_classes = []

    for name in sorted(set(imported_names) - wired):
        issues.append((EDITOR, f"unwired_import:{name}"))
    for name in sorted({name for name in tool_keys if tool_keys.count(name) > 1}):
        issues.append((EDITOR, f"duplicate_tool_key:{name}"))
    for module in imported_modules:
        path, source = component_source(module)
        if path is None:
            issues.append((EDITOR, f"missing_component:{module}"))

    for path in files:
        source = path.read_text(encoding="utf-8")
        if VIETNAMESE.search(source):
            issues.append((path, "vietnamese_text"))
        if "TODO" in source or "FIXME" in source:
            issues.append((path, "unfinished_marker"))
        if not re.search(r"export\s+default\s+class", source):
            continue
        name = path.stem
        if name in PLUGINS:
            continue
        component_classes.append(name)
        if "isInline" in source or "isTune" in source:
            continue
        for member in ("toolbox", "render", "save"):
            if member not in source:
                issues.append((path, f"missing_contract:{member}"))

    inactive_classes = set(component_classes) - set(imported_modules)
    if inactive_classes and "(require as any).context(" not in editor_source:
        issues.append((EDITOR, f"unreachable_components:{len(inactive_classes)}"))

    for path, issue in issues:
        print(f"{path.relative_to(ROOT)}:{issue}")
    if issues:
        return 1
    print(
        f"compilation_component_audit_passed files={len(files)} "
        f"components={len(component_classes)} direct={len(imports) - len(PLUGINS)} "
        f"registry={len(inactive_classes)} tools={len(tool_keys)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
