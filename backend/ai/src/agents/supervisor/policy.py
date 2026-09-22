import json
from functools import lru_cache
from pathlib import Path

from src.runtime.limits import limits
from src.runtime.models import AgentTask, PlannedTask, ToolCall
from src.tools.registry import policies, registered_tools


def available_tools(permissions, intent="", compact=False):
    values = []
    tools = registered_tools()
    allowed_specialists = set(routing_policies().get(intent, {}).get("specialists", []))
    for policy in policies().values():
        tool = tools.get(policy.name)
        if (
            policy.permission in permissions
            and tool
            and (
                not allowed_specialists
                or bool(policy.specialists.intersection(allowed_specialists))
            )
        ):
            schema = tool.args_schema.model_json_schema()
            arguments = schema
            if compact:
                arguments = {
                    "required": schema.get("required", []),
                    "properties": {
                        key: {
                            attribute: value
                            for attribute, value in specification.items()
                            if attribute in {"type", "enum", "minimum", "maximum"}
                        }
                        for key, specification in schema.get("properties", {}).items()
                    },
                }
            values.append(
                {
                    "name": policy.name,
                    "specialists": sorted(policy.specialists),
                    "action": policy.action,
                    "requires_approval": policy.requires_approval,
                    "arguments": arguments,
                }
            )
    return values


@lru_cache(maxsize=1)
def routing_policies():
    path = Path(__file__).with_name("routing_policy.json")
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def bounded_tasks(tasks, run):
    policy = routing_policies().get(run.intent, {})
    maximum = min(policy.get("maximum_tasks", limits.supervisor_steps), limits.supervisor_steps)
    specialists = set(policy.get("specialists", []))
    return [
        task
        for task in tasks
        if not specialists
        or (task.specialist if isinstance(task, PlannedTask) else task.get("specialist"))
        in specialists
    ][:maximum]


def fallback_tasks(run, evidence_refs, constraints):
    value = routing_policies().get(run.intent, {}).get("fallback")
    if not value:
        return []
    replacements = {
        "$project_id": run.project_id,
        "$objective": run.objective,
    }
    arguments = {
        key: replacements.get(item, item) for key, item in value.get("arguments", {}).items()
    }
    return [
        PlannedTask(
            specialist=value["specialist"],
            objective=run.objective,
            evidence_refs=evidence_refs,
            constraints=constraints,
            tool_calls=[ToolCall(tool_name=value["tool_name"], arguments=arguments)],
        )
    ]


def validated_tasks(tasks, run, evidence_refs, maximum=None, known_identifiers=None):
    tool_values = registered_tools()
    policy_values = policies()
    validated = []
    intent_policy = routing_policies().get(run.intent, {})
    task_limit = max(
        0,
        intent_policy.get("maximum_tasks", limits.supervisor_steps)
        - len(run.completed_tasks),
    )
    if maximum is not None:
        task_limit = min(task_limit, maximum)
    for planned in bounded_tasks(tasks, run)[:task_limit]:
        task = planned if isinstance(planned, PlannedTask) else PlannedTask(**planned)
        calls = []
        for call in task.tool_calls[: limits.tool_calls_per_task]:
            policy = policy_values.get(call.tool_name)
            tool = tool_values.get(call.tool_name)
            if not policy or not tool or task.specialist not in policy.specialists:
                continue
            arguments = dict(call.arguments)
            schema = tool.args_schema.model_json_schema()
            properties = schema.get("properties", {})
            if "project_id" in properties:
                arguments["project_id"] = run.project_id
            identifiers = {
                str(value)
                for key, value in arguments.items()
                if key != "project_id" and key.endswith("_id") and value
            }
            if identifiers.difference(set(known_identifiers or evidence_refs)):
                continue
            required = set(schema.get("required", []))
            if required.difference(arguments):
                continue
            try:
                normalized = tool.args_schema.model_validate(arguments).model_dump(
                    mode="python", exclude_unset=True
                )
            except Exception:
                continue
            calls.append(ToolCall(tool_name=call.tool_name, arguments=normalized))
        validated.append(
            AgentTask(
                run_id=run.run_id,
                project_id=run.project_id,
                specialist=task.specialist,
                objective=task.objective,
                evidence_refs=task.evidence_refs or evidence_refs,
                constraints=task.constraints,
                tool_calls=calls,
            )
        )
    return validated
