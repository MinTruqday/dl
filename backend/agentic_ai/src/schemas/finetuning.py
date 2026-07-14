from typing import Optional
from pydantic import BaseModel, Field

class FinetuneJobUpdate(BaseModel):
    """
    Represents a snapshot of a model finetuning job's state.
    Values are optional because updates may only contain partial state changes (e.g., just progress or loss).
    """
    progress: Optional[float] = Field(default=None, description="<conditional_output>The progress percentage.</conditional_output>")
    current_epoch: Optional[int] = Field(default=None, description="<conditional_output>The current training epoch.</conditional_output>")
    current_loss: Optional[float] = Field(default=None, description="<conditional_output>The current training loss.</conditional_output>")
    status: Optional[str] = Field(default=None, description="<conditional_output>The current status (e.g. RUNNING, SUCCESS).</conditional_output>")
    adapter_path: Optional[str] = Field(default=None, description="<conditional_output>Path to the saved LoRA adapter.</conditional_output>")
    merged_model_name: Optional[str] = Field(default=None, description="<conditional_output>Name of the resulting merged model.</conditional_output>")
    error_message: Optional[str] = Field(default=None, description="<conditional_output>Error message if the job failed.</conditional_output>")
    best_loss: Optional[float] = Field(default=None, description="<conditional_output>The best loss achieved so far.</conditional_output>")
