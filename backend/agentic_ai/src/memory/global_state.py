import json
import os
from typing import Dict, Any
from loguru import logger

class GlobalStateManager:
    """
    <module_purpose>
    <purpose>Manages persistent global memory across sessions for Metis.</purpose>
    <metis_behavior>Stores state mutely. Never exposes the underlying JSON file to users or mentions memory structures directly.</metis_behavior>
    </module_purpose>
    """
    def __init__(self, storage_path: str = ".agentic_global_state.json"):
        self.storage_path = storage_path
        self._state = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.exception("State restoration execution failed")
        return {"preferences": {}, "project_context": {}, "history": []}

    def _save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
        except Exception as e:
            logger.exception("State persistence execution failed")

    def update_preference(self, key: str, value: Any):
        self._state["preferences"][key] = value
        self._save()
        logger.info("Global preference synchronization completed successfully")

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self._state["preferences"].get(key, default)

    def update_project_context(self, project_id: str, context: Dict[str, Any]):
        if project_id not in self._state["project_context"]:
            self._state["project_context"][project_id] = {}
        self._state["project_context"][project_id].update(context)
        self._save()
        logger.info("Project context synchronization completed successfully")
        
    def get_project_context(self, project_id: str) -> Dict[str, Any]:
        return self._state["project_context"].get(project_id, {})

    def add_history_event(self, event: str):
        self._state["history"].append(event)
        if len(self._state["history"]) > 1000:
            self._state["history"] = self._state["history"][-1000:]
        self._save()

global_state = GlobalStateManager()
