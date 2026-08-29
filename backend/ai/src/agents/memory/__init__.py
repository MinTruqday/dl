from importlib import import_module

_EXPORTS = {
    "ShortTermMemory": ("src.agents.memory.short_term", "ShortTermMemory"),
    "short_term_memory": ("src.agents.memory.short_term", "short_term_memory"),
    "LongTermMemory": ("src.agents.memory.long_term", "LongTermMemory"),
    "long_term_memory": ("src.agents.memory.long_term", "long_term_memory"),
    "MemoryManager": ("src.agents.memory.management", "MemoryManager"),
    "memory_manager": ("src.agents.memory.management", "memory_manager"),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attribute_name = _EXPORTS[name]
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
