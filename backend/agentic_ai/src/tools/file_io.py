import os
import json
from langchain_core.tools import tool
from loguru import logger

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
        if not os.path.exists(file_path):
            return json.dumps({"error": f"File not found: {file_path}"})
            
        start_line = chunk_index * chunk_size
        end_line = start_line + chunk_size
        
        lines = []
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= end_line:
                    break
                if i >= start_line:
                    lines.append(line.rstrip('\n'))
                    
        total_read = len(lines)
        if total_read == 0:
            return json.dumps({"status": "EOF", "message": "No more lines to read from this chunk index."})
            
        return json.dumps({
            "status": "success",
            "chunk_index": chunk_index,
            "start_line": start_line,
            "end_line": start_line + total_read - 1,
            "lines": lines
        }, indent=2)
    except Exception as e:
        logger.exception(f"Error reading chunk from {file_path}")
        return json.dumps({"error": f"Failed to read file: {str(e)}"})
