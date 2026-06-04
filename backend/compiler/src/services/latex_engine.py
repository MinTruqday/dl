import os
import uuid
from uuid6 import uuid7
import tempfile
import asyncio
import glob
import re
from loguru import logger
class LatexEngine:
    DANGEROUS_PATTERNS = [
        r"\\input\s*\{?\s*/", r"\\include\s*\{?\s*/",
        r"\\input\s*\{?\s*\.\.", r"\\include\s*\{?\s*\.\.",
        r"\\lstinputlisting", r"\\openin", r"\\read",
        r"\\newwrite", r"\\openout", r"\\write"
    ]

    @staticmethod
    async def compile_to_pdf(content: str) -> bytes:
        for pattern in LatexEngine.DANGEROUS_PATTERNS:
            if re.search(pattern, content):
                raise Exception({"error": "Bảo mật: Mã LaTeX chứa các tập lệnh đọc file hoặc ghi file không được phép."})

        job_id = str(uuid7())
        temp_dir = tempfile.gettempdir()
        tex_path = os.path.join(temp_dir, f"{job_id}.tex")
        pdf_path = os.path.join(temp_dir, f"{job_id}.pdf")
        log_path = os.path.join(temp_dir, f"{job_id}.log")
        
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                "timeout", "-k", "35", "30",
                "tectonic", 
                "--synctex", 
                "--keep-logs", 
                "-Z", "continue-on-errors",
                "--outdir", temp_dir,
                tex_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024 * 2
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            if not os.path.exists(pdf_path):
                log_content = ""
                parsed_errors = []
                
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                        lf.seek(0, 2)
                        size = lf.tell()
                        lf.seek(max(size - 500000, 0))
                        log_content = lf.read()
                    
                    error_pattern = re.compile(r"!(.*?)\nl\.(\d+)(.*?)(?=\n|$)", re.IGNORECASE)
                    matches = error_pattern.findall(log_content)
                    for match in matches:
                        parsed_errors.append({
                            "line": int(match[1]),
                            "message": match[0].strip(),
                            "context": match[2].strip()[:100]
                        })
                
                raise Exception({
                    "error": "Không thể biên dịch LaTeX.", 
                    "logs": log_content[-2048:], 
                    "parsed_errors": parsed_errors
                })
                
            with open(pdf_path, "rb") as f:
                return f.read()
                
        except asyncio.TimeoutError:
            if process:
                try:
                    process.kill()
                except Exception as e:
                    logger.warning(f"LatexEngine: Lỗi khi kill process: {e}")
            raise Exception("Quá thời gian biên dịch tài liệu LaTeX (Max 30s).")
            
        finally:
            for filepath in glob.glob(os.path.join(temp_dir, f"{job_id}.*")):
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.warning(f"LatexEngine: Không thể dọn dẹp file {filepath}: {e}")

    @staticmethod
    async def export_to_format(content: str, target_format: str) -> bytes:
        job_id = str(uuid7())
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
            for filepath in glob.glob(os.path.join(temp_dir, f"{job_id}.*")):
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.warning(f"LatexEngine: Không thể dọn dẹp file {filepath}: {e}")
