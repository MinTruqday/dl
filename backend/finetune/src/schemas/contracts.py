from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

class TrainingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

class DatasetCreate(TrainingRequest):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    source: Literal["manual", "feedback", "documents"] = Field(default="manual")

class TrainingSample(TrainingRequest):
    instruction: str = Field(min_length=1, max_length=100000)
    input: str = Field(default="", max_length=100000)
    output: str = Field(min_length=1, max_length=100000)

class SamplesCreate(TrainingRequest):
    samples: list[TrainingSample] = Field(min_length=1, max_length=1000)

class GeneratedSamples(TrainingRequest):
    samples: list[TrainingSample] = Field(min_length=1, max_length=10)

class DocumentImport(TrainingRequest):
    document_ids: list[str] = Field(min_length=1, max_length=100)

class TrainingJobCreate(TrainingRequest):
    dataset_id: str = Field(min_length=1, max_length=128)
    job_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    base_model: Optional[str] = Field(default=None, min_length=1, max_length=300)
    method: Literal["lora"] = Field(default="lora")
    epochs: int = Field(default=3, ge=1, le=20)
    learning_rate: float = Field(default=0.0002, gt=0, le=0.1)
    batch_size: int = Field(default=4, ge=1, le=128)
    lora_rank: int = Field(default=16, ge=1, le=256)
    lora_alpha: int = Field(default=32, ge=1, le=512)

class EvaluationRequest(TrainingRequest):
    test_samples: list[TrainingSample] = Field(min_length=1, max_length=1000)
    use_judge: bool = Field(default=True)

class TrainingJobUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    progress: Optional[float] = Field(default=None, ge=0, le=100)
    current_epoch: Optional[int] = Field(default=None, ge=0, le=1000)
    current_loss: Optional[float] = Field(default=None, ge=0)
    loss: Optional[float] = Field(default=None, ge=0)
    status: Optional[Literal["pending", "running", "completed", "failed", "cancelled"]] = Field(default=None)
    adapter_path: Optional[str] = Field(default=None, max_length=2000)
    merged_path: Optional[str] = Field(default=None, max_length=2000)
    gguf_path: Optional[str] = Field(default=None, max_length=2000)
    merged_model_name: Optional[str] = Field(default=None, max_length=500)
    error_message: Optional[str] = Field(default=None, max_length=2000)
    error_code: Optional[str] = Field(default=None, pattern=r"^[a-z0-9_]{1,100}$")
    best_loss: Optional[float] = Field(default=None, ge=0)
