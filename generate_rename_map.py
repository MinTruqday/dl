import json
import os
import re

SERVICE_MAP = {
    "agentic_ai": "intelligence",
    "authentication": "identity",
    "collector": "ingestion",
    "content": "documents",
    "editor": "workspace",
    "finance": "billing",
    "management": "administration",
    "messaging": "conversations",
    "notification": "alerts",
    "realtime": "live_events",
    "worker": "task_queue",
    "core": "shared",
    "tests": "tests",
    "logs": "logs"
}

# A dictionary to replace specific words to noun/resource format
WORD_MAP = {
    "login": "sessions",
    "authentication": "auth",
    "delivery": "dispatch",
    "collection": "ingestion",
    "operations": "ops",
    "drafts": "drafts",
    "export": "exports",
    "pinning": "pins",
    "upload": "uploads",
    "process": "workflows",
    "progress": "progress",
    "editing": "edit_sessions",
    "monetization": "monetization",
    "deposit": "deposits",
    "withdrawal": "withdrawals",
    "purchase": "purchases",
    "profile": "profiles",
    "logs": "audit_logs",
    "banner": "banners",
    "health": "health",
    "telemetry": "telemetry",
    "quota": "quotas",
    "conversation": "threads",
    "sync": "sync_state",
    "finetuning": "finetuning_jobs",
    "inference": "inference",
    "interaction": "interactions",
    "planning": "plans",
    "execution": "sandboxes",
    "reasoning": "reasoning",
    "generation": "responses",
    "search": "search",
    "engine": "engines",
    "parsing": "parsers", # wait, parser is agent noun. -> parsed_data? let's stick to parsers or parsings
    "chunking": "chunks",
    "embedding": "embeddings",
    "retrieval": "retrieval",
    "database": "database",
    "tools": "tools",
    "evaluation": "evaluations",
    "resilience": "resilience",
    "model": "models",
    "translation": "translations",
    "graph": "graphs",
    "state": "states",
    "orchestration": "orchestrators",
    "management": "mgmt",
    "history": "histories",
    "feedback": "feedback",
    "task": "tasks"
}

def clean_filename(filename, service_new_name):
    # Strip .py
    base = filename[:-3]
    if base == "__init__" or base == "main":
        return filename
        
    parts = base.split('_')
    
    new_parts = []
    for p in parts:
        # Remove stuttering (e.g. document_metadata in documents -> metadata)
        if p == 'document' and service_new_name in ('documents', 'workspace'):
            continue
        if p == 'system' and service_new_name == 'administration':
            continue
        if p == 'user' and service_new_name in ('identity', 'administration'):
            continue
        if p == 'fiat' and service_new_name == 'billing':
            continue
            
        new_parts.append(WORD_MAP.get(p, p))
        
    if not new_parts:
        new_parts = [base] # Fallback
        
    new_name = "_".join(new_parts) + ".py"
    return new_name

def main():
    with open('backend_py_files.txt', 'r') as f:
        files = [line.strip() for line in f if line.strip()]

    rename_map = {}
    
    for old_path in files:
        parts = old_path.split('/')
        if parts[0] != 'backend':
            continue
            
        old_service = parts[1]
        new_service = SERVICE_MAP.get(old_service, old_service)
        
        # New parts
        new_parts = list(parts)
        new_parts[1] = new_service
        
        # Rename filename
        filename = parts[-1]
        new_filename = clean_filename(filename, new_service)
        new_parts[-1] = new_filename
        
        new_path = "/".join(new_parts)
        rename_map[old_path] = new_path
        
    # Add directory renames for root services
    dir_map = {}
    for old, new in SERVICE_MAP.items():
        if old != new:
            dir_map[f"backend/{old}"] = f"backend/{new}"
            
    output = {
        "directories": dir_map,
        "files": rename_map
    }
    
    with open('rename_map.json', 'w') as f:
        json.dump(output, f, indent=4)
        
    print("Generated rename_map.json")

if __name__ == "__main__":
    main()
