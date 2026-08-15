import os

from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    CORS_ALLOWED_ORIGINS: str = os.environ["CORS_ALLOWED_ORIGINS"]
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    REDIS_URI: str = os.environ["REDIS_URI"]
    AGENTIC_AI_DB_NAME: str = os.environ["AGENTIC_AI_DB_NAME"]
    CONTENT_URL: str = os.getenv("CONTENT_URL", "http://content:8000")
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://ollama:11434")
    LLM_MODEL: str = os.environ["LLM_MODEL"]
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    FINETUNE_MODELS_DIR: str = os.environ["FINETUNE_MODELS_DIR"]
    FINETUNE_ADAPTERS_DIR: str = os.environ["FINETUNE_ADAPTERS_DIR"]
    FINETUNE_GGUF_DIR: str = os.environ["FINETUNE_GGUF_DIR"]
    FINETUNE_BASE_MODEL: str = os.getenv(
        "FINETUNE_BASE_MODEL", "google/gemma-4-E4B-it"
    )


settings = Settings()
