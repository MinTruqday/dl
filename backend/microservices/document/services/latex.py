import os
import uuid
import tempfile
import asyncio
import glob
import re
import zipfile
import io
from fastapi import HTTPException
from loguru import logger
from datetime import datetime
from shared.core.database import db_client
class LatexService:
    @staticmethod
    async def clean_temp_files(current_user):
        temp_dir = tempfile.gettempdir()
        extensions_to_clean = ["*.aux", "*.log", "*.out", "*.fls", "*.fdb_latexmk", "*.synctex.gz"]
        total_bytes_freed = 0
        files_deleted = 0
        for ext in extensions_to_clean:
            for file_path in glob.glob(os.path.join(temp_dir, ext)):
                try:
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    total_bytes_freed += size
                    files_deleted += 1
                except Exception as e:
logger.info("Log message sanitized"))
logger.info("Log message sanitized"))
        return {"status": "success", "message": f"Đã dọn dẹp {files_deleted} tệp rác.", "bytes_freed": total_bytes_freed}
    @staticmethod
    async def compile_latex_preview(request, current_user):
        latex_code = request.content
        if request.is_fragment and "\\documentclass" not in latex_code:
            latex_code = f"""
\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{amsmath, amssymb, xcolor, graphicx, tikz}}
\\begin{{document}}
{latex_code}
\\end{{document}}
            """
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
                raise HTTPException(status_code=400, detail={"error": "Không thể biên dịch LaTeX.", "logs": log_content[-2048:], "parsed_errors": parsed_errors})
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
logger.info("Log message sanitized"))
            return pdf_bytes
        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception as e:
logger.info("Log message sanitized"))
            raise HTTPException(status_code=504, detail="Quá thời gian xử lý công thức LaTeX.")
        except HTTPException:
            raise
        except Exception as e:
logger.info("Log message sanitized"))
            raise HTTPException(status_code=500, detail="Lỗi trong quá trình biên dịch LaTeX.")
        finally:
            for ext in [".tex", ".pdf", ".aux", ".log", ".out"]:
                path = os.path.join(temp_dir, f"{job_id}{ext}")
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception as e:
logger.info("Log message sanitized"))
    @staticmethod
    async def format_latex(request):
        latex_code = request.content
        try:
            lines = latex_code.split("\n")
            formatted = []
            indent_level = 0
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("\\end{"):
                    indent_level = max(0, indent_level - 1)
                formatted.append("    " * indent_level + stripped)
                if stripped.startswith("\\begin{") and not stripped.startswith("\\begin{document}"):
                    indent_level += 1
            return {"formatted_content": "\n".join(formatted)}
        except Exception as e:
logger.info("Log message sanitized"))
            raise HTTPException(status_code=500, detail="Lỗi hệ thống khi đang định dạng mã LaTeX.")
    @staticmethod
    async def export_latex(request, current_user):
        if request.format not in ["docx", "html"]:
            raise HTTPException(status_code=400, detail="Định dạng không được hỗ trợ.")
        job_id = str(uuid.uuid4())
        temp_dir = tempfile.gettempdir()
        tex_path = os.path.join(temp_dir, f"{job_id}.tex")
        out_path = os.path.join(temp_dir, f"{job_id}.{request.format}")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(request.content)
        try:
            process = await asyncio.create_subprocess_exec(
                "pandoc", tex_path, "-o", out_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.communicate(), timeout=30)
            if not os.path.exists(out_path):
                raise HTTPException(status_code=500, detail="Máy chủ không thể tạo tập tin xuất bản theo yêu cầu.")
            with open(out_path, "rb") as f:
                file_bytes = f.read()
logger.info("Log message sanitized"))
            return file_bytes
        except Exception as e:
logger.info("Log message sanitized"))
            raise HTTPException(status_code=500, detail="Lỗi hệ thống trong quá trình xuất bản tập tin.")
        finally:
            for p in [tex_path, out_path]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception as e:
logger.info("Log message sanitized"))
    @staticmethod
    async def export_project_zip(request):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("main.tex", request.content.encode("utf-8"))
            zip_file.writestr("README.md", "Exported from DocLib Studio".encode("utf-8"))
            zip_file.writestr(".gitignore", "*.pdf\n*.aux\n*.log\n*.out".encode("utf-8"))
        return zip_buffer.getvalue()
    @staticmethod
    async def auto_save(request):
        db = db_client.mongodb.get_default_database()
        await db["documents"].update_one(
            {"_id": request.document_id},
            {"$set": {"content": request.content, "updated_at": datetime.utcnow()}}
        )
        return {"status": "success", "timestamp": datetime.utcnow().isoformat()}