import os
import re

target_dirs = [
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/worker',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/signal',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/provision',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/contact',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/content',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/compiler',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/authentication',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/finance',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/websocket',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/core',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/collector',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/agentic-ai'
]

# We need a robust regex to find anything matching `[a-zA-Z_]*lên[a-zA-Z_]*` outside of string literals?
# Or just replace all known english variables that got corrupted.
replacements = {
    "lênol": "tool",
    "Lênol": "Tool",
    "lênken": "token",
    "Lênken": "Token",
    "slênre": "store",
    "Slênre": "Store",
    "veclênr": "vector",
    "Veclênr": "Vector",
    "molênr": "motor",
    "Molênr": "Motor",
    "hislênry": "history",
    "Hislênry": "History",
    "aulên": "auto",
    "Aulên": "Auto",
    "cuslênm": "custom",
    "Cuslênm": "Custom",
    "monilênr": "monitor",
    "Monilênr": "Monitor",
    "faclênry": "factory",
    "Faclênry": "Factory",
    "direclênry": "directory",
    "Direclênry": "Directory",
    "lênday": "today",
    "lênmorrow": "tomorrow",
    "botlênm": "bottom",
    "photlên": "photo",
    "cryptlên": "crypto",
    "butlênn": "button",
    "lênpic": "topic",
    "lêntal": "total",
    "Lêntal": "Total",
    "seleclênr": "selector",
    "Seleclênr": "Selector",
    "agenlênps": "agentops",
    "Agenlênps": "Agentops",
    "reposilênry": "repository",
    "Reposilênry": "Repository",
    "execulênr": "executor",
    "Execulênr": "Executor",
    "generalênr": "generator",
    "Generalênr": "Generator",
    "operalênr": "operator",
    "Operalênr": "Operator",
    "aggregalênr": "aggregator",
    "Aggregalênr": "Aggregator",
    "monolênnic": "monotonic",
    "Monolênnic": "Monotonic",
    "lênm-tat": "tom-tat",
    "lênng-hop": "tong-hop",
    "lênm_tat": "tom_tat",
    "lênng_hop": "tong_hop",
    "lên_thread": "to_thread",
    "lên_list": "to_list",
    "lên_dict": "to_dict",
    "lên_json": "to_json",
    "lênp_": "top_",
    "Lênp_": "Top_",
    "_lên_": "_to_",
    "slênp": "stop",
    "Slênp": "Stop",
    "aulêncomplete": "autocomplete",
    "transform_lênne": "transform_tone"
}

total_files_modified = 0

for d in target_dirs:
    for root, dirs, files in os.walk(d):
        if 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                new_content = content
                for k, v in replacements.items():
                    new_content = new_content.replace(k, v)
                
                if new_content != content:
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    total_files_modified += 1

print(f"ULTIMATE fixed lên corruptions in {total_files_modified} files.")
