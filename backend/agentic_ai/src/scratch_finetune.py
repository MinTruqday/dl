import re
import os

router_path = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/agentic_ai/src/router/finetune.py"
service_path = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/agentic_ai/src/services/finetune.py"

with open(router_path, "r") as f:
    content = f.read()

# Extract all functions after active_jobs = {}
service_code = """import asyncio
import json
import threading
from datetime import datetime, timezone
import httpx
from datasets import Dataset
from fastapi import HTTPException, Query
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from uuid6 import uuid7
from core.infrastructure.app_config import settings
from core.repositories.base_repository import RepositoryFactory

active_jobs = {}

def get_db():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    return client.get_default_database()

class FinetuneService:
"""

# Extracting all functions and making them static methods inside FinetuneService
# This is a bit complex. Let's just move the entire logic down.

# Alternatively, I can just copy the functions to service_path, indent them, and add @staticmethod.

