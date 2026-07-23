import json
from typing import Any, Callable, Dict, List, Optional
from loguru import logger

class DynamicToolRegistry:
    def __init__(self):
        self._registered_tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        parameters_schema: Dict[str, Any],
        handler: Callable[..., Any]
    ) -> bool:
        if not name or not handler:
            return False

        tool_info = {
            "name": name,
            "description": description,
            "schema": parameters_schema,
            "handler": handler
        }
        self._registered_tools[name] = tool_info
        logger.info(f"Registered dynamic OpenAPI tool: {name}")
        return True

    def register_from_openapi_spec(self, openapi_json: str, handler_factory: Callable[[str, str], Callable]) -> int:
        try:
            spec = json.loads(openapi_json)
            paths = spec.get("paths", {})
            count = 0
            for path_key, path_item in paths.items():
                for method, operation in path_item.items():
                    if method.lower() in ["get", "post", "put", "delete"]:
                        operation_id = operation.get("operationId") or f"{method}_{path_key.replace('/', '_')}"
                        summary = operation.get("summary") or operation.get("description") or f"API endpoint {method.upper()} {path_key}"
                        params_schema = operation.get("parameters", [])
                        handler = handler_factory(method, path_key)
                        self.register_tool(operation_id, summary, {"parameters": params_schema}, handler)
                        count += 1
            return count
        except Exception as err:
            logger.exception("Failed to parse OpenAPI spec for dynamic tool discovery")
            return 0

    def register_openapi_spec(self, name: str, spec: Dict[str, Any]) -> List[str]:
        json_str = json.dumps(spec) if isinstance(spec, dict) else str(spec)
        def dummy_factory(m, p):
            return lambda **k: "ok"
        count = self.register_from_openapi_spec(json_str, dummy_factory)
        return list(self._registered_tools.keys())

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        return self._registered_tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        result = []
        for name, info in self._registered_tools.items():
            result.append({
                "name": name,
                "description": info["description"],
                "schema": info["schema"]
            })
        return result

    async def execute_tool(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        tool = self.get_tool(name)
        if not tool:
            return {"success": False, "error": f"Dynamic tool '{name}' not found"}

        handler = tool["handler"]
        try:
            import asyncio
            if asyncio.iscoroutinefunction(handler):
                res = await handler(**kwargs)
            else:
                res = handler(**kwargs)
            return {"success": True, "result": res}
        except Exception as err:
            logger.exception(f"Error executing dynamic tool '{name}'")
            return {"success": False, "error": str(err)}

dynamic_tool_registry = DynamicToolRegistry()
