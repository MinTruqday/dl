from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import os

class SystemSettings(BaseModel):
    commission_rate: float = Field(default_factory=lambda: float(os.getenv("DEFAULT_COMMISSION_RATE")))
    min_withdrawal_amount: int = Field(default_factory=lambda: int(os.getenv("MIN_WITHDRAWAL_AMOUNT")))
    topup_fees: Dict[str, float] = Field(default_factory=lambda: {k: float(v) for k, v in [item.split(":") for item in os.getenv("TOPUP_FEES").split(",")]})
    
    active_llm_model: str = Field(default_factory=lambda: os.getenv("ACTIVE_LLM_MODEL"))
    active_embedding_model: str = Field(default_factory=lambda: os.getenv("ACTIVE_EMBEDDING_MODEL"))
    active_reranker_model: str = Field(default_factory=lambda: os.getenv("ACTIVE_RERANKER_MODEL"))
    rag_hybrid_alpha: float = Field(default_factory=lambda: float(os.getenv("RAG_HYBRID_ALPHA")))
    rag_top_k: int = Field(default_factory=lambda: int(os.getenv("RAG_TOP_K")))
    
    is_registration_open: bool = Field(default_factory=lambda: os.getenv("IS_REGISTRATION_OPEN") == "true")
    is_maintenance_mode: bool = Field(default_factory=lambda: os.getenv("IS_MAINTENANCE_MODE") == "true")
    maintenance_message: Optional[str] = Field(default_factory=lambda: os.getenv("MAINTENANCE_MESSAGE"))
    
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

