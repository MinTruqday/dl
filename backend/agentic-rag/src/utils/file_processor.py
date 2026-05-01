import base64
import tempfile
import os
from markitdown import MarkItDown
from loguru import logger

def extract_text_from_base64(base64_data: str, filename: str = "temp_file") -> str:
    try:
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]
            
        file_bytes = base64.b64decode(base64_data)
        
        ext = os.path.splitext(filename)[1] or ".pdf"
        
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
            
        logger.info(f"Extracting text from uploaded file: {filename} ({ext})")
        md = MarkItDown()
        result = md.convert(tmp_path)
        full_text = result.text_content
        
        os.remove(tmp_path)
        logger.info(f"Extracted {len(full_text)} characters from upload.")
        return full_text
    except Exception as e:
        logger.error(f"Failed to extract text from upload: {e}")
        return ""
