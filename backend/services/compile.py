import tempfile
import subprocess
import os
from loguru import logger
from fastapi import HTTPException

class CompileService:
    @staticmethod
    async def compile_latex_to_pdf(content: str):
        if not content:
            raise HTTPException(status_code=400, detail="Nội dung trống.")
            
        if "\\documentclass" not in content and "\\begin{document}" not in content:
            content = f"\\documentclass{{article}}\n\\usepackage{{amsmath,amssymb}}\n\\begin{{document}}\n{content}\n\\end{{document}}"
            
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tex_file = os.path.join(tmpdir, "main.tex")
                with open(tex_file, "w", encoding="utf-8") as f:
                    f.write(content)
                
                result = subprocess.run(
                    ["tectonic", tex_file, "--outdir", tmpdir],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if result.returncode != 0:
                    logger.error(f"Tectonic error: {result.stderr}")
                    raise HTTPException(status_code=422, detail={"error": "Không thể tạo công thức toán học.", "logs": result.stderr})
                    
                pdf_path = os.path.join(tmpdir, "main.pdf")
                if not os.path.exists(pdf_path):
                    raise HTTPException(status_code=500, detail="Không thể tạo file PDF.")
                    
                with open(pdf_path, "rb") as pdf_file:
                    pdf_data = pdf_file.read()
                    
                return pdf_data
                
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=408, detail="Quá thời gian xử lý, vui lòng thử lại.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Compilation error: {str(e)}")
            raise HTTPException(status_code=500, detail="Lỗi trong quá trình biên dịch LaTeX.")
