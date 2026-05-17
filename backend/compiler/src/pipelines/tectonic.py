import asyncio
import base64
import os
import tempfile
import re
from loguru import logger

async def run_tectonic_compile(job_id: str, content: str):
    temp_dir = tempfile.gettempdir()
    tex_path = os.path.join(temp_dir, f"{job_id}.tex")
    pdf_path = os.path.join(temp_dir, f"{job_id}.pdf")
    log_path = os.path.join(temp_dir, f"{job_id}.log")
    
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(content)
        
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
            return {"status": "error", "message": "Không thể biên dịch LaTeX.", "logs": log_content[-2048:], "parsed_errors": parsed_errors}
            
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
            
        return {"status": "success", "data": base64.b64encode(pdf_bytes).decode('ascii')}
        
    except asyncio.TimeoutError:
        try:
            process.kill()
        except:
            pass
        return {"status": "error", "message": "Quá thời gian xử lý công thức LaTeX."}
    except Exception as e:
        logger.error(f"LaTeX compilation error: {e}")
        return {"status": "error", "message": "Lỗi trong quá trình biên dịch LaTeX."}
    finally:
        for ext in [".tex", ".pdf", ".aux", ".log", ".out"]:
            path = os.path.join(temp_dir, f"{job_id}{ext}")
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
