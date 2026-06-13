import asyncio
import glob
import os
import re
import tempfile
import uuid

from loguru import logger
from uuid6 import uuid7
from core.config import settings


class LatexEngine:
    DANGEROUS_PATTERNS = [
        r"\\input\s*\{?\s*/",
        r"\\include\s*\{?\s*/",
        r"\\input\s*\{?\s*\.",
        r"\\include\s*\{?\s*\.",
        r"\\lstinputlisting",
        r"\\openin",
        r"\\read",
        r"\\newwrite",
        r"\\openout",
        r"\\write",
    ]

    @staticmethod
    async def compile_to_pdf(content: str) -> bytes:
        for pattern in LatexEngine.DANGEROUS_PATTERNS:
            if re.search(pattern, content):
                raise Exception(
                    {
                        "error": "Bảo mật: Mã LaTeX chứa các tập lệnh đọc file hoặc ghi file không được phép"
                    }
                )

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
                "timeout",
                "-k",
                "35",
                "30",
                "tectonic",
                "--synctex",
                "--keep-logs",
                "-Z",
                "continue-on-errors",
                "--outdir",
                temp_dir,
                tex_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024 * 2,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=settings.LONG_PROCESS_TIMEOUT
            )

            if not os.path.exists(pdf_path):
                log_content = ""
                parsed_errors = []

                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                        lf.seek(0, 2)
                        size = lf.tell()
                        lf.seek(max(size - 500000, 0))
                        log_content = lf.read()

                    error_pattern = re.compile(
                        r"!(.*?)\nl\.(\d+)(.*?)(?=\n|$)", re.IGNORECASE
                    )
                    matches = error_pattern.findall(log_content)
                    for match in matches:
                        parsed_errors.append(
                            {
                                "line": int(match[1]),
                                "message": match[0].strip(),
                                "context": match[2].strip()[:100],
                            }
                        )

                raise Exception(
                    {
                        "error": "Lỗi biên dịch LaTeX",
                        "logs": log_content[-2048:],
                        "parsed_errors": parsed_errors,
                    }
                )

            with open(pdf_path, "rb") as f:
                return f.read()

        except asyncio.TimeoutError:
            if process:
                try:
                    process.kill()
                except Exception as e:
                    logger.warning("Lỗi dừng tiến trình biên dịch")
            raise Exception("Lỗi biên dịch LaTeX quá thời gian")

        finally:
            for filepath in glob.glob(os.path.join(temp_dir, f"{job_id}.*")):
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.warning("Lỗi dọn dẹp tệp tạm {filepath}")

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
                "pandoc",
                tex_path,
                "-o",
                out_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(
                process.communicate(), timeout=settings.LONG_PROCESS_TIMEOUT
            )

            if not os.path.exists(out_path):
                raise Exception("Lỗi chuyển đổi định dạng tài liệu")

            with open(out_path, "rb") as f:
                return f.read()
        finally:
            for filepath in glob.glob(os.path.join(temp_dir, f"{job_id}.*")):
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.warning("Lỗi dọn dẹp tệp tạm {filepath}")

    @staticmethod
    def format_latex(content: str) -> dict:
        lines = content.split("\n")
        formatted = []
        indent_level = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("\\end{"):
                indent_level = max(0, indent_level - 1)
            formatted.append("    " * indent_level + stripped)
            if stripped.startswith("\\begin{") and (
                not stripped.startswith("\\begin{document}")
            ):
                indent_level += 1
        return {"formatted_content": "\n".join(formatted)}

    @staticmethod
    def export_project_zip(content: str) -> bytes:
        import io
        import zipfile

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("main.tex", content.encode("utf-8"))
            zip_file.writestr(
                "README.md", "Exported from DocLib Studio".encode("utf-8")
            )
            zip_file.writestr(
                ".gitignore", "*.pdf\n*.aux\n*.log\n*.out".encode("utf-8")
            )
        return zip_buffer.getvalue()
