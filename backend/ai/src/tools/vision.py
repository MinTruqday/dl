import base64
from langchain_core.tools import tool
from loguru import logger

from src.utils.local_models import local_model_client


class VisionTool:
    """
    <module_purpose>Analyzes images using a HuggingFace Vision-Language Model.</module_purpose>
    <contract>Accepts base64-encoded image data. Returns a textual description or answer to the question posed about the image.</contract>
    """

    def __init__(self):
        self._client = local_model_client

    @property
    def client(self):
        return self._client

    async def analyze_image(self, image_base64: str, question: str) -> str:
        logger.info("Vision analysis started")
        try:
            if len(image_base64) > 20_000_000 or len(question) > 4000:
                raise ValueError("vision_input_limit_exceeded")
            base64.b64decode(image_base64, validate=True)
            response = await self.client.chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                            },
                            {"type": "text", "text": question},
                        ],
                    }
                ],
                max_tokens=1024,
            )
            result = response.choices[0].message.content
            logger.info("Vision analysis completed")
            return result
        except Exception:
            logger.exception("Vision analysis failed")
            raise RuntimeError("vision_analysis_failed")

    async def describe_image(self, image_base64: str) -> str:
        return await self.analyze_image(
            image_base64,
            "Describe this image in detail, including any text, diagrams, code, or technical content visible.",
        )


vision_tool = VisionTool()


@tool
async def tool_analyze_image(image_base64: str, question: str) -> str:
    """
    <module_purpose>
    Analyzes an image and answers a question about its content using a Vision-Language Model.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Understanding and analyzing images based on a user question.

    Parameters:
    - image_base64: Base64-encoded image string.
    - question: The question to answer about the image.

    Returns:
    - Textual description or answer based on the image content.
    </contract>
    """
    return await vision_tool.analyze_image(image_base64, question)
