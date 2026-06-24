import os

files_to_patch = [
    "backend/collection/src/services/ingestion.py",
    "backend/agentic_ai/src/rag/pipeline.py",
    "backend/agentic_ai/src/harness/agentops.py",
    "backend/agentic_ai/src/api/feedback.py",
    "backend/agentic_ai/src/api/history.py",
    "backend/agentic_ai/src/main.py",
    "backend/agentic_ai/src/services/finetuning.py"
]

for fpath in files_to_patch:
    if os.path.exists(fpath):
        with open(fpath, "r") as f:
            content = f.read()
        
        # collection has db_client in src.core, agentic_ai in src.core.infrastructure
        if "agentic_ai" in fpath:
            import_str = "from src.core.infrastructure.db_client import ClientProxy as AsyncIOMotorClient"
        else:
            import_str = "from src.core.db_client import ClientProxy as AsyncIOMotorClient"
            
        content = content.replace("from motor.motor_asyncio import AsyncIOMotorClient", import_str)
        
        with open(fpath, "w") as f:
            f.write(content)
        print(f"Patched {fpath}")
