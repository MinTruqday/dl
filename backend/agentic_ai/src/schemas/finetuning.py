from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

class FinetuneRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

class DatasetCreate(FinetuneRequest):
    name: str = Field(min_length=1, max_length=200, description="<input_context>Unique display name for the owned training dataset.</input_context>")
    description: str = Field(default="", max_length=2000, description="<input_context>Purpose and provenance of the dataset.</input_context>")
    source: Literal["manual", "feedback", "documents"] = Field(default="manual", description="<critical_instructions>Trusted source category for dataset samples.</critical_instructions>")

class FinetuneSample(FinetuneRequest):
    instruction: str = Field(min_length=1, max_length=100000, description="<input_context>Instruction presented to the model.</input_context>")
    input: str = Field(default="", max_length=100000, description="<input_context>Optional context supplied with the instruction.</input_context>")
    output: str = Field(min_length=1, max_length=100000, description="<critical_instructions>Expected grounded model response.</critical_instructions>")

class SamplesCreate(FinetuneRequest):
    samples: list[FinetuneSample] = Field(min_length=1, max_length=1000, description="<input_context>Bounded training samples to append.</input_context>")

class GeneratedSamples(FinetuneRequest):
    samples: list[FinetuneSample] = Field(min_length=1, max_length=10, description="<output_format>Grounded samples generated from one document segment.</output_format>")

class DocumentImport(FinetuneRequest):
    document_ids: list[str] = Field(min_length=1, max_length=100, description="<critical_instructions>Owned document identifiers used as training sources.</critical_instructions>")

class FinetuneJobCreate(FinetuneRequest):
    dataset_id: str = Field(min_length=1, max_length=128, description="<critical_instructions>Owned dataset selected for training.</critical_instructions>")
    job_name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="<input_context>Optional display name for the training job.</input_context>")
    base_model: Optional[str] = Field(default=None, min_length=1, max_length=300, description="<critical_instructions>Hugging Face model identifier or approved local model path.</critical_instructions>")
    method: Literal["lora"] = Field(default="lora", description="<critical_instructions>Supported parameter efficient training method.</critical_instructions>")
    epochs: int = Field(default=3, ge=1, le=20, description="<constraints>Number of complete passes through the dataset.</constraints>")
    learning_rate: float = Field(default=0.0002, gt=0, le=0.1, description="<constraints>Optimizer learning rate.</constraints>")
    batch_size: int = Field(default=4, ge=1, le=128, description="<constraints>Samples processed per training step.</constraints>")
    lora_rank: int = Field(default=16, ge=1, le=256, description="<constraints>Rank of the LoRA adapters.</constraints>")
    lora_alpha: int = Field(default=32, ge=1, le=512, description="<constraints>LoRA scaling factor.</constraints>")

class EvaluationRequest(FinetuneRequest):
    test_samples: list[FinetuneSample] = Field(min_length=1, max_length=1000, description="<input_context>Bounded benchmark samples.</input_context>")
    use_judge: bool = Field(default=True, description="<conditional_output>Whether to include structured language model judging.</conditional_output>")

class FinetuneJobUpdate(BaseModel):
    """
    Represents a snapshot of a model finetuning job's state.
    Values are optional because updates may only contain partial state changes (e.g., just progress or loss).
    """
    model_config = ConfigDict(extra="forbid")

    progress: Optional[float] = Field(default=None, ge=0, le=100, description="<conditional_output>The progress percentage.</conditional_output>")
    current_epoch: Optional[int] = Field(default=None, ge=0, le=1000, description="<conditional_output>The current training epoch.</conditional_output>")
    current_loss: Optional[float] = Field(default=None, ge=0, description="<conditional_output>The current training loss.</conditional_output>")
    loss: Optional[float] = Field(default=None, ge=0, description="<conditional_output>The loss value recorded for the current epoch.</conditional_output>")
    status: Optional[Literal["pending", "running", "completed", "failed", "cancelled"]] = Field(default=None, description="<conditional_output>The validated training lifecycle state.</conditional_output>")
    adapter_path: Optional[str] = Field(default=None, max_length=2000, description="<conditional_output>Path to the saved LoRA adapter.</conditional_output>")
    merged_path: Optional[str] = Field(default=None, max_length=2000, description="<conditional_output>Path to the merged model artifact.</conditional_output>")
    gguf_path: Optional[str] = Field(default=None, max_length=2000, description="<conditional_output>Path to the converted GGUF artifact.</conditional_output>")
    merged_model_name: Optional[str] = Field(default=None, max_length=500, description="<conditional_output>Name of the resulting merged model.</conditional_output>")
    error_message: Optional[str] = Field(default=None, max_length=2000, description="<conditional_output>Error message if the job failed.</conditional_output>")
    error_code: Optional[str] = Field(default=None, pattern=r"^[a-z0-9_]{1,100}$", description="<conditional_output>Stable machine readable failure code.</conditional_output>")
    best_loss: Optional[float] = Field(default=None, ge=0, description="<conditional_output>The best loss achieved so far.</conditional_output>")
