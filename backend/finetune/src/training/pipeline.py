import gc
from pathlib import Path

import torch
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.models import resolve_model_revision
from src.training.gemma4 import (
    doclib_samples_to_dataset,
    export_gguf_artifacts,
    is_gemma4_model,
    merge_gemma4_adapter,
    train_gemma4_qlora,
)


MODELS_DIR = Path(settings.FINETUNE_MODELS_DIR)
ADAPTERS_DIR = Path(settings.FINETUNE_ADAPTERS_DIR)
GGUF_DIR = Path(settings.FINETUNE_GGUF_DIR)
for directory in (MODELS_DIR, ADAPTERS_DIR, GGUF_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def run_training_job(job_id: str, config: dict, update_callback):
    model_id = str(config.get("base_model") or settings.FINETUNE_BASE_MODEL)
    if not is_gemma4_model(model_id):
        raise ValueError("unsupported_training_model")

    token = config.get("hf_token") or settings.HF_TOKEN
    revision = resolve_model_revision(model_id, token)
    adapter_path = ADAPTERS_DIR / job_id
    merged_path = MODELS_DIR / f"merged-{job_id}"
    dataset = doclib_samples_to_dataset(config.get("training_data", []))
    result = train_gemma4_qlora(
        dataset=dataset,
        output_dir=adapter_path,
        model_id=model_id,
        hf_token=token,
        revision=revision,
        epochs=int(config.get("epochs", 3)),
        batch_size=min(int(config.get("batch_size", 1)), 2),
        gradient_accumulation_steps=max(
            1, 8 // min(int(config.get("batch_size", 1)), 2)
        ),
        learning_rate=float(config.get("learning_rate", 2e-4)),
        lora_rank=int(config.get("lora_rank", 16)),
        lora_alpha=int(config.get("lora_alpha", 32)),
        update_callback=update_callback,
    )
    final_loss = float(result["final_loss"])
    result.pop("trainer", None)
    result.pop("processor", None)
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    merge_gemma4_adapter(
        adapter_path=adapter_path,
        merged_path=merged_path,
        model_id=model_id,
        hf_token=token,
        revision=revision,
    )
    output = {
        "adapter_path": str(adapter_path),
        "merged_path": str(merged_path),
        "final_loss": final_loss,
    }
    llama_cpp = Path("/app/llama.cpp")
    if llama_cpp.exists():
        output.update(
            export_gguf_artifacts(
                merged_path=merged_path,
                output_dir=GGUF_DIR / job_id,
                llama_cpp_dir=llama_cpp,
            )
        )
    else:
        logger.warning("GGUF exporter is unavailable")
    return output
