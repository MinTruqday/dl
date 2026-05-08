import tempfile
import asyncio
import os
from loguru import logger
from fastapi import HTTPException

class CompilationService:
    @staticmethod
    async def compile_latex_to_pdf(content: str):
        if not content:
            raise HTTPException(status_code=400, detail="Nội dung tài liệu đang trống.")
            
        if "\\documentclass" not in content and "\\begin{document}" not in content:
            content = f"\\documentclass{{article}}\n\\usepackage{{amsmath,amssymb}}\n\\begin{{document}}\n{content}\n\\end{{document}}"
            
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tex_file = os.path.join(tmpdir, "main.tex")
                with open(tex_file, "w", encoding="utf-8") as f:
                    f.write(content)
                
                process = await asyncio.create_subprocess_exec(
                    "tectonic", tex_file, "--outdir", tmpdir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=20.0)
                except asyncio.TimeoutError:
                    process.kill()
                    raise HTTPException(status_code=408, detail="Quá thời gian xử lý biên dịch LaTeX (Timeout).")
                
                if process.returncode != 0:
                    err_msg = stderr.decode()
                    logger.info("Log message sanitized")
                    raise HTTPException(status_code=422, detail={"error": "Lỗi định dạng LaTeX, không thể biên dịch.", "logs": err_msg})
                    
                pdf_path = os.path.join(tmpdir, "main.pdf")
                if not os.path.exists(pdf_path):
                    raise HTTPException(status_code=500, detail="Tệp PDF không được tạo ra sau khi biên dịch.")
                    
                with open(pdf_path, "rb") as pdf_file:
                    pdf_data = pdf_file.read()
                    
                return pdf_data
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Compilation: System error during LaTeX compilation: {e}")
            raise HTTPException(status_code=500, detail="Lỗi hệ thống trong quá trình biên dịch tài liệu.")
