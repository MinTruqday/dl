import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    CORS_ALLOWED_ORIGINS: str = ""

    JWT_SECRET_KEY: str = "secret"
    JWT_ALGORITHM: str = "HS256"

    MONGODB_URI: str = "mongodb://mongodb:27017"
    RAG_DB_NAME: str = "doclib_rag"
    CONTENT_DB_NAME: str = "doclib_content"

    REDIS_URI: str = "redis://redis:6379/0"

    QDRANT_URL: str = "http://qdrant:6333"
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "doclib_neo4j_password"

    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    RERANKER_MODEL: str = "BAAI/bge-reranker-large"

    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_PUBLIC_BUCKET: str = "doclib-public"
    MINIO_PRIVATE_BUCKET: str = "doclib-private"

    CONTENT_SERVICE_URL: str = "http://content:8000"
    DRM_SERVICE_URL: str = "http://drm:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
