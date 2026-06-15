import base64
import os
import tempfile

from loguru import logger
from markitdown import MarkItDown


def extract_text_from_base64(base64_data: str, filename: str = "temp_file") -> str:
    try:
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]

        file_bytes = base64.b64decode(base64_data)

        ext = os.path.splitext(filename)[1] or ".pdf"

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        logger.info(
            "The system is currently extracting textual content from the uploaded file"
        )
        md = MarkItDown()
        result = md.convert(tmp_path)
        full_text = result.text_content

        os.remove(tmp_path)
        logger.info("The text extraction process completed successfully and the content is ready for further processing")
        return full_text
    except Exception:
        logger.error("The system encountered a failure while attempting to extract text from the provided file")
        return ""