from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from core.config import settings

class SystemSettings(BaseModel):
    commission_rate: float = Field(default=0.1)
    min_withdrawal_amount: int = Field(default=100000)
    topup_fees: Dict[str, float] = Field(default_factory=dict)
    
    active_llm_model: str = Field(default=settings.ACTIVE_LLM_MODEL)
    active_embedding_model: str = Field(default="BAAI/bge-m3")
    active_reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3")
    rag_hybrid_alpha: float = Field(default=settings.HYBRID_ALPHA)
    rag_top_k: int = Field(default=5)
    
    is_registration_open: bool = Field(default=True)
    is_maintenance_mode: bool = Field(default=False)
    maintenance_message: Optional[str] = Field(default=None)
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SettingsInDB(SystemSettings):
    id: str = Field(default="global_settings", alias="_id")

class SettingsUpdate(BaseModel):
    commission_rate: Optional[float] = None
    min_withdrawal_amount: Optional[int] = None
    topup_fees: Optional[Dict[str, float]] = None
    active_llm_model: Optional[str] = None
    rag_hybrid_alpha: Optional[float] = None
    is_maintenance_mode: Optional[bool] = None
    maintenance_message: Optional[str] = None

