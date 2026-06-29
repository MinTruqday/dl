import os
import uuid

os.environ["PROJECT_NAME"] = "test"
os.environ["VERSION"] = "1.0"
os.environ["SECRET_KEY"] = "secret"
os.environ["CORS_ALLOWED_ORIGINS"] = "*"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["PLATFORM_SYSTEM_ID"] = "system_1"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB_NAME"] = "test"
os.environ["SERVICE_DB_NAME"] = "test"
os.environ["REDIS_URI"] = "redis://localhost:6379"
os.environ["RABBITMQ_URI"] = "amqp://localhost"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["QDRANT_HOST"] = "localhost"
os.environ["QDRANT_PORT"] = "6333"
os.environ["SMTP_PORT"] = "587"
os.environ["MIN_FILE_SIZE_BYTES"] = "1024"
os.environ["EMBEDDING_DIMENSIONS"] = "768"
os.environ["EMBEDDING_BATCH_SIZE"] = "32"
os.environ["MEMORY_MAX_TURNS"] = "10"
os.environ["MAP_REDUCE_BATCH_SIZE"] = "10"
os.environ["MAP_REDUCE_MAX_CHUNKS"] = "10"
os.environ["TOOL_MAX_RETRIES"] = "3"
os.environ["CIRCUIT_BREAKER_THRESHOLD"] = "5"
os.environ["MAX_CONTEXT_TOKENS"] = "2000"
os.environ["CHARS_PER_TOKEN_APPROX"] = "4"
os.environ["DEFAULT_CHUNK_SIZE"] = "1000"
os.environ["DEFAULT_CHUNK_OVERLAP"] = "200"
os.environ["DEFAULT_PAGE_LIMIT"] = "10"
os.environ["MAX_PAGE_LIMIT"] = "100"
os.environ["HYBRID_ALPHA"] = "0.5"
os.environ["TOOL_TIMEOUT_SECONDS"] = "10.0"
os.environ["CIRCUIT_BREAKER_RESET_SECONDS"] = "60.0"
os.environ["DEFAULT_HTTP_TIMEOUT"] = "10.0"
os.environ["LONG_PROCESS_TIMEOUT"] = "60.0"
os.environ["HF_TOKEN"] = "dummy"
os.environ["MANAGEMENT_URL"] = "http://localhost"
os.environ["QWEN_MODEL"] = "qwen2"
os.environ["LLAMA_MODEL"] = "llama3"

from fastapi.testclient import TestClient
from src.main import app
from src.core.dependency import get_current_user, CurrentUser, Role, AITier

def override_get_current_user():
    return CurrentUser(
        id=uuid.uuid4(),
        role=Role.USER,
        ai_tier=AITier.FREE
    )

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_glossary():
    print("Testing giai-thich-thuat-ngu")
    response = client.post(
        "/suy-luan/giai-thich-thuat-ngu",
        json={"text": "Hệ thống AI này sử dụng mô hình ngôn ngữ lớn để phân tích văn bản"}
    )
    print("Status:", response.status_code)
    try:
        print("Response:", response.json())
    except:
        print("Response text:", response.text)

def test_imitate_style():
    print("Testing bat-chuoc-van-phong")
    response = client.post(
        "/suy-luan/bat-chuoc-van-phong",
        json={
            "text": "Hôm nay trời rất đẹp",
            "reference_text": "Nắng vàng ươm rải đều trên những tán lá xanh mướt"
        }
    )
    print("Status:", response.status_code)
    try:
        print("Response:", response.json())
    except:
        print("Response text:", response.text)

if __name__ == "__main__":
    test_glossary()
    test_imitate_style()
