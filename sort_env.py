import os

env_path = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/.env"
with open(env_path, "r") as f:
    lines = [line.strip() for line in f if line.strip()]

# Classify keys
categories = {
    "SYSTEM": ["PROJECT_NAME", "VERSION", "URL", "FLARESOLVERR_URL", "NEXT_PUBLIC_API_URL", "INTERNAL_API_URL", "NEXT_PUBLIC_WS_URL"],
    "SECURITY": ["SECRET_KEY", "CORS_ALLOWED_ORIGINS", "ACCESS_TOKEN_EXPIRE_MINUTES", "REFRESH_TOKEN_EXPIRE_DAYS", "PLATFORM_ADMIN_ID"],
    "DATABASES": ["MONGODB_URI", "MONGODB_DB_NAME", "REDIS_URI", "INTELLIGENCE_REDIS_URI", "RABBITMQ_URI", "QDRANT_URL", "QDRANT_HOST", "QDRANT_PORT"],
    "GOOGLE_OAUTH": ["GOOGLE_CLIENT_ID", "NEXT_PUBLIC_GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI", "GOOGLE_AUTH_URL", "GOOGLE_TOKEN_URL", "GOOGLE_USERINFO_URL"],
    "PASSKEY": ["PASSKEY_RP_ID", "PASSKEY_RP_NAME", "PASSKEY_ALLOWED_ORIGINS"],
    "PAYOS": ["PAYOS_CLIENT_ID", "PAYOS_API_KEY", "PAYOS_CHECKSUM_KEY", "PAYOS_RETURN_URL", "PAYOS_API_URL"],
    "SMTP": ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SENDER_EMAIL", "SENDER_NAME"],
    "MINIO": ["MINIO_ENDPOINT", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY", "MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD", "MINIO_BUCKET_NAME", "MINIO_REGION", "MINIO_PUBLIC_URL", "MIN_FILE_SIZE_BYTES"],
    "AI_MODELS": ["TAVILY_API_KEY", "HF_TOKEN", "LLAMA_MODEL", "QWEN_MODEL", "EMBEDDING_MODEL", "RERANKER_MODEL", "NLLB_MODEL", "NLI_MODEL_NAME", "OLLAMA_BASE_URL", "OLLAMA_MODEL"],
    "AI_PARAMS": ["HYBRID_ALPHA", "EMBEDDING_DIMENSIONS", "EMBEDDING_BATCH_SIZE", "MEMORY_MAX_TURNS", "MAP_REDUCE_BATCH_SIZE", "MAP_REDUCE_MAX_CHUNKS", "TOOL_TIMEOUT_SECONDS", "TOOL_MAX_RETRIES", "CIRCUIT_BREAKER_THRESHOLD", "CIRCUIT_BREAKER_RESET_SECONDS", "MAX_CONTEXT_TOKENS", "CHARS_PER_TOKEN_APPROX", "DEFAULT_CHUNK_SIZE", "DEFAULT_CHUNK_OVERLAP"],
    "TELEMETRY": ["GF_SECURITY_ADMIN_PASSWORD", "RETURN_RESET_TOKEN_IN_RESPONSE", "LANGSMITH_TRACING", "LANGSMITH_ENDPOINT", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT"]
}

# Parse env lines
env_dict = {}
for line in lines:
    if "=" in line:
        k, v = line.split("=", 1)
        env_dict[k] = line

# Reorder
new_env_lines = []
for cat_name, cat_keys in categories.items():
    new_env_lines.append(f"# {cat_name}")
    for k in cat_keys:
        if k in env_dict:
            new_env_lines.append(env_dict[k])
            del env_dict[k]
    new_env_lines.append("")

# Any leftovers
if env_dict:
    new_env_lines.append("# OTHER")
    for k, line in env_dict.items():
        new_env_lines.append(line)
    new_env_lines.append("")

with open(env_path, "w") as f:
    f.write("\n".join(new_env_lines))
    
print("Sorted .env")
