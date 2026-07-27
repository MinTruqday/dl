import json
from pathlib import Path
from langchain_core.tools import tool
from loguru import logger
from src.core.infrastructure.configuration import settings

@tool
def read_large_file_chunk(file_path: str, chunk_index: int = 0, chunk_size: int = 1000) -> str:
    """
    <module_purpose>
    Read a specific chunk of lines from a large file to avoid exceeding memory or LLM context limits.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this to read large log files, huge CSVs, or unformatted text files in chunks.
    - `chunk_index` is 0-indexed.
    - `chunk_size` is the number of lines to read per chunk (default 1000).
    </contract>
    """
    try:
        root = Path(settings.AGENT_FILE_ROOT).resolve()
        supplied_path = Path(file_path)
        target = (
            supplied_path.resolve()
            if supplied_path.is_absolute()
            else (root / supplied_path).resolve()
        )
        if not target.is_relative_to(root):
            return json.dumps({"status": "file_access_denied"})
        if not target.is_file():
            return json.dumps({"status": "file_not_found"})
            
        start_line = chunk_index * chunk_size
        end_line = start_line + chunk_size
        
        lines = []
        with target.open("r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= end_line:
                    break
                if i >= start_line:
                    lines.append(line.rstrip('\n'))
                    
        total_read = len(lines)
        if total_read == 0:
            return json.dumps({"status": "eof"})
            
        return json.dumps({
            "status": "success",
            "chunk_index": chunk_index,
            "start_line": start_line,
            "end_line": start_line + total_read - 1,
            "lines": lines
        }, indent=2)
    except Exception:
        logger.exception("File chunk read failed")
        return json.dumps({"status": "file_read_failed"})
