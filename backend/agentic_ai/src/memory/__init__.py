from importlib import import_module

_EXPORTS = {
    "MemoryBank": ("src.proactive.bank", "MemoryBank"),
    "MemoryEntry": ("src.proactive.bank", "MemoryEntry"),
    "ProactiveMemoryBank": ("src.proactive.bank", "ProactiveMemoryBank"),
    "proactive_memory_bank": ("src.proactive.bank", "proactive_memory_bank"),
    "ProactiveMemoryAgent": ("src.proactive.agent", "ProactiveMemoryAgent"),
    "proactive_memory_agent": ("src.proactive.agent", "proactive_memory_agent"),
    "ShortTermMemory": ("src.memory.short_term", "ShortTermMemory"),
    "short_term_memory": ("src.memory.short_term", "short_term_memory"),
    "LongTermMemory": ("src.memory.long_term", "LongTermMemory"),
    "long_term_memory": ("src.memory.long_term", "long_term_memory"),
    "EntityStore": ("src.memory.long_term", "EntityStore"),
    "ProjectStore": ("src.memory.long_term", "ProjectStore"),
    "MemoryManager": ("src.memory.management", "MemoryManager"),
    "memory_manager": ("src.memory.management", "memory_manager"),
    "SemanticCache": ("src.memory.semantic_cache", "SemanticCache"),
    "semantic_cache": ("src.memory.semantic_cache", "semantic_cache"),
}

__all__ = list(_EXPORTS)

def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attribute_name = _EXPORTS[name]
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
