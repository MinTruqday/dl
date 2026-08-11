#!/usr/bin/env python3
"""Static and behavioral audit for the shared project/Colab fine-tune pipeline."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / "backend/agentic_ai/src/training/gemma4_finetuning.py"
PROJECT_PIPELINE = ROOT / "backend/agentic_ai/src/training/finetuning.py"
NOTEBOOK = ROOT / "backend/agentic_ai/notebooks/DocLib_finetune.ipynb"
REQUIREMENTS = ROOT / "backend/agentic_ai/requirements.txt"


def load_module():
    spec = importlib.util.spec_from_file_location("doclib_gemma4_finetuning", MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module()
    row = {
        "messages": [
            {"role": "user", "content": "Kiểm tra tài liệu"},
            {
                "role": "assistant",
                "content": "",
                "reasoning_content": "Suy luận riêng không được dùng để huấn luyện",
                "tool_calls": [
                    {"function": {"name": "read_document", "arguments": {"id": "1"}}}
                ],
            },
            {"role": "tool", "name": "read_document", "content": "Nội dung"},
            {"role": "assistant", "content": "Đã đọc tài liệu."},
        ]
    }
    examples = module.fable_row_to_examples(row)
    serialized = json.dumps(examples, ensure_ascii=False)
    assert len(examples) == 2
    assert "reasoning_content" not in serialized
    assert "Suy luận riêng" not in serialized
    assert "read_document" in serialized

    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_finetune_notebook.py"), "--check"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        source = "\n".join(
            line for line in source.splitlines() if not line.lstrip().startswith("%")
        )
        compile(source, f"DocLib_finetune.ipynb:cell-{index}", "exec")

    project_source = PROJECT_PIPELINE.read_text(encoding="utf-8")
    assert "train_gemma4_qlora" in project_source
    assert "merge_gemma4_adapter" in project_source
    assert '"--outtype",\n            "q4_k_m"' not in project_source
    requirements = REQUIREMENTS.read_text(encoding="utf-8")
    assert "transformers>=5.5.0,<6.0.0" in requirements
    print(
        "finetuning_audit_passed "
        f"examples={len(examples)} notebook_cells={len(notebook['cells'])} "
        f"pipeline_sha256={module.source_sha256()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
