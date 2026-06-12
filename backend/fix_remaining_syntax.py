import sys

def fix_file(filepath, replacements):
    with open(filepath, 'r') as f:
        content = f.read()
    new_content = content
    for k, v in replacements.items():
        new_content = new_content.replace(k, v)
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)

fix_file('/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/agentic-ai/src/store/vector_store.py', {
    "thời gian chờ60.0": "timeout=60.0"
})

fix_file('/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/agentic-ai/src/tools/api_tools.py', {
    "thời gian chờhttpx.Timeout(30.0)": "timeout=httpx.Timeout(30.0)"
})

fix_file('/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/agentic-ai/src/training/engine.py', {
    "thời gian chờ1800": "timeout=1800"
})

fix_file('/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/compiler/src/services/latex_engine.py', {
    r'r"\\input\s*\{?\s*\.\",': r'r"\\input\s*\{?\s*\.",',
    r'r"\\include\s*\{?\s*\.\",': r'r"\\include\s*\{?\s*\.",'
})
