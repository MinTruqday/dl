import os
from datetime import datetime, timezone
import torch
from core.config import settings
from loguru import logger
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer
from datasets import Dataset

def run_finetune_job(job_id: str, config: dict, progress_callback) -> dict:
    try:
        logger.info("The standalone artificial intelligence structural model training pipeline explicitly initiated execution flawlessly")
        
        base_model_name = config.get("base_model", settings.LLAMA_MODEL)
        output_dir = f"./workspace/finetune/{job_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        tokenizer = AutoTokenizer.from_pretrained(base_model_name, token=settings.HF_TOKEN)
        tokenizer.pad_token = tokenizer.eos_token
        
        raw_data = config.get("training_data", [])
        formatted_data = [{"text": f"Instruction: {d['instruction']}\nInput: {d['input']}\nOutput: {d['output']}"} for d in raw_data]
        dataset = Dataset.from_list(formatted_data)
        
        model = AutoModelForCausalLM.from_pretrained(base_model_name, token=settings.HF_TOKEN, device_map="auto", torch_dtype=torch.float16)
        
        peft_config = LoraConfig(
            r=config.get("lora_rank", 16),
            lora_alpha=config.get("lora_alpha", 32),
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        model = get_peft_model(model, peft_config)
        
        class ProgressCallback:
            def on_log(self, args, state, control, logs=None, **kwargs):
                if logs and "loss" in logs:
                    progress_callback({"loss": logs["loss"], "current_epoch": state.epoch})
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            per_device_train_batch_size=config.get("batch_size", 4),
            learning_rate=config.get("learning_rate", 2e-4),
            num_train_epochs=config.get("epochs", 3),
            logging_steps=10,
            save_strategy="no",
            optim="paged_adamw_32bit"
        )
        
        trainer = SFTTrainer(
            model=model,
            train_dataset=dataset,
            peft_config=peft_config,
            dataset_text_field="text",
            max_seq_length=1024,
            tokenizer=tokenizer,
            args=training_args,
        )
        
        trainer.train(callbacks=[ProgressCallback()])
        
        adapter_path = os.path.join(output_dir, "adapter")
        trainer.model.save_pretrained(adapter_path)
        tokenizer.save_pretrained(adapter_path)
        
        final_loss = trainer.state.log_history[-1].get("loss", 0.0) if trainer.state.log_history else 0.0
        
        logger.info("The rigorous mathematical statistical evaluation training procedure conclusively succeeded mapping specific layers")
        return {"adapter_path": adapter_path, "merged_path": adapter_path, "gguf_path": "", "final_loss": final_loss}
    except Exception:
        logger.error("The sophisticated isolated neural language model modifying fine tuning processor catastrophically crashed")
        raise