import os
import glob
import subprocess
import json
from pathlib import Path
from langchain_core.tools import tool
from loguru import logger
import shlex

@tool
def glob_search(pattern: str, path: str = ".") -> str:
    """
    <tool_definition>
    
    The Glob Tool: A fast filename / path matching tool.
    It answers the question: "Which files exist whose path matches this pattern?"
    
    WHEN TO USE THIS TOOL:
    - Locating files by name or extension (e.g. all `*.py` or `*.tex` files).
    - Discovering the structure/layout of a codebase or document library before diving in.
    - Finding the most recently modified files matching a pattern.
    
    Parameters:
    - pattern: The glob pattern to match files against (e.g. `**/*.json`, `src/**/*.{py,tex}`).
    - path: The directory to search within. Defaults to the current working directory.
    
    Returns:
    - A JSON list of matching file paths, sorted by modification time (most recent first).
    
    </tool_definition>
    """
    try:
        if not path:
            path = "."
            
        search_path = os.path.join(path, pattern)
        
        cmd = ["rg", "--files", "--iglob", pattern, path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0 and result.returncode != 1:
            if result.returncode == 1:
                return json.dumps([])
            else:
                files = glob.glob(search_path, recursive=True)
        else:
            files = [f for f in result.stdout.splitlines() if f.strip()]
            
        file_mtimes = []
        for f in files:
            try:
                mtime = os.path.getmtime(f)
                file_mtimes.append((f, mtime))
            except FileNotFoundError:
                continue
                
        file_mtimes.sort(key=lambda x: x[1], reverse=True)
        sorted_files = [f[0] for f in file_mtimes]
        
        return json.dumps(sorted_files, indent=2)
    except Exception as e:
        logger.exception(f"Glob search failed for pattern: {pattern}")
        return json.dumps({"error": f"Error executing glob search: {str(e)}"})

@tool
def grep_search(
    pattern: str,
    path: str = ".",
    glob_pattern: str = None,
    file_type: str = None,
    output_mode: str = "files_with_matches",
    case_insensitive: bool = False,
    show_line_numbers: bool = False,
    context_after: int = 0,
    context_before: int = 0,
    context_both: int = 0,
    multiline: bool = False,
    head_limit: int = 0
) -> str:
    """
    <tool_definition>
    
    The Grep Tool: A powerful content search tool built on top of ripgrep (rg).
    It answers the question: "Which files contain text matching this pattern, and what are the matching lines?"
    
    WHEN TO USE THIS TOOL:
    - Finding where a function, variable, class, or string is defined or used.
    - Locating all occurrences of a pattern across a codebase.
    
    Parameters:
    - pattern: A regular expression to search for.
    - path: File or directory to search in. Defaults to the current working directory.
    - glob_pattern: Glob pattern to filter which files are searched (e.g. `*.docx`, `*.pdf`).
    - file_type: File type to search (e.g. `py`, `json`, `tex`).
    - output_mode: One of `content`, `files_with_matches` (default), or `count`.
    - case_insensitive: Case-insensitive search.
    - show_line_numbers: Show line numbers. Only applies when `output_mode` is `content`.
    - context_after: Lines of context to show After each match.
    - context_before: Lines of context to show Before each match.
    - context_both: Lines of context to show before and after each match.
    - multiline: Enable multiline mode so `.` matches newlines.
    - head_limit: Limit output to the first N lines/entries.
    
    </tool_definition>
    """
    try:
        cmd = ["rg"]
        
        if case_insensitive:
            cmd.append("-i")
        if multiline:
            cmd.append("--multiline")
            
        if output_mode == "files_with_matches":
            cmd.append("--files-with-matches")
        elif output_mode == "count":
            cmd.append("--count")
        elif output_mode == "content":
            if show_line_numbers:
                cmd.append("-n")
            if context_both > 0:
                cmd.extend(["-C", str(context_both)])
            else:
                if context_after > 0:
                    cmd.extend(["-A", str(context_after)])
                if context_before > 0:
                    cmd.extend(["-B", str(context_before)])
                    
        if file_type:
            cmd.extend(["-t", file_type])
        if glob_pattern:
            cmd.extend(["-g", glob_pattern])
            
        cmd.append("--")
        cmd.append(pattern)
        cmd.append(path)
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        output_lines = []
        try:
            if head_limit > 0:
                for _ in range(head_limit):
                    line = process.stdout.readline()
                    if not line:
                        break
                    output_lines.append(line.rstrip('\n'))
                process.terminate()
            else:
                stdout_data, stderr_data = process.communicate(timeout=30)
                output_lines = stdout_data.splitlines()
        except subprocess.TimeoutExpired:
            process.kill()
            return json.dumps({"error": "Search timed out after 30 seconds"})
            
        process.wait()
        
        if process.returncode != 0 and process.returncode != 1 and process.returncode != -15:
            if not output_lines:
                stderr_output = process.stderr.read() if process.stderr else "Unknown error"
                return json.dumps({"error": f"Ripgrep error (code {process.returncode}): {stderr_output}"})
                
        result_text = "\n".join(output_lines)
        return json.dumps({"result": result_text})
        
    except Exception as e:
        logger.exception(f"Grep search failed for pattern: {pattern}")
        return json.dumps({"error": f"Error executing grep search: {str(e)}"})
