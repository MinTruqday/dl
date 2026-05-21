import os
import uuid
import tempfile
import asyncio
import glob
import re
from loguru import logger
class LatexEngine:
    @staticmethod
    async def compile_to_pdf(content: str) -> bytes:
        latex_code = content
        
        job_id = str(uuid.uuid4())
        temp_dir = tempfile.gettempdir()
        tex_path = os.path.join(temp_dir, f"{job_id}.tex")
        pdf_path = os.path.join(temp_dir, f"{job_id}.pdf")
        log_path = os.path.join(temp_dir, f"{job_id}.log")
        
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_code)
            
        try:
            process = await asyncio.create_subprocess_exec(
                "tectonic", 
                "--synctex", 
                "--keep-logs", 
                "-Z", "continue-on-errors",
                "-Z", "shell-escape",
                "--outdir", temp_dir,
                tex_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            if not os.path.exists(pdf_path):
                log_content = stdout.decode('utf-8', errors='ignore') + stderr.decode('utf-8', errors='ignore')
                parsed_errors = []
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                        log_content = lf.read()
                    
                    error_pattern = re.compile(r"!(.*?)l\.(\d+)(.*)", re.DOTALL)
                    matches = error_pattern.findall(log_content)
                    for match in matches:
                        parsed_errors.append({
                            "line": int(match[1]),
                            "message": match[0].strip(),
                            "context": match[2].strip().split("\n")[0][:100]
                        })
                
                raise Exception({
                    "error": "Không thể biên dịch LaTeX.", 
                    "logs": log_content[-2048:], 
                    "parsed_errors": parsed_errors
                })
                
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
                
            return pdf_bytes
            
        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception as e:
                logger.warning(f"LatexEngine: Failed to kill process: {e}")
            raise Exception("Quá thời gian biên dịch tài liệu LaTeX")
            
        finally:
            for ext in [".tex", ".pdf", ".aux", ".log", ".out", ".fls", ".fdb_latexmk"]:
                path = os.path.join(temp_dir, f"{job_id}{ext}")
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception as e:
                        logger.warning(f"LatexEngine: Failed to remove temp file: {e}")

    @staticmethod
    async def export_to_format(content: str, target_format: str) -> bytes:
        job_id = str(uuid.uuid4())
        temp_dir = tempfile.gettempdir()
        tex_path = os.path.join(temp_dir, f"{job_id}.tex")
        out_path = os.path.join(temp_dir, f"{job_id}.{target_format}")
        
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
                raise Exception("Không thể chuyển đổi định dạng tài liệu")
                
            with open(out_path, "rb") as f:
                return f.read()
        finally:
            for p in [tex_path, out_path]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception as e:
                        logger.warning(f"LatexEngine: Failed to remove temp file: {e}")
