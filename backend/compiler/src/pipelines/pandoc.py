import asyncio
import base64
import os
import tempfile
from loguru import logger

async def run_pandoc_export(job_id: str, content: str, format: str):
    if format not in ["docx", "html"]:
        return {"status": "error", "message": "Định dạng không được hỗ trợ."}
        
    temp_dir = tempfile.gettempdir()
    tex_path = os.path.join(temp_dir, f"{job_id}.tex")
    out_path = os.path.join(temp_dir, f"{job_id}.{format}")
    
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    try:
        process = await asyncio.create_subprocess_exec(
            "pandoc", tex_path, "-o", out_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(process.communicate(), timeout=30)
        
        if not os.path.exists(out_path):
            return {"status": "error", "message": "Máy chủ không thể tạo tập tin xuất bản theo yêu cầu."}
            
        with open(out_path, "rb") as f:
            file_bytes = f.read()
            
        return {"status": "success", "data": base64.b64encode(file_bytes).decode('ascii')}
        
    except Exception as e:
        logger.error(f"Pandoc export error: {e}")
        return {"status": "error", "message": "Lỗi hệ thống trong quá trình xuất bản tập tin."}
    finally:
        for p in [tex_path, out_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass
