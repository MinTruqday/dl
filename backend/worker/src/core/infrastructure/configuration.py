import os

class Settings:
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    RABBITMQ_URI: str = os.environ["RABBITMQ_URI"]
    WORKER_DB_NAME: str = os.environ["WORKER_DB_NAME"]
    WORKER_QUEUE_NAME: str = os.environ["WORKER_QUEUE_NAME"]
    TESTING_URL: str = os.environ["TESTING_URL"].rstrip("/")


settings = Settings()
