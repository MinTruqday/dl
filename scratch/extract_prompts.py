import os
import re

src_dir = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/agentic-ai/src"
files = [
    "workflow/semantic_router.py",
    "workflow/aggregator.py",
    "api/chat.py",
    "rag/retrieval.py",
    "api/inference.py",
    "workflow/dispatcher.py",
    "agents/code_interpreter.py",
    "agents/reasoning.py",
    "agents/draft_generator.py"
]

import ast

def extract_strings(filepath):
    with open(filepath, "r") as f:
        content = f.read()
    
    matches = re.finditer(r'(f?"""SYSTEM IDENTITY:[\s\S]*?"""|f"SYSTEM IDENTITY:[\s\S]*?")', content)
    for m in matches:
        print(f"\n--- {filepath} ---")
        print(m.group(0))

for f in files:
    extract_strings(os.path.join(src_dir, f))
