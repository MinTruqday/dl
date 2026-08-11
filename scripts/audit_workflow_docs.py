"""Verify architecture guides remain linked to the implemented service contracts."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTIC_GUIDE = ROOT / "agentic_ai_workflow_and_architecture_guide_3.md"
DRM_GUIDE = ROOT / "drm_full_workflow_guide.md"
COMPILATION_GUIDE = ROOT / "compilation_workflow_and_architecture_guide.md"
WATERMARK_SOURCE = ROOT / "backend/drm/src/services/watermark.py"
COMPILATION_COMPONENTS = ROOT / "frontend/features/compilation/components"
STANDARD_EDITOR = COMPILATION_COMPONENTS / "StandardEditor.tsx"
COMMAND_PALETTE = COMPILATION_COMPONENTS / "DocumentCommandPalette.tsx"
COMMAND_ENGINE = COMPILATION_COMPONENTS / "document-command-engine.ts"
COMMAND_CATALOG = COMPILATION_COMPONENTS / "document-command-catalog.generated.json"
FRONTEND_FEATURE_MANIFEST = COMPILATION_COMPONENTS / "word-feature-manifest.json"
BACKEND_FEATURE_MANIFEST = (
    ROOT / "backend/compilation/src/resources/word-feature-manifest.json"
)
EDITORJS_SERVICE = ROOT / "frontend/features/compilation/services/editorjs.service.ts"
EDITOR_WORKSPACE_HOOK = (
    ROOT / "frontend/features/compilation/hooks/useEditorWorkspace.ts"
)


def _mermaid_blocks(text: str) -> list[str]:
    parts = text.split("```mermaid")
    blocks = []
    for part in parts[1:]:
        if "```" not in part:
            raise AssertionError("mermaid_fence_not_closed")
        blocks.append(part.split("```", 1)[0].strip())
    return blocks


def _load_extension_function():
    tree = ast.parse(WATERMARK_SOURCE.read_text(encoding="utf-8"))
    function = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "protected_extension_for_format"
        ),
        None,
    )
    if function is None:
        raise AssertionError("protected_extension_function_missing")
    module = ast.Module(body=[function], type_ignores=[])
    namespace: dict[str, object] = {}
    exec(compile(module, str(WATERMARK_SOURCE), "exec"), namespace)
    return namespace["protected_extension_for_format"]


def main() -> None:
    agentic = AGENTIC_GUIDE.read_text(encoding="utf-8")
    drm = DRM_GUIDE.read_text(encoding="utf-8")
    compilation = COMPILATION_GUIDE.read_text(encoding="utf-8")

    for guide_name, text, minimum_diagrams in (
        ("agentic_ai", agentic, 8),
        ("drm", drm, 8),
        ("compilation", compilation, 10),
    ):
        assert "file:///" not in text, f"{guide_name}_contains_absolute_file_uri"
        assert "## Công nghệ" in text or "Công nghệ đang sử dụng" in text
        blocks = _mermaid_blocks(text)
        assert len(blocks) >= minimum_diagrams, f"{guide_name}_diagram_coverage_too_small"
        assert all(block.startswith("flowchart") for block in blocks)

        for index, workflow in enumerate(blocks[1:], start=1):
            prefix = f"{guide_name}_workflow_{index}"
            assert workflow.startswith("flowchart TD"), f"{prefix}_must_flow_top_down"
            assert "Bắt đầu" in workflow, f"{prefix}_missing_start_terminal"
            assert "Kết thúc" in workflow, f"{prefix}_missing_end_terminal"
            assert re.search(r"\{[^{}]+\}", workflow), f"{prefix}_missing_decision"
            visible_labels = []
            for line in workflow.splitlines():
                visible_labels.extend(re.findall(r"\[([^\[\]]+)\]", line))
                visible_labels.extend(re.findall(r"\{([^{}]+)\}", line))
                visible_labels.extend(re.findall(r"\|([^|]+)\|", line))
            assert not any(
                re.search(r"[,\.:;?!…]", label) for label in visible_labels
            ), f"{prefix}_contains_sentence_punctuation"
            assert "-->|Có|" in workflow or "-->|Không|" in workflow, (
                f"{prefix}_missing_named_decision_branch"
            )

    for required in (
        "LangGraph",
        "Ollama",
        "MongoDB",
        "Redis",
        "Qdrant",
        "MCP",
        "Reqwise Figma",
        "Chrome DevTools",
        "Fine-tuning",
        "Supervisor DAG",
    ):
        assert required in agentic, f"agentic_technology_or_workflow_missing:{required}"

    for required in (
        "AES-256-GCM",
        "RSA-OAEP",
        "PyMuPDF",
        "Content service",
        "Finance service",
        "Humanity service",
        "`.doclib`",
        "`.doclibx`",
    ):
        assert required in drm, f"drm_technology_or_workflow_missing:{required}"

    for required in (
        "Editor.js",
        "Tectonic",
        "WeasyPrint",
        "Pandoc",
        "2.449",
        "2.296",
        "347",
        "1.949",
        "55",
        "document-command-catalog.generated.json",
        "`.doclib`",
        "`.doclibx`",
    ):
        assert required in compilation, (
            f"compilation_technology_or_workflow_missing:{required}"
        )

    standard_editor = STANDARD_EDITOR.read_text(encoding="utf-8")
    palette = COMMAND_PALETTE.read_text(encoding="utf-8")
    catalog = json.loads(COMMAND_CATALOG.read_text(encoding="utf-8"))
    frontend_manifest_source = FRONTEND_FEATURE_MANIFEST.read_text(encoding="utf-8")
    backend_manifest_source = BACKEND_FEATURE_MANIFEST.read_text(encoding="utf-8")
    feature_manifest = json.loads(frontend_manifest_source)
    labels = set(re.findall(r"^  (DocLib[A-Za-z0-9]+):", palette, re.MULTILINE))
    command_engine = COMMAND_ENGINE.read_text(encoding="utf-8")
    verified_match = re.search(
        r"const verifiedInteractiveCommands = new Set\(\[(.*?)\]\);",
        command_engine,
        re.DOTALL,
    )
    assert verified_match is not None
    verified_ids = set(
        re.findall(r'"(DocLib[A-Za-z0-9]+)"', verified_match.group(1))
    )
    visible_commands = [
        command
        for command in catalog
        if command["id"] in labels
        and command["id"] in verified_ids
    ]
    assert standard_editor.count('import("./DocLib') == 31
    assert 'import("./DocLibMacroButton")' not in standard_editor
    assert len(catalog) == 2296
    assert sum(command["implementation"] == "direct" for command in catalog) == 347
    assert sum(command["implementation"] == "bridge" for command in catalog) == 1949
    assert len(visible_commands) == 55
    assert len(feature_manifest["features"]) == 2449
    assert frontend_manifest_source == backend_manifest_source
    assert "is_fragment" not in EDITORJS_SERVICE.read_text(encoding="utf-8")
    workspace_hook = EDITOR_WORKSPACE_HOOK.read_text(encoding="utf-8")
    assert 'selectedDocument.content_format === "doclibx"' in workspace_hook

    extension_for = _load_extension_function()
    assert extension_for("doclib") == "doclib"
    assert extension_for("doclibx") == "doclibx"
    assert extension_for(" DOCLIBX ") == "doclibx"
    assert extension_for("") == "doclib"

    print(
        "workflow_docs_audit_passed "
        f"agentic_diagrams={len(_mermaid_blocks(agentic))} "
        f"drm_diagrams={len(_mermaid_blocks(drm))} "
        f"compilation_diagrams={len(_mermaid_blocks(compilation))}"
    )


if __name__ == "__main__":
    main()
