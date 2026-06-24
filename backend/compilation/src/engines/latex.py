import asyncio
import glob
import os
import re
import tempfile

from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings


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
                raise Exception("Mã chứa lệnh không hợp lệ")

        job_id = str(uuid7())
        temp_dir = tempfile.gettempdir()
        tex_path = os.path.join(temp_dir, f"{job_id}.tex")
        pdf_path = os.path.join(temp_dir, f"{job_id}.pdf")

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
            await asyncio.wait_for(
                process.communicate(), timeout=settings.LONG_PROCESS_TIMEOUT
            )

            if not os.path.exists(pdf_path):
                raise Exception("Lỗi biên dịch do cú pháp không hợp lệ")

            with open(pdf_path, "rb") as f:
                return f.read()

        except asyncio.TimeoutError as e:
            if process:
                try:
                    process.kill()
                except Exception as e:
                    logger.warning(f"Lỗi dừng tác vụ biên dịch: {e}")
            raise Exception("Hết thời gian chờ quá trình biên dịch tài liệu")

        finally:
            for filepath in glob.glob(os.path.join(temp_dir, f"{job_id}.*")):
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.warning(f"Lỗi dọn dẹp tệp tạm thời: {e}")

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
                    logger.warning(f"Lỗi dọn dẹp tệp tạm thời: {e}")

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
                "README.md",
                "Exported from the document compilation service".encode("utf-8"),
            )
            zip_file.writestr(
                ".gitignore", "*.pdf\n*.aux\n*.log\n*.out".encode("utf-8")
            )
        return zip_buffer.getvalue()
