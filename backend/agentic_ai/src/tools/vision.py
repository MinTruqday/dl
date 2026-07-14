import base64
from typing import Optional

from huggingface_hub import AsyncInferenceClient
from langchain_core.tools import tool
from loguru import logger

from src.core.infrastructure.configuration import settings

class VisionTool:
    """
    <module_purpose>
    <purpose>Analyzes images using a HuggingFace Vision-Language Model.</purpose>
    <metis_behavior>Accepts base64-encoded image data. Returns a textual description or answer to the question posed about the image.</metis_behavior>
    </module_purpose>
    """

    def __init__(self):
        self._client: Optional[AsyncInferenceClient] = None

    @property
    def client(self) -> AsyncInferenceClient:
        if self._client is None:
            self._client = AsyncInferenceClient(
                model=settings.QWEN_MODEL,
                token=settings.HF_TOKEN,
            )
        return self._client

    async def analyze_image(self, image_base64: str, question: str) -> str:
        logger.info("Vision analysis started")
        try:
            image_bytes = base64.b64decode(image_base64)
            response = await self.client.chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                            {"type": "text", "text": question},
                        ],
                    }
                ],
                max_tokens=1024,
            )
            result = response.choices[0].message.content
            logger.info("Vision analysis completed successfully")
            return result
        except Exception:
            logger.exception("Vision analysis failed")
            return "Hệ thống không thể phân tích hình ảnh này"

    async def describe_image(self, image_base64: str) -> str:
        return await self.analyze_image(
            image_base64,
            "Describe this image in detail, including any text, diagrams, code, or technical content visible.",
        )


vision_tool = VisionTool()


@tool
async def tool_analyze_image(image_base64: str, question: str) -> str:
    """
    <tool_definition>
    <purpose>Analyzes an image and answers a question about its content using a Vision-Language Model.</purpose>
    <input_params>image_base64: Base64-encoded image string. question: The question to answer about the image.</input_params>
    <return_value>Textual description or answer based on the image content.</return_value>
    </tool_definition>
    """
    return await vision_tool.analyze_image(image_base64, question)
