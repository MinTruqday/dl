import base64
import datetime
import os
import uuid

from src.repositories.license import LicenseRepository

class LicenseService:
    @staticmethod
    async def create_license(document_id: str, user_id: str) -> tuple[str, bytes]:
        file_id = str(uuid.uuid4())
        raw_key = os.urandom(32)  
        encoded_key = base64.b64encode(raw_key).decode("utf-8")
        
        await LicenseRepository.create_license(
            {
                "file_id": file_id,
                "aes_key": encoded_key,
                "document_id": document_id,
                "user_id": user_id,
                "created_at": datetime.datetime.now(datetime.timezone.utc),
                "status": "ACTIVE",
                "open_count": 0,
            }
        )
        return file_id, raw_key
