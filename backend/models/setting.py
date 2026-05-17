from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime, timezone
from core.config import settings

class SystemSettings(BaseModel):
    commission_rate: float = Field(default=0.1)
    min_withdrawal_amount: int = Field(default=100000)
    topup_fees: Dict[str, float] = Field(default_factory=dict)
    
    llm_model: str = Field(default=settings.LLAMA_MODEL)
    embedding_model: str = Field(default=settings.EMBEDDING_MODEL)
    reranker_model: str = Field(default=settings.RERANKER_MODEL)
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
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    reranker_model: Optional[str] = None
    rag_hybrid_alpha: Optional[float] = None
    is_maintenance_mode: Optional[bool] = None
    maintenance_message: Optional[str] = None
