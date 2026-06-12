import sys
import json
import asyncio
from pathlib import Path
from loguru import logger
from datasets import Dataset

MODELS_DIR = Path("/tmp/doclib_finetune/models")
ADAPTERS_DIR = Path("/tmp/doclib_finetune/adapters")
GGUF_DIR = Path("/tmp/doclib_finetune/gguf")
MODELS_DIR.mkdir(parents=True, exist_ok=True)
ADAPTERS_DIR.mkdir(parents=True, exist_ok=True)
GGUF_DIR.mkdir(parents=True, exist_ok=True)


def format_samples_to_chat(samples: list, tokenizer=None, for_mlx=False) -> list:
    formatted = []
    for s in samples:
        instruction = s.get("instruction", "")
        inp = s.get("input", "")
        output = s.get("output", "")
        user_content = f"{instruction}\n{inp}".strip() if inp else instruction
        if for_mlx:
            formatted.append({"messages": [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": output}
            ]})
        else:
            messages = [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": output},
            ]
            try:
                text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            except Exception:
                text = f"<|user|>\n{user_content}\n<|assistant|>\n{output}"
            formatted.append({"text": text})
    return formatted


def run_mlx_training(job_id: str, config: dict, update_callback):
    import mlx.core as mx
    from mlx_lm import load, generate
    from mlx_lm.tuner import train, make_lora_layers, TrainingArgs
    from mlx_lm.tuner.datasets import Dataset as MlxDataset

    base_model_name = config.get("base_model")
    epochs = config.get("epochs", 3)
    batch_size = config.get("batch_size", 4)
    learning_rate = config.get("learning_rate", 2e-4)
    lora_rank = config.get("lora_rank", 16)
    samples = config.get("training_data", [])

    logger.info(f"Đang tải mô hình nền tảng trên Apple Silicon {base_model_name}")
    update_callback({"progress": 10, "status": "running"})

    model, tokenizer = load(base_model_name)
    model.freeze()
    make_lora_layers(model, lora_rank)
    
    update_callback({"progress": 20})

    formatted_data = format_samples_to_chat(samples, for_mlx=True)
    jsonl_path = str(ADAPTERS_DIR / f"{job_id}_train.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for item in formatted_data:
            f.write(json.dumps(item) + "\n")

    class SimpleMlxDataset(MlxDataset):
        def __init__(self, data):
            self._data = data
        def __getitem__(self, idx):
            return self._data[idx]
        def __len__(self):
            return len(self._data)

    train_data = []
    for item in formatted_data:
        text = tokenizer.apply_chat_template(item["messages"], tokenize=False, add_generation_prompt=False)
        train_data.append(text)

    dataset = SimpleMlxDataset(train_data)
    total_iters = (len(dataset) // batch_size) * epochs

    training_args = TrainingArgs(
        batch_size=batch_size,
        iters=total_iters,
        learning_rate=learning_rate,
        steps_per_report=1,
        steps_per_eval=0,
        adapter_file=str(ADAPTERS_DIR / f"{job_id}_adapters.safetensors")
    )

    class Reporter:
        def __init__(self, cb, total):
            self.cb = cb
            self.total = total
            self.step = 0
            self.last_epoch = 0

        def __call__(self, loss, iters):
            self.step += 1
            epoch = (self.step * batch_size) // max(1, len(dataset))
            progress = 25 + (self.step / max(1, self.total)) * 65
            current_epoch = epoch + 1
            
            update_data = {"progress": round(min(progress, 90), 1), "current_loss": round(float(loss), 6), "current_epoch": current_epoch}
            if current_epoch != self.last_epoch:
                update_data["loss"] = round(float(loss), 6)
                self.last_epoch = current_epoch
            self.cb(update_data)

    logger.info(f"Bắt đầu huấn luyện LoRA mức {lora_rank})")
    update_callback({"progress": 25})
    
    train(
        model=model,
        tokenizer=tokenizer,
        optimizer=mx.optimizers.AdamW(learning_rate=learning_rate),
        train_dataset=dataset,
        val_dataset=None,
        args=training_args,
        loss_fn=None,
        iteration_callback=Reporter(update_callback, total_iters)
    )

    merged_path = str(MODELS_DIR / f"merged-{job_id}")
    from mlx_lm.fuse import fuse
    fuse(model=base_model_name, adapter_file=training_args.adapter_file, save_path=merged_path)

    update_callback({"progress": 96})
    return {"adapter_path": training_args.adapter_file, "final_loss": 0, "merged_path": merged_path}


def run_hf_training(job_id: str, config: dict, update_callback):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, PeftModel
    from trl import SFTTrainer, SFTConfig

    base_model_name = config.get("base_model")
    hf_token = config.get("hf_token")
    epochs = config.get("epochs", 3)
    batch_size = config.get("batch_size", 4)
    learning_rate = config.get("learning_rate", 2e-4)
    lora_rank = config.get("lora_rank", 16)
    samples = config.get("training_data", [])

    logger.info(f"Đang tải mô hình nền tảng trên vi xử lý đồ họa {base_model_name}")
    update_callback({"progress": 10, "status": "running"})

    bnb_config = None
    if torch.cuda.is_available():
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        token=hf_token,
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, token=hf_token, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    update_callback({"progress": 20})

    lora_config = LoraConfig(
        r=lora_rank, lora_alpha=lora_rank*2, lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none", task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)

    formatted = format_samples_to_chat(samples, tokenizer=tokenizer)
    dataset = Dataset.from_list(formatted)

    update_callback({"progress": 25})

    total_steps = max(1, (len(dataset) // batch_size) * epochs)
    last_reported_epoch = [0]

    def on_step(info):
        step = info.get("step", 0)
        loss = info.get("loss", 0)
        epoch = info.get("epoch", 0)
        progress = 25 + (step / total_steps) * 65
        current_epoch = int(epoch) + 1
        update_data = {"progress": round(min(progress, 90), 1), "current_loss": round(loss, 6), "current_epoch": current_epoch}
        if current_epoch != last_reported_epoch[0]:
            update_data["loss"] = round(loss, 6)
            last_reported_epoch[0] = current_epoch
        update_callback(update_data)

    adapter_path = str(ADAPTERS_DIR / job_id)
    
    training_args = SFTConfig(
        output_dir=adapter_path, num_train_epochs=epochs, per_device_train_batch_size=batch_size,
        learning_rate=learning_rate, logging_steps=1, bf16=torch.cuda.is_available(),
        optim="adamw_8bit" if torch.cuda.is_available() else "adamw_torch", max_seq_length=2048, dataset_text_field="text",
    )

    from transformers import TrainerCallback as _TCB
    class _ProgressCB(_TCB):
        def on_log(self, args, state, control, logs=None, **kwargs):
            if logs:
                on_step({"step": state.global_step, "loss": logs.get("loss", 0), "epoch": logs.get("epoch", 0)})

    trainer = SFTTrainer(model=model, tokenizer=tokenizer, train_dataset=dataset, args=training_args, callbacks=[_ProgressCB()])
    train_result = trainer.train()
    trainer.save_model(adapter_path)
    tokenizer.save_pretrained(adapter_path)

    final_loss = train_result.metrics.get("train_loss", 0)
    update_callback({"progress": 92, "current_loss": round(final_loss, 6)})

    logger.info("Đang gộp bộ chuyển đổi vào mô hình nền tảng")
    base_model = AutoModelForCausalLM.from_pretrained(base_model_name, device_map="cpu", torch_dtype=torch.float16, token=hf_token)
    merged_model = PeftModel.from_pretrained(base_model, adapter_path).merge_and_unload()
    merged_path = str(MODELS_DIR / f"merged-{job_id}")
    merged_model.save_pretrained(merged_path)
    tokenizer.save_pretrained(merged_path)

    update_callback({"progress": 96})
    return {"adapter_path": adapter_path, "final_loss": final_loss, "merged_path": merged_path}


def run_finetune_job(job_id: str, config: dict, update_callback):
    base_model_name = config.get("base_model", "").lower()
    
    if "flux" in base_model_name or "diffusion" in base_model_name:
        logger.info("Detected Diffusion model. Dispatching lên Diffusion Engine")
        result = run_diffusion_training(job_id, config, update_callback)
    elif "nllb" in base_model_name or "t5" in base_model_name or "bart" in base_model_name:
        logger.info("Detected Seq2Seq model. Dispatching lên Seq2Seq Engine")
        result = run_seq2seq_training(job_id, config, update_callback)
    else:
        if sys.platform == "darwin":
            logger.info("Detected macOS environment. Dispatching lên MLX Engine")
            result = run_mlx_training(job_id, config, update_callback)
        else:
            logger.info("Detected Linux/Windows environment. Dispatching lên PyTorch Engine")
            result = run_hf_training(job_id, config, update_callback)

    merged_path = result.get("merged_path")
    gguf_path = str(GGUF_DIR / f"doclib-ft-{job_id[:8]}.gguf")
    try:
        import shutil
        import subprocess
        convert_script = shutil.which("python3") or "python"
        llama_cpp_convert = Path("/app/llama.cpp/convert_hf_to_gguf.py")
        if not llama_cpp_convert.exists():
            llama_cpp_convert = Path("convert_hf_to_gguf.py")

        if llama_cpp_convert.exists():
            subprocess.run(
                [convert_script, str(llama_cpp_convert), merged_path, "--outfile", gguf_path, "--outtype", "q4_k_m"],
                check=True, timeout=1800
            )
            logger.info(f"GGUF export Thành côngful: {gguf_path}")
            result["gguf_path"] = gguf_path
        else:
            logger.warning("Không tìm thấy công cụ chuyển đổi định dạng, hệ thống chỉ lưu mô hình gốc")
    except Exception as e:
        logger.error("GGUF conversion thất bại")

    return result

def run_seq2seq_training(job_id: str, config: dict, update_callback):
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, Seq2SeqTrainer, Seq2SeqTrainingArguments
    from peft import LoraConfig, get_peft_model, PeftModel
    from datasets import Dataset

    base_model_name = config.get("base_model")
    hf_token = config.get("hf_token")
    epochs = config.get("epochs", 3)
    batch_size = config.get("batch_size", 4)
    learning_rate = config.get("learning_rate", 2e-4)
    lora_rank = config.get("lora_rank", 16)
    samples = config.get("training_data", [])

    logger.info(f"Đang tải mô hình nền tảng trên vi xử lý đồ họa {base_model_name}")
    update_callback({"progress": 10, "status": "running"})

    model = AutoModelForSeq2SeqLM.from_pretrained(
        base_model_name,
        device_map="auto",
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        token=hf_token,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, token=hf_token)
    
    update_callback({"progress": 20})

    lora_config = LoraConfig(
        r=lora_rank, lora_alpha=lora_rank*2, lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"],
        bias="none", task_type="SEQ_2_SEQ_LM",
    )
    model = get_peft_model(model, lora_config)

    formatted = []
    for s in samples:
        formatted.append({"source": s.get("input", ""), "target": s.get("output", "")})
    dataset = Dataset.from_list(formatted)

    def preprocess_function(examples):
        inputs = [ex for ex in examples["source"]]
        targets = [ex for ex in examples["target"]]
        model_inputs = tokenizer(inputs, max_length=1024, padding="max_length", truncation=True)
        labels = tokenizer(targets, max_length=1024, padding="max_length", truncation=True)
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    tokenized_dataset = dataset.map(preprocess_function, batched=True)

    update_callback({"progress": 25})

    total_steps = max(1, (len(dataset) // batch_size) * epochs)
    last_reported_epoch = [0]

    def on_step(info):
        step = info.get("step", 0)
        loss = info.get("loss", 0)
        epoch = info.get("epoch", 0)
        progress = 25 + (step / total_steps) * 65
        current_epoch = int(epoch) + 1
        update_data = {"progress": round(min(progress, 90), 1), "current_loss": round(loss, 6), "current_epoch": current_epoch}
        if current_epoch != last_reported_epoch[0]:
            update_data["loss"] = round(loss, 6)
            last_reported_epoch[0] = current_epoch
        update_callback(update_data)

    adapter_path = str(ADAPTERS_DIR / job_id)
    
    training_args = Seq2SeqTrainingArguments(
        output_dir=adapter_path, num_train_epochs=epochs, per_device_train_batch_size=batch_size,
        learning_rate=learning_rate, logging_steps=1, bf16=torch.cuda.is_available(),
        optim="adamw_8bit" if torch.cuda.is_available() else "adamw_torch",
        predict_with_generate=True,
    )

    from transformers import TrainerCallback as _TCB
    class _ProgressCB(_TCB):
        def on_log(self, args, state, control, logs=None, **kwargs):
            if logs:
                on_step({"step": state.global_step, "loss": logs.get("loss", 0), "epoch": logs.get("epoch", 0)})

    trainer = Seq2SeqTrainer(model=model, tokenizer=tokenizer, train_dataset=tokenized_dataset, args=training_args, callbacks=[_ProgressCB()])
    train_result = trainer.train()
    trainer.save_model(adapter_path)
    tokenizer.save_pretrained(adapter_path)

    final_loss = train_result.metrics.get("train_loss", 0)
    update_callback({"progress": 92, "current_loss": round(final_loss, 6)})

    logger.info("Đang gộp bộ chuyển đổi vào mô hình nền tảng")
    base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_name, device_map="cpu", torch_dtype=torch.float32, token=hf_token)
    merged_model = PeftModel.from_pretrained(base_model, adapter_path).merge_and_unload()
    merged_path = str(MODELS_DIR / f"merged-{job_id}")
    merged_model.save_pretrained(merged_path)
    tokenizer.save_pretrained(merged_path)

    update_callback({"progress": 96})
    return {"adapter_path": adapter_path, "final_loss": final_loss, "merged_path": merged_path}


def run_diffusion_training(job_id: str, config: dict, update_callback):
    import torch
    import torch.nn.functional as F
    from diffusers import FluxPipeline
    from peft import LoraConfig, get_peft_model
    from PIL import Image
    import numpy as np
    import io
    import base64

    base_model_name = config.get("base_model")
    hf_token = config.get("hf_token")
    epochs = config.get("epochs", 3)
    batch_size = config.get("batch_size", 1)
    learning_rate = config.get("learning_rate", 1e-4)
    lora_rank = config.get("lora_rank", 16)
    samples = config.get("training_data", [])

    logger.info(f"Đang tải mô hình nền tảng trên vi xử lý đồ họa {base_model_name}")
    update_callback({"progress": 10, "status": "running"})

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

    pipeline = FluxPipeline.from_pretrained(base_model_name, torch_dtype=dtype, token=hf_token)
    pipeline.to(device)
    transformer = pipeline.transformer

    update_callback({"progress": 20})

    lora_config = LoraConfig(
        r=lora_rank, lora_alpha=lora_rank*2, lora_dropout=0.05,
        target_modules=["lên_q", "lên_k", "lên_v", "lên_out.0"],
        bias="none",
    )
    transformer = get_peft_model(transformer, lora_config)
    transformer.train()

    optimizer = torch.optim.AdamW(transformer.parameters(), lr=learning_rate)

    update_callback({"progress": 25})

    total_steps = max(1, len(samples) * epochs)
    current_step = 0
    final_loss = 0.0

    for epoch in range(epochs):
        for s in samples:
            prompt = s.get("instruction", "")
            image_b64 = s.get("output", "")
            if image_b64.startswith("data:image"):
                image_b64 = image_b64.split(",")[1]
            try:
                image_data = base64.b64decode(image_b64)
                img = Image.open(io.BytesIO(image_data)).convert("RGB").resize((512, 512))
            except Exception as e:
                logger.error("Tải hình ảnh cho quá trình huấn luyện diffusion thất bại")
                continue

            optimizer.zero_grad()

            try:
                img_tensor = torch.tensor(np.array(img)).permute(2,0,1).unsqueeze(0).float().to(device)
                img_tensor = (img_tensor / 127.5) - 1.0
                with torch.no_grad():
                    latents = pipeline.vae.encode(img_tensor).latent_dist.sample() * pipeline.vae.config.scaling_factor
                    
                text_input_ids = pipeline.tokenizer(prompt, return_tensors="pt", max_length=77, truncation=True, padding="max_length").input_ids.to(device)
                with torch.no_grad():
                    prompt_embeds = pipeline.text_encoder(text_input_ids)[0]

                noise = torch.randn_like(latents)
                timesteps = torch.randint(0, pipeline.scheduler.config.num_train_timesteps, (1,), device=device)
                noisy_latents = pipeline.scheduler.add_noise(latents, noise, timesteps)

                model_pred = transformer(noisy_latents, timesteps, prompt_embeds).sample
                loss = F.mse_loss(model_pred, noise)

                loss.backward()
                optimizer.step()
                final_loss = float(loss)
            except Exception as e:
                logger.error("Bước huấn luyện diffusion thất bại")
                final_loss = 0.0

            current_step += 1
            progress = 25 + (current_step / total_steps) * 65
            update_callback({"progress": round(min(progress, 90), 1), "current_loss": round(final_loss, 6), "current_epoch": epoch + 1})

    adapter_path = str(ADAPTERS_DIR / job_id)
    transformer.save_pretrained(adapter_path)
    
    update_callback({"progress": 92, "current_loss": final_loss})

    merged_path = str(MODELS_DIR / f"merged-{job_id}")
    pipeline.save_pretrained(merged_path)

    update_callback({"progress": 96})
    return {"adapter_path": adapter_path, "final_loss": final_loss, "merged_path": merged_path}
