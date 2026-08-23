"""Build and verify the self-contained DocLib Metis Colab notebook."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend/agentic_ai/src/training/gemma4_finetuning.py"
NOTEBOOK_PATH = ROOT / "backend/agentic_ai/notebooks/DocLib_finetune.ipynb"
SYNC_CELL_ID = "doclib-shared-pipeline"


def markdown(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def code(source: str, *, metadata: dict | None = None) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": metadata or {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def build_notebook() -> dict:
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    module_hash = hashlib.sha256(module_source.encode()).hexdigest()
    embedded_module = (
        "from pathlib import Path\n"
        f"MODULE_SOURCE = {module_source!r}\n"
        "PORTABLE_MODULE = Path('/content/gemma4_finetuning.py')\n"
        "PORTABLE_MODULE.write_text(MODULE_SOURCE, encoding='utf-8')\n"
        "print(f'Đã đồng bộ pipeline dùng chung: {PORTABLE_MODULE}')\n"
    )
    cells = [
        markdown(
            """# DocLib Metis — Gemma 4 E4B QLoRA trên Google Colab

Notebook này dùng **chính xác cùng pipeline** với `src/training/gemma4_finetuning.py` trong dự án DocLib. Mỗi lần module dự án thay đổi, chạy `python3 scripts/build_finetune_notebook.py` để tạo lại notebook; lệnh `--check` xác minh hai bản không lệch nhau.

Pipeline thực hiện: tải `Glint-Research/Fable-5-traces` (`pi_agent`), loại bỏ `reasoning_content`, tạo mẫu prompt/completion, QLoRA NF4 cho `google/gemma-4-E4B-it`, lưu adapter, merge tùy chọn, đẩy lên Hugging Face private repo/Google Drive, chuyển F16 GGUF rồi quantize Q4_K_M và tạo `Modelfile` cho Ollama.

> Yêu cầu: bật GPU trong **Runtime → Change runtime type → GPU**. T4/L4 phù hợp cho QLoRA với batch 1; bước merge cần High-RAM hoặc A100/L4 đủ bộ nhớ. Bạn phải chấp nhận điều khoản Gemma trên Hugging Face. Dataset Fable-5-traces dùng giấy phép AGPL-3.0; hãy giữ thông tin nguồn và kiểm tra nghĩa vụ giấy phép trước khi phân phối model.
"""
        ),
        markdown("## 1. Cài môi trường Colab"),
        code(
            """# Gemma 4 yêu cầu Transformers 5.5+; -U là bắt buộc trên Colab.
%pip install -q -U "transformers>=5.5,<6" "trl>=0.29" "peft>=0.18" datasets teich accelerate bitsandbytes safetensors huggingface_hub sentencepiece protobuf

# Sau lần cài đầu, nếu Colab báo phải restart runtime: Runtime → Restart session,
# rồi chạy lại notebook từ đầu.
"""
        ),
        markdown("## 2. Token Hugging Face, Drive và cấu hình"),
        code(
            """import gc
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import torch
import transformers
from huggingface_hub import HfApi, login

try:
    from google.colab import userdata
    HF_TOKEN = userdata.get("HF_TOKEN") or os.getenv("HF_TOKEN")
except Exception:
    HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError(
        "Hãy thêm secret HF_TOKEN trong biểu tượng chìa khóa của Colab. "
        "Token cần quyền đọc model Gemma đã chấp nhận điều khoản."
    )
login(token=HF_TOKEN, add_to_git_credential=False)

MODEL_ID = "google/gemma-4-E4B-it"
DATASET_ID = "Glint-Research/Fable-5-traces"
DATASET_CONFIG = "pi_agent"
OUTPUT_ROOT = Path("/content/doclib-metis")
ADAPTER_DIR = OUTPUT_ROOT / "adapter"
MERGED_DIR = OUTPUT_ROOT / "merged"
GGUF_DIR = OUTPUT_ROOT / "gguf"

# 500 source traces là cấu hình khởi đầu an toàn. Đặt None để dùng toàn bộ dataset.
MAX_SOURCE_ROWS = 500
EPOCHS = 1
BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 8
LEARNING_RATE = 2e-4
LORA_RANK = 16
LORA_ALPHA = 32
MAX_LENGTH = 2048
SEED = 42

# Merge/GGUF cần nhiều RAM và dung lượng hơn. Adapter vẫn luôn được lưu dù hai cờ này tắt.
MERGE_MODEL = False
EXPORT_GGUF = False
SAVE_TO_DRIVE = False
PUSH_ADAPTER_TO_HUB = False
PUSH_MERGED_TO_HUB = False
HF_ADAPTER_REPO = "TEN_HF_CUA_BAN/doclib-metis-gemma4-e4b-lora"
HF_MERGED_REPO = "TEN_HF_CUA_BAN/doclib-metis-gemma4-e4b-merged"

OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
print("Transformers:", transformers.__version__)
print("PyTorch:", torch.__version__)
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "KHÔNG CÓ")
"""
        ),
        markdown("## 3. Pipeline dùng chung 100% với dự án"),
        code(
            embedded_module,
            metadata={
                "doclib_cell_id": SYNC_CELL_ID,
                "doclib_source_path": str(MODULE_PATH.relative_to(ROOT)),
                "doclib_source_sha256": module_hash,
            },
        ),
        code(
            """sys.path.insert(0, "/content")
from gemma4_finetuning import (
    DOCLIB_MODEL_NAME,
    DEFAULT_BASE_MODEL,
    DEFAULT_DATASET,
    build_artifact_manifest,
    export_gguf_artifacts,
    load_fable_training_dataset,
    merge_gemma4_adapter,
    source_sha256,
    train_gemma4_qlora,
    validate_colab_runtime,
)

assert MODEL_ID == DEFAULT_BASE_MODEL
assert DATASET_ID == DEFAULT_DATASET
runtime = validate_colab_runtime()
print(DOCLIB_MODEL_NAME, runtime)
print("SHA-256 pipeline:", source_sha256())
"""
        ),
        markdown("## 4. Tải và chuẩn hóa Fable-5-traces"),
        code(
            """dataset = load_fable_training_dataset(
    dataset_id=DATASET_ID,
    dataset_config=DATASET_CONFIG,
    max_rows=MAX_SOURCE_ROWS,
    seed=SEED,
    max_history_messages=24,
)
split = dataset.train_test_split(test_size=min(0.02, max(1 / len(dataset), 0.005)), seed=SEED)
train_dataset = split["train"]
eval_dataset = split["test"]

print(f"Mẫu train: {len(train_dataset):,}; mẫu kiểm tra: {len(eval_dataset):,}")
print(json.dumps(train_dataset[0], ensure_ascii=False, indent=2)[:4000])
assert "reasoning_content" not in json.dumps(train_dataset[0], ensure_ascii=False)
"""
        ),
        markdown("## 5. QLoRA DocLib Metis"),
        code(
            """def show_progress(data):
    print(
        f"Tiến độ {data.get('progress', 0):>5}% | "
        f"epoch={data.get('current_epoch', '-')} | "
        f"loss={data.get('current_loss', '-')}"
    )

training = train_gemma4_qlora(
    dataset=train_dataset,
    output_dir=ADAPTER_DIR,
    model_id=MODEL_ID,
    hf_token=HF_TOKEN,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
    learning_rate=LEARNING_RATE,
    lora_rank=LORA_RANK,
    lora_alpha=LORA_ALPHA,
    max_length=MAX_LENGTH,
    update_callback=show_progress,
)
trainer = training["trainer"]
processor = training["processor"]
print("Adapter:", training["adapter_path"])
print("Train loss:", training["final_loss"])
"""
        ),
        markdown("## 6. Kiểm tra adapter ngay trên Colab"),
        code(
            """messages = [
    {"role": "system", "content": "Bạn là DocLib Metis."},
    {"role": "user", "content": "Giới thiệu ngắn gọn bạn là ai."},
]
inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
    add_generation_prompt=True,
    enable_thinking=False,
).to(trainer.model.device)
input_length = inputs["input_ids"].shape[-1]
with torch.inference_mode():
    generated = trainer.model.generate(**inputs, max_new_tokens=96)
response = processor.decode(generated[0][input_length:], skip_special_tokens=False)
print(processor.parse_response(response, prefix=inputs["input_ids"]))
"""
        ),
        markdown("## 7. Đẩy adapter lên Hugging Face private repo"),
        code(
            """api = HfApi(token=HF_TOKEN)
if PUSH_ADAPTER_TO_HUB:
    if HF_ADAPTER_REPO.startswith("TEN_HF_CUA_BAN/"):
        raise ValueError("Hãy thay TEN_HF_CUA_BAN trong HF_ADAPTER_REPO")
    api.create_repo(HF_ADAPTER_REPO, private=True, exist_ok=True)
    api.upload_folder(
        repo_id=HF_ADAPTER_REPO,
        folder_path=str(ADAPTER_DIR),
        commit_message="DocLib Metis Gemma 4 E4B QLoRA adapter",
    )
    print("Đã đẩy adapter private:", HF_ADAPTER_REPO)
else:
    print("Adapter đã lưu tại", ADAPTER_DIR, "— bật PUSH_ADAPTER_TO_HUB khi sẵn sàng.")
"""
        ),
        markdown("## 8. Merge adapter vào Gemma 4 (khuyên dùng trước khi xuất GGUF)"),
        code(
            """merged_path = None
if MERGE_MODEL or EXPORT_GGUF or PUSH_MERGED_TO_HUB:
    # Giải phóng QLoRA khỏi VRAM trước khi tải base model không quantize.
    del trainer
    del training
    gc.collect()
    torch.cuda.empty_cache()
    merged_path = merge_gemma4_adapter(
        adapter_path=ADAPTER_DIR,
        merged_path=MERGED_DIR,
        model_id=MODEL_ID,
        hf_token=HF_TOKEN,
    )
    print("Merged model:", merged_path)
else:
    print("Đang giữ adapter riêng. Bật MERGE_MODEL nếu Colab có High-RAM.")
"""
        ),
        markdown("## 9. Đẩy merged model lên Hugging Face private repo"),
        code(
            """if PUSH_MERGED_TO_HUB:
    if not merged_path:
        raise RuntimeError("Bật MERGE_MODEL trước khi push merged model")
    if HF_MERGED_REPO.startswith("TEN_HF_CUA_BAN/"):
        raise ValueError("Hãy thay TEN_HF_CUA_BAN trong HF_MERGED_REPO")
    api.create_repo(HF_MERGED_REPO, private=True, exist_ok=True)
    api.upload_folder(
        repo_id=HF_MERGED_REPO,
        folder_path=str(MERGED_DIR),
        commit_message="DocLib Metis merged Gemma 4 E4B",
    )
    print("Đã đẩy merged model private:", HF_MERGED_REPO)
"""
        ),
        markdown("## 10. Xuất GGUF F16 → Q4_K_M và Modelfile Ollama"),
        code(
            """gguf_artifacts = {}
if EXPORT_GGUF:
    if not merged_path:
        raise RuntimeError("GGUF yêu cầu merged model; bật MERGE_MODEL hoặc EXPORT_GGUF từ đầu")
    llama_cpp = Path("/content/llama.cpp")
    if not llama_cpp.exists():
        subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/ggml-org/llama.cpp.git", str(llama_cpp)],
            check=True,
        )
    subprocess.run(
        [
            "cmake", "-S", str(llama_cpp), "-B", str(llama_cpp / "build"),
            "-DGGML_NATIVE=OFF", "-DLLAMA_CURL=OFF",
        ],
        check=True,
    )
    subprocess.run(
        ["cmake", "--build", str(llama_cpp / "build"), "--target", "llama-quantize", "-j2"],
        check=True,
    )
    gguf_artifacts = export_gguf_artifacts(
        merged_path=MERGED_DIR,
        output_dir=GGUF_DIR,
        llama_cpp_dir=llama_cpp,
        quantization="Q4_K_M",
    )
    print(json.dumps(gguf_artifacts, ensure_ascii=False, indent=2))
else:
    print("Bật EXPORT_GGUF để tạo F16, Q4_K_M và Modelfile.")
"""
        ),
        markdown("## 11. Lưu Google Drive và manifest"),
        code(
            """manifest = build_artifact_manifest(
    adapter_path=ADAPTER_DIR,
    merged_path=merged_path,
    gguf_path=gguf_artifacts.get("gguf_path"),
)
(OUTPUT_ROOT / "artifact-manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
)

if SAVE_TO_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")
    drive_target = Path("/content/drive/MyDrive/DocLib-Metis")
    if drive_target.exists():
        shutil.rmtree(drive_target)
    shutil.copytree(OUTPUT_ROOT, drive_target)
    print("Đã lưu vào", drive_target)

print(json.dumps(manifest, ensure_ascii=False, indent=2))
"""
        ),
        markdown(
            """## 12. Áp vào DocLib local

Sau khi tải thư mục `gguf/` về máy, chạy tại thư mục đó:

```bash
ollama create doclib-metis -f Modelfile
ollama run doclib-metis "Xin chào, bạn là ai?"
```

Sau khi test thành công, đổi `.env` của dự án:

```dotenv
LLM_MODEL=doclib-metis:latest
```

rồi tái tạo riêng các dịch vụ gọi model:

```bash
docker compose up -d --force-recreate agentic_ai rag
```

Nếu chỉ tải adapter, giữ đúng base model `google/gemma-4-E4B-it` khi merge. Không gắn adapter vào một bản Gemma khác hoặc một quantization khác. Với llama.cpp multimodal, projector cần được xuất/test riêng; GGUF chính trong notebook là đường triển khai text/tool-use an toàn nhất cho dataset Fable vốn chỉ có text traces. Hãy giữ model Ollama cũ cho audio/image cho đến khi bản GGUF mới vượt qua kiểm thử đa phương thức.
"""
        ),
    ]
    return {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"gpuType": "T4", "provenance": []},
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
            "doclib_pipeline_sha256": module_hash,
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def embedded_source(notebook: dict) -> str:
    for cell in notebook.get("cells", []):
        if cell.get("metadata", {}).get("doclib_cell_id") == SYNC_CELL_ID:
            source = "".join(cell.get("source", []))
            assignment = source.splitlines()[1]
            return ast.literal_eval(assignment.split("=", 1)[1].strip())
    raise ValueError("doclib_shared_pipeline_cell_missing")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = MODULE_PATH.read_text(encoding="utf-8")
    if args.check:
        notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
        if embedded_source(notebook) != expected:
            raise SystemExit("finetune_notebook_pipeline_out_of_sync")
        print("finetune_notebook_pipeline_sync_passed")
        return 0
    NOTEBOOK_PATH.write_text(
        json.dumps(build_notebook(), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"Đã tạo {NOTEBOOK_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
