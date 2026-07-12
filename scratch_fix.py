import os
import re

files_to_fix = [
    "backend/agentic_ai/src/tools/interface.py",
    "backend/agentic_ai/src/tools/drm.py",
    "backend/agentic_ai/src/workflow/reduction.py"
]

pattern = re.compile(
    r'<overview>\s*(.*?)\s*</overview>\s*<when_to_use>\s*(.*?)\s*</when_to_use>\s*<constraints>\s*(.*?)\s*</constraints>',
    re.DOTALL
)

def format_docstring(match):
    overview = match.group(1).strip()
    when = match.group(2).strip()
    constraints = match.group(3).strip()
    
    # Format according to Fable 5
    new_doc = f"{overview}\n\n    WHEN TO USE THIS TOOL:\n    {when}\n\n    CRITICAL: {constraints}"
    # Indentation adjustment is tricky with regex replace, let's just do a clean replace 
    # replacing the whole tags with the formatted ones, keeping the indentation of the tags
    
    return new_doc

for fpath in files_to_fix:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Let's write a custom replacer to maintain indentation
    # Actually, the regex replaces the inner contents.
    
    def replacer(m):
        overview = m.group(1).strip()
        when = m.group(2).strip()
        constraints = m.group(3).strip()
        
        # We need to prepend the right indentation (usually 4 spaces)
        res = f"{overview}\n\n    WHEN TO USE THIS TOOL:\n    - {when}\n\n    CRITICAL: {constraints}"
        return res

    new_content = pattern.sub(replacer, content)
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"Fixed {fpath}")

