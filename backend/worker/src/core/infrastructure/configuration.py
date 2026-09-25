import os

from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    RABBITMQ_URI: str = os.environ["RABBITMQ_URI"]
    WORKER_DB_NAME: str = os.environ["WORKER_DB_NAME"]
    WORKER_MAX_RETRIES: int = int(os.environ["WORKER_MAX_RETRIES"])
    WORKER_REQUEST_TIMEOUT_SECONDS: float = float(
        os.environ["WORKER_REQUEST_TIMEOUT_SECONDS"]
    )
    WORKER_EXECUTION_TIMEOUT_SECONDS: float = float(
        os.environ["WORKER_EXECUTION_TIMEOUT_SECONDS"]
    )
    TESTING_URL: str = os.environ["TESTING_URL"].rstrip("/")


settings = Settings()
