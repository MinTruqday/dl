from loguru import logger
import subprocess
import os
import uuid
from typing import Optional

def compile_latex(latex_str: str) -> Optional[bytes]:
    job_id = str(uuid.uuid4())
    tex_path = f"/tmp/{job_id}.tex"
    pdf_path = f"/tmp/{job_id}.pdf"
    
    if r"\documentclass" not in latex_str:
        latex_str = f"\\documentclass{{article}}\n\\usepackage[utf8]{{inputenc}}\n\\usepackage{{amsmath, amssymb, graphicx}}\n\\begin{{document}}\n{latex_str}\n\\end{{document}}"
        
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_str)
        
    try:
        subprocess.run(
            [
                "tectonic", 
                "--synctex", 
                "--keep-logs", 
                "-Z", "continue-on-errors",
                "-Z", "shell-escape",
                "--outdir", "/tmp", 
                tex_path
            ],
            check=True,
            capture_output=True,
            timeout=15
        )
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        return pdf_bytes
    except subprocess.CalledProcessError as e:
        logger.error(f"LaTeX compilation error: {e.stdout.decode('utf-8', errors='ignore')}")
        return None
    except subprocess.TimeoutExpired:
        logger.info("LaTeX compilation timeout")
        return None
    finally:
        for ext in [".tex", ".pdf", ".aux", ".log"]:
            path = f"/tmp/{job_id}{ext}"
            if os.path.exists(path):
                os.remove(path)
