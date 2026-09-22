from dataclasses import dataclass

from src.core.infrastructure.configuration import settings


@dataclass(frozen=True)
class RuntimeLimits:
    supervisor_steps: int
    specialist_steps: int
    tool_calls_per_task: int
    tool_errors: int
    retries: int
    run_timeout_seconds: int
    task_timeout_seconds: int
    evidence_items: int


limits = RuntimeLimits(
    supervisor_steps=settings.AGENT_MAX_SUPERVISOR_STEPS,
    specialist_steps=settings.AGENT_MAX_SPECIALIST_STEPS,
    tool_calls_per_task=settings.AGENT_MAX_TOOL_CALLS_PER_TASK,
    tool_errors=settings.AGENT_MAX_TOOL_ERRORS,
    retries=settings.AGENT_MAX_RETRIES,
    run_timeout_seconds=settings.AGENT_EXECUTION_TIMEOUT_SECONDS,
    task_timeout_seconds=settings.AGENT_TASK_TIMEOUT_SECONDS,
    evidence_items=settings.AGENT_MAX_EVIDENCE_ITEMS,
)
