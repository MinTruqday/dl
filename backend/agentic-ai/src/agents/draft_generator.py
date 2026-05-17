from loguru import logger
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.config import settings
import boto3
import uuid
import asyncio

class DraftGeneratorAgent:
    def __init__(self):
        _hf_endpoint = HuggingFaceEndpoint(
            repo_id=settings.LLAMA_MODEL,
            huggingfacehub_api_token=settings.HF_TOKEN,
            temperature=0.3
        )
        self.llm = ChatHuggingFace(llm=_hf_endpoint)

    async def execute(self, task_description: str, format_type: str = "markdown") -> str:
        logger.info(f"DraftGenerator: Generating draft in format={format_type}")
        
        system_prompt = f"""Bạn là một chuyên gia soạn thảo văn bản (Draft Generator Agent).
Nhiệm vụ của bạn là viết một bản nháp hoàn chỉnh theo định dạng {format_type}.
Văn bản phải được trình bày chuyên nghiệp, câu chữ rõ ràng.
Nếu được yêu cầu LaTeX, hãy trả về đúng cấu trúc chuẩn của LaTeX."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Yêu cầu: {task_description}")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.MINIO_ENDPOINT,
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY
            )
            file_name = f"drafts/{uuid.uuid4().hex}.{'tex' if format_type == 'latex' else 'md'}"
            s3_client.put_object(
                Bucket=settings.MINIO_BUCKET_NAME,
                Key=file_name,
                Body=content.encode('utf-8')
            )
            upload_status = f"Draft saved to storage: {file_name}"
            logger.info(f"DraftGenerator: {upload_status}")
            return f"{content}\n\n{upload_status}"
        except Exception as e:
            logger.error(f"DraftGenerator: Failed to generate draft: {e}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

draft_generator_agent = DraftGeneratorAgent()
