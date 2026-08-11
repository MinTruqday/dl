"""Portable Gemma 4 QLoRA pipeline shared by DocLib and the Colab notebook."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterable

DOCLIB_MODEL_NAME = "DocLib Metis"
DEFAULT_BASE_MODEL = "google/gemma-4-E4B-it"
DEFAULT_DATASET = "Glint-Research/Fable-5-traces"
DEFAULT_DATASET_CONFIG = "pi_agent"
DEFAULT_SYSTEM_PROMPT = (
    "Bạn là DocLib Metis, trợ lý AI đa phương thức của DocLib. "
    "Hãy trả lời đúng ngôn ngữ của người dùng, sử dụng công cụ có cấu trúc khi cần, "
    "không tiết lộ suy luận nội bộ và không khẳng định công việc chưa thực hiện là đã hoàn tất."
)


def source_sha256() -> str:
    """Return the hash used to prove notebook/project pipeline parity."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def is_gemma4_model(model_id: str) -> bool:
    normalized = str(model_id or "").lower().replace("_", "-")
    return "gemma-4" in normalized or "gemma4" in normalized


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "\n".join(part for part in parts if part).strip()
    return ""


def _tool_call_text(tool_calls: Any) -> str:
    if not tool_calls:
        return ""
    return "<tool_call>\n" + json.dumps(
        tool_calls,
        ensure_ascii=False,
        sort_keys=True,
    ) + "\n</tool_call>"


def normalize_trace_message(message: dict[str, Any]) -> dict[str, str] | None:
    """Normalize a Fable trace message without importing hidden reasoning content."""
    role = str(message.get("role", "")).lower()
    content = _text(message.get("content"))
    if role == "assistant":
        tool_text = _tool_call_text(message.get("tool_calls"))
        content = "\n".join(part for part in (content, tool_text) if part).strip()
    elif role == "tool":
        tool_name = message.get("name") or message.get("tool_call_id") or "công cụ"
        content = f"[Kết quả {tool_name}]\n{content}".strip()
        role = "user"
    if role not in {"system", "user", "assistant"} or not content:
        return None
    return {"role": role, "content": content}


def fable_row_to_examples(
    row: dict[str, Any],
    *,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    max_history_messages: int = 24,
) -> list[dict[str, list[dict[str, str]]]]:
    """Expand one agent trace into assistant-target prompt/completion examples."""
    history: list[dict[str, str]] = []
    examples = []
    for raw_message in row.get("messages") or []:
        message = normalize_trace_message(raw_message)
        if message is None:
            continue
        if message["role"] == "assistant":
            prompt = history[-max_history_messages:]
            if not prompt or prompt[0]["role"] != "system":
                prompt = [{"role": "system", "content": system_prompt}, *prompt]
            if any(item["role"] == "user" for item in prompt):
                examples.append({"prompt": prompt, "completion": [message]})
        history.append(message)
    return examples


def load_fable_training_dataset(
    *,
    dataset_id: str = DEFAULT_DATASET,
    dataset_config: str = DEFAULT_DATASET_CONFIG,
    split: str = "train",
    max_rows: int | None = None,
    seed: int = 42,
    max_history_messages: int = 24,
):
    """Load and normalize the official Fable trace dataset for text SFT.

    The repository currently contains heterogeneous raw JSONL shards. The Hub
    datasets server exposes the repository's correctly normalized ``pi_agent``
    view, so it is used only when ``load_dataset`` raises while decoding a raw
    shard.
    """
    from datasets import Dataset, load_dataset

    def normalized_examples(rows):
        normalized = []
        for row in rows:
            normalized.extend(
                fable_row_to_examples(
                    row,
                    max_history_messages=max_history_messages,
                )
            )
        return normalized

    try:
        if max_rows:
            source = load_dataset(
                dataset_id,
                dataset_config,
                split=split,
                streaming=True,
            ).take(max_rows)
        else:
            source = load_dataset(dataset_id, dataset_config, split=split)
        examples = normalized_examples(source)
    except Exception as load_error:
        rows = []
        offset = 0
        target = int(max_rows) if max_rows else None
        while target is None or len(rows) < target:
            length = min(100, (target - len(rows)) if target else 100)
            query = urllib.parse.urlencode(
                {
                    "dataset": dataset_id,
                    "config": dataset_config,
                    "split": split,
                    "offset": offset,
                    "length": length,
                }
            )
            request = urllib.request.Request(
                f"https://datasets-server.huggingface.co/rows?{query}"
            )
            hf_token = os.getenv("HF_TOKEN", "").strip()
            if hf_token:
                request.add_header("Authorization", f"Bearer {hf_token}")
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    payload = json.load(response)
            except Exception as fallback_error:
                raise RuntimeError("fable_dataset_loading_failed") from ExceptionGroup(
                    "load_dataset_and_dataset_server_failed",
                    [load_error, fallback_error],
                )
            page = [item.get("row", {}) for item in payload.get("rows", [])]
            rows.extend(page)
            offset += len(page)
            total = int(payload.get("num_rows_total", offset) or offset)
            if not page or offset >= total:
                break
        examples = normalized_examples(rows[:target] if target else rows)
    if not examples:
        raise ValueError("fable_dataset_has_no_trainable_assistant_messages")
    return Dataset.from_list(examples).shuffle(seed=seed)


def doclib_samples_to_dataset(
    samples: Iterable[dict[str, Any]],
    *,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
):
    """Convert DocLib's instruction/input/output records to the same SFT schema."""
    from datasets import Dataset

    rows = []
    for sample in samples:
        instruction = _text(sample.get("instruction"))
        context = _text(sample.get("input"))
        output = _text(sample.get("output"))
        prompt = "\n".join(part for part in (instruction, context) if part).strip()
        if prompt and output:
            rows.append(
                {
                    "prompt": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "completion": [{"role": "assistant", "content": output}],
                }
            )
    if not rows:
        raise ValueError("finetuning_dataset_has_no_valid_samples")
    return Dataset.from_list(rows)


def validate_colab_runtime() -> dict[str, Any]:
    """Fail early instead of pretending that an 8B-weight Gemma model can train on CPU."""
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("gemma4_qlora_requires_cuda_gpu")
    major, _minor = torch.cuda.get_device_capability()
    return {
        "device": torch.cuda.get_device_name(0),
        "bf16": bool(torch.cuda.is_bf16_supported()),
        "compute_capability": major,
        "vram_gib": round(torch.cuda.get_device_properties(0).total_memory / 2**30, 2),
    }


def load_gemma4_qlora(
    model_id: str = DEFAULT_BASE_MODEL,
    *,
    hf_token: str | None = None,
    revision: str | None = None,
):
    """Load Gemma 4 with the official multimodal auto class and NF4 QLoRA."""
    import torch
    from peft import prepare_model_for_kbit_training
    from transformers import AutoModelForMultimodalLM, AutoProcessor, BitsAndBytesConfig

    runtime = validate_colab_runtime()
    compute_dtype = torch.bfloat16 if runtime["bf16"] else torch.float16
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=True,
    )
    common = {"token": hf_token}
    if revision:
        common["revision"] = revision
    processor = AutoProcessor.from_pretrained(model_id, **common)
    model = AutoModelForMultimodalLM.from_pretrained(
        model_id,
        quantization_config=quantization,
        device_map={"": torch.cuda.current_device()},
        dtype=compute_dtype,
        low_cpu_mem_usage=True,
        **common,
    )
    model = prepare_model_for_kbit_training(
        model,
        use_gradient_checkpointing=True,
    )
    model.gradient_checkpointing_enable(
        gradient_checkpointing_kwargs={"use_reentrant": False}
    )
    model.config.use_cache = False
    return model, processor, runtime


def create_lora_config(rank: int = 16, alpha: int = 32, dropout: float = 0.05):
    """Create the language-backbone adapter shared by local and Colab training."""
    from peft import LoraConfig

    return LoraConfig(
        r=int(rank),
        lora_alpha=int(alpha),
        lora_dropout=float(dropout),
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        bias="none",
        task_type="CAUSAL_LM",
    )


def train_gemma4_qlora(
    *,
    dataset,
    output_dir: str | Path,
    model_id: str = DEFAULT_BASE_MODEL,
    hf_token: str | None = None,
    revision: str | None = None,
    epochs: int = 1,
    batch_size: int = 1,
    gradient_accumulation_steps: int = 8,
    learning_rate: float = 2e-4,
    lora_rank: int = 16,
    lora_alpha: int = 32,
    max_length: int = 2048,
    update_callback: Callable[[dict[str, Any]], None] | None = None,
):
    """Train a text/tool-use QLoRA adapter while retaining Gemma 4 multimodality."""
    import torch
    from peft import get_peft_model
    from transformers import TrainerCallback
    from trl import SFTConfig, SFTTrainer

    callback = update_callback or (lambda _data: None)
    callback({"progress": 10, "status": "running"})
    model, processor, runtime = load_gemma4_qlora(
        model_id,
        hf_token=hf_token,
        revision=revision,
    )
    model = get_peft_model(
        model,
        create_lora_config(lora_rank, lora_alpha),
    )
    callback({"progress": 20})

    total_steps = max(
        1,
        math.ceil(len(dataset) / max(1, batch_size * gradient_accumulation_steps))
        * int(epochs),
    )

    class ProgressCallback(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kwargs):
            logs = logs or {}
            progress = 25 + (state.global_step / total_steps) * 65
            callback(
                {
                    "progress": round(min(progress, 90), 1),
                    "current_loss": round(float(logs.get("loss", 0) or 0), 6),
                    "current_epoch": min(
                        int(epochs),
                        max(1, math.ceil(float(logs.get("epoch", 0) or 0))),
                    ),
                }
            )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    bf16 = bool(runtime["bf16"])
    args = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=int(epochs),
        per_device_train_batch_size=int(batch_size),
        gradient_accumulation_steps=int(gradient_accumulation_steps),
        learning_rate=float(learning_rate),
        logging_steps=1,
        save_strategy="epoch",
        save_total_limit=2,
        bf16=bf16,
        fp16=not bf16,
        optim="paged_adamw_8bit",
        max_length=int(max_length),
        packing=False,
        completion_only_loss=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        report_to="none",
        remove_unused_columns=False,
    )
    trainer = SFTTrainer(
        model=model,
        processing_class=processor,
        train_dataset=dataset,
        args=args,
        callbacks=[ProgressCallback()],
    )
    result = trainer.train()
    trainer.model.save_pretrained(output_dir, safe_serialization=True)
    processor.save_pretrained(output_dir)
    final_loss = float(result.metrics.get("train_loss", 0) or 0)
    callback({"progress": 92, "current_loss": round(final_loss, 6)})
    return {
        "trainer": trainer,
        "processor": processor,
        "adapter_path": str(output_dir),
        "final_loss": final_loss,
        "runtime": runtime,
    }


def merge_gemma4_adapter(
    *,
    adapter_path: str | Path,
    merged_path: str | Path,
    model_id: str = DEFAULT_BASE_MODEL,
    hf_token: str | None = None,
    revision: str | None = None,
):
    """Merge the QLoRA adapter into an unquantized multimodal Gemma 4 model."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForMultimodalLM, AutoProcessor

    common = {"token": hf_token}
    if revision:
        common["revision"] = revision
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float16
    base = AutoModelForMultimodalLM.from_pretrained(
        model_id,
        device_map="cpu",
        dtype=dtype,
        low_cpu_mem_usage=True,
        **common,
    )
    merged = PeftModel.from_pretrained(base, str(adapter_path)).merge_and_unload(
        safe_merge=True
    )
    processor = AutoProcessor.from_pretrained(model_id, **common)
    merged_path = Path(merged_path)
    merged_path.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(
        merged_path,
        safe_serialization=True,
        max_shard_size="4GB",
    )
    processor.save_pretrained(merged_path)
    return str(merged_path)


def _find_quantizer(llama_cpp_dir: Path) -> Path | None:
    candidates = [
        llama_cpp_dir / "build/bin/llama-quantize",
        llama_cpp_dir / "llama-quantize",
        Path(shutil.which("llama-quantize") or ""),
    ]
    return next((path for path in candidates if path and path.is_file()), None)


def write_ollama_modelfile(gguf_path: str | Path, output_path: str | Path) -> str:
    """Write a portable Ollama definition for the merged DocLib Metis model."""
    gguf_name = Path(gguf_path).name
    content = (
        f"FROM ./{gguf_name}\n"
        "PARAMETER temperature 1.0\n"
        "PARAMETER top_p 0.95\n"
        "PARAMETER top_k 64\n"
        "PARAMETER num_ctx 4096\n"
        f'SYSTEM """{DEFAULT_SYSTEM_PROMPT}"""\n'
    )
    output_path = Path(output_path)
    output_path.write_text(content, encoding="utf-8")
    return str(output_path)


def export_gguf_artifacts(
    *,
    merged_path: str | Path,
    output_dir: str | Path,
    llama_cpp_dir: str | Path,
    quantization: str = "Q4_K_M",
    timeout_seconds: int = 7200,
) -> dict[str, str]:
    """Convert HF weights to F16 GGUF, then quantize with llama-quantize."""
    merged_path = Path(merged_path)
    output_dir = Path(output_dir)
    llama_cpp_dir = Path(llama_cpp_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    converter = llama_cpp_dir / "convert_hf_to_gguf.py"
    if not converter.is_file():
        raise FileNotFoundError("llama_cpp_converter_not_found")
    f16_path = output_dir / "doclib-metis-F16.gguf"
    subprocess.run(
        [
            os.sys.executable,
            str(converter),
            str(merged_path),
            "--outfile",
            str(f16_path),
            "--outtype",
            "f16",
        ],
        check=True,
        timeout=timeout_seconds,
    )
    result = {"f16_gguf_path": str(f16_path)}
    quantizer = _find_quantizer(llama_cpp_dir)
    if quantizer:
        quantized_path = output_dir / f"doclib-metis-{quantization}.gguf"
        subprocess.run(
            [str(quantizer), str(f16_path), str(quantized_path), quantization],
            check=True,
            timeout=timeout_seconds,
        )
        result["gguf_path"] = str(quantized_path)
    else:
        result["gguf_path"] = str(f16_path)
    result["modelfile_path"] = write_ollama_modelfile(
        result["gguf_path"],
        output_dir / "Modelfile",
    )
    return result


def build_artifact_manifest(
    *,
    adapter_path: str | Path,
    merged_path: str | Path | None = None,
    gguf_path: str | Path | None = None,
) -> dict[str, Any]:
    """Describe portable outputs for Hub, Drive and local DocLib deployment."""
    return {
        "model_name": DOCLIB_MODEL_NAME,
        "base_model": DEFAULT_BASE_MODEL,
        "dataset": DEFAULT_DATASET,
        "adapter_path": str(adapter_path),
        "merged_path": str(merged_path) if merged_path else None,
        "gguf_path": str(gguf_path) if gguf_path else None,
        "pipeline_sha256": source_sha256(),
    }
