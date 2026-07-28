from importlib import import_module


_EXPORTS = {
    "agentops": ("src.harness.agentops", "agentops"),
    "context": ("src.harness.context", "context"),
    "entropy": ("src.harness.entropy", "entropy"),
    "evaluation": ("src.loop.evaluation", "evaluation"),
    "failure": ("src.harness.failure", "failure"),
    "governance": ("src.harness.governance", "governance"),
    "intervention": ("src.loop.intervention", "intervention"),
    "orchestration": ("src.harness.orchestration", "orchestration"),
    "security": ("src.harness.security", "security"),
    "tool": ("src.harness.tool", "tool"),
    "verification": ("src.loop.verification", "verification"),
    "RubricMiddleware": ("src.loop.rubric", "RubricMiddleware"),
    "standard_rubric_middleware": (
        "src.loop.rubric",
        "standard_rubric_middleware",
    ),
    "document_rubric_middleware": (
        "src.loop.rubric",
        "document_rubric_middleware",
    ),
    "financial_rubric_middleware": (
        "src.loop.rubric",
        "financial_rubric_middleware",
    ),
    "create_standard_rubric": ("src.loop.rubric", "create_standard_rubric"),
    "create_document_rubric": ("src.loop.rubric", "create_document_rubric"),
    "create_financial_rubric": ("src.loop.rubric", "create_financial_rubric"),
    "event_driven_loop": ("src.loop.event", "event_driven_loop"),
    "cron_scheduler": ("src.loop.event", "cron_scheduler"),
    "EventType": ("src.loop.event", "EventType"),
    "AgentEvent": ("src.loop.event", "AgentEvent"),
    "CronSchedule": ("src.loop.event", "CronSchedule"),
    "hill_climbing_loop": ("src.loop.hill_climbing", "hill_climbing_loop"),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attribute_name = _EXPORTS[name]
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
