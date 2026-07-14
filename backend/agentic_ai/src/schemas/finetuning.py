from typing import Optional
from pydantic import BaseModel

class FinetuneJobUpdate(BaseModel):
    """
    <schema_definition>
    <purpose>Represents a snapshot of a model finetuning job's state.</purpose>
    <metis_constraint>Values are optional because updates may only contain partial state changes (e.g., just progress or loss).</metis_constraint>
    </schema_definition>
    """
    progress: Optional[float] = None
    current_epoch: Optional[int] = None
    current_loss: Optional[float] = None
    status: Optional[str] = None
    adapter_path: Optional[str] = None
    merged_model_name: Optional[str] = None
    error_message: Optional[str] = None
    best_loss: Optional[float] = None
