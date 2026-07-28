from importlib import import_module


_EXPORTS = {
    "knowledge_app": ("src.workflow.graph", "knowledge_app"),
    "AgentState": ("src.workflow.state", "AgentState"),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attribute_name = _EXPORTS[name]
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
