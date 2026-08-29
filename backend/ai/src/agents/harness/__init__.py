from importlib import import_module


_EXPORTS = {
    "agentops": ("src.agents.harness.agentops", "agentops"),
    "context": ("src.agents.harness.context", "context"),
    "entropy": ("src.agents.harness.entropy", "entropy"),
    "evaluation": ("src.agents.loop.evaluation", "evaluation"),
    "failure": ("src.agents.harness.failure", "failure"),
    "governance": ("src.agents.harness.governance", "governance"),
    "intervention": ("src.agents.loop.intervention", "intervention"),
    "orchestration": ("src.agents.harness.orchestration", "orchestration"),
    "security": ("src.agents.harness.security", "security"),
    "tool": ("src.agents.harness.tool", "tool"),
    "verification": ("src.agents.loop.verification", "verification"),
    "RubricMiddleware": ("src.agents.loop.rubric", "RubricMiddleware"),
    "standard_rubric_middleware": ("src.agents.loop.rubric", "standard_rubric_middleware"),
    "document_rubric_middleware": ("src.agents.loop.rubric", "document_rubric_middleware"),
    "create_standard_rubric": ("src.agents.loop.rubric", "create_standard_rubric"),
    "create_document_rubric": ("src.agents.loop.rubric", "create_document_rubric"),
    "event_driven_loop": ("src.agents.loop.event", "event_driven_loop"),
    "cron_scheduler": ("src.agents.loop.event", "cron_scheduler"),
    "EventType": ("src.agents.loop.event", "EventType"),
    "AgentEvent": ("src.agents.loop.event", "AgentEvent"),
    "CronSchedule": ("src.agents.loop.event", "CronSchedule"),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attribute_name = _EXPORTS[name]
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
