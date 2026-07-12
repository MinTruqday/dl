from typing import Optional
from pydantic import BaseModel

class FinetuneJobUpdate(BaseModel):
    progress: Optional[float] = None
    current_epoch: Optional[int] = None
    current_loss: Optional[float] = None
    status: Optional[str] = None
    adapter_path: Optional[str] = None
    merged_model_name: Optional[str] = None
    error_message: Optional[str] = None
    best_loss: Optional[float] = None
