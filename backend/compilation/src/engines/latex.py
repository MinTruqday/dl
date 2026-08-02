import asyncio
import io
import os
import re
import resource
import signal
import tempfile
import zipfile

from src.core.infrastructure.configuration import settings


compile_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_COMPILATIONS)


def limit_process():
    resource.setrlimit(resource.RLIMIT_CPU, (25, 25))
    resource.setrlimit(resource.RLIMIT_AS, (4 * 1024 * 1024 * 1024, 4 * 1024 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (settings.MAX_COMPILE_OUTPUT_BYTES, settings.MAX_COMPILE_OUTPUT_BYTES))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_NPROC, (4096, 4096))


async def run_process(arguments: list[str], working_directory: str):
    environment = os.environ.copy()
    environment["GHCRTS"] = "-N1"
    process = await asyncio.create_subprocess_exec(
        *arguments,
        cwd=working_directory,
        env=environment,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        limit=2 * 1024 * 1024,
        preexec_fn=limit_process,
        start_new_session=True,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
    except asyncio.TimeoutError:
        os.killpg(process.pid, signal.SIGKILL)
        await process.wait()
        raise ValueError("Quá trình biên dịch vượt quá thời gian tối đa")
    if process.returncode != 0:
        message = stderr.decode("utf-8", errors="ignore")[-2000:]
        raise ValueError(message or "Quá trình biên dịch thất bại")
    return stdout, stderr


class LatexEngine:
    dangerous_patterns = [
        r"\\(?:input|include|lstinputlisting|openin|read|newwrite|openout|write|immediate|write18)\b",
        r"\\usepackage\s*\{[^}]*shellesc[^}]*\}",
        r"(?:https?|file|ftp)://",
        r"\\(?:catcode|csname)\b",
    ]

    @staticmethod
    def validate_content(content: str):
        encoded = content.encode("utf-8")
        if not encoded or len(encoded) > settings.MAX_COMPILE_INPUT_BYTES:
            raise ValueError("Kích thước nội dung biên dịch không hợp lệ")
        for pattern in LatexEngine.dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                raise ValueError("Mã nguồn tài liệu chứa chỉ thị không an toàn")

    @staticmethod
    async def compile_to_pdf(content: str) -> bytes:
        LatexEngine.validate_content(content)
        async with compile_semaphore:
            with tempfile.TemporaryDirectory(prefix="doclib_latex_") as temp_dir:
                tex_path = os.path.join(temp_dir, "main.tex")
                pdf_path = os.path.join(temp_dir, "main.pdf")
                with open(tex_path, "w", encoding="utf-8") as stream:
                    stream.write(content)
                await run_process(
                    [
                        "tectonic",
                        "--untrusted",
                        "--outdir",
                        temp_dir,
                        tex_path,
                    ],
                    temp_dir,
                )
                if not os.path.isfile(pdf_path):
                    raise ValueError("Quá trình biên dịch không tạo được tệp PDF")
                size = os.path.getsize(pdf_path)
                if size < 1 or size > settings.MAX_COMPILE_OUTPUT_BYTES:
                    raise ValueError("Kích thước tệp kết quả không hợp lệ")
                with open(pdf_path, "rb") as stream:
                    return stream.read()

    @staticmethod
    async def export_to_format(content: str, target_format: str) -> bytes:
        LatexEngine.validate_content(content)
        if target_format not in {"docx", "html"}:
            raise ValueError("Định dạng xuất không được hỗ trợ")
        async with compile_semaphore:
            with tempfile.TemporaryDirectory(prefix="doclib_latex_export_") as temp_dir:
                tex_path = os.path.join(temp_dir, "main.tex")
                output_path = os.path.join(temp_dir, f"document.{target_format}")
                with open(tex_path, "w", encoding="utf-8") as stream:
                    stream.write(content)
                await run_process(
                    ["pandoc", tex_path, "-o", output_path],
                    temp_dir,
                )
                if not os.path.isfile(output_path):
                    raise ValueError("Quá trình xuất không tạo được tệp kết quả")
                size = os.path.getsize(output_path)
                if size < 1 or size > settings.MAX_COMPILE_OUTPUT_BYTES:
                    raise ValueError("Kích thước tệp kết quả không hợp lệ")
                with open(output_path, "rb") as stream:
                    return stream.read()

    @staticmethod
    def format_latex(content: str) -> dict:
        LatexEngine.validate_content(content)
        lines = content.split("\n")
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

    @staticmethod
    def export_project_zip(content: str) -> bytes:
        LatexEngine.validate_content(content)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("main.tex", content.encode("utf-8"))
            archive.writestr("README.md", b"Exported from DocLib")
            archive.writestr(".gitignore", b"*.pdf\n*.aux\n*.log\n*.out")
        result = zip_buffer.getvalue()
        if len(result) > settings.MAX_COMPILE_OUTPUT_BYTES:
            raise ValueError("Kích thước tệp kết quả không hợp lệ")
        return result
