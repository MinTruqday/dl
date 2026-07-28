from importlib import import_module


_EXPORTS = {
    "MemoryBank": ("src.proactive.bank", "MemoryBank"),
    "MemoryEntry": ("src.proactive.bank", "MemoryEntry"),
    "ProactiveMemoryBank": ("src.proactive.bank", "ProactiveMemoryBank"),
    "proactive_memory_bank": ("src.proactive.bank", "proactive_memory_bank"),
    "ProactiveMemoryAgent": ("src.proactive.agent", "ProactiveMemoryAgent"),
    "proactive_memory_agent": ("src.proactive.agent", "proactive_memory_agent"),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attribute_name = _EXPORTS[name]
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
