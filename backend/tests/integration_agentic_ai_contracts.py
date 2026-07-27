import ast
import asyncio
import io
import json
import string
import tokenize
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.agents.planning import PlanAgent
from src.agents.routing import RouteAgent, SemanticRouterValidator
from src.core.logging_route import summarize_payload
from src.core.model_runtime import run_chat_completion
from src.core.registry import PromptType, RegistryCore, registry
from src.schemas.inference import StyleImitationRequest
from src.workflow.orchestration import execute_tool_node, sanitizer_node, supervisor


ROOT = Path("/app")
SOURCE = ROOT / "src"


class FlakyClient:
    def __init__(self):
        self.calls = 0

    async def chat_completion(self, **kwargs):
        self.calls += 1
        if self.calls < 3:
            raise TimeoutError("temporary")
        message = SimpleNamespace(content="Hoàn tất")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakePlanModel:
    async def ainvoke(self, messages):
        content = '<think>private chain</think>{"nodes":[{"id":"one","agent":"Knowledge","task":"Retrieve relevant documents","dependencies":[]}]}'
        return SimpleNamespace(content=content)


class FakeEvaluationModel:
    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, prompt):
        return SimpleNamespace(status="PASS", feedback="", revised_task="")


class FakeActionTool:
    async def execute(self, action, params, user_id, token, auto_approve=False):
        assert auto_approve is True
        return "Action completed"


async def verify_runtime():
    client = FlakyClient()
    with patch("src.core.model_runtime.asyncio.sleep", return_value=None):
        result = await run_chat_completion(
            client=client,
            messages=[{"role": "user", "content": "secret body"}],
            model="test",
            max_tokens=32,
            temperature=0,
            timeout_seconds=1,
        )
    assert result == "Hoàn tất"
    assert client.calls == 3


async def verify_planner_privacy():
    planner = PlanAgent.__new__(PlanAgent)
    planner.llm = FakePlanModel()
    from langchain_core.output_parsers import JsonOutputParser
    from src.schemas.planning import ExecutionPlan
    planner.parser = JsonOutputParser(pydantic_object=ExecutionPlan)
    planner._redis = None
    with (
        patch("src.agents.planning.memo_manager.get_memories", return_value=""),
        patch.object(planner, "_invoke_llm", side_effect=planner.llm.ainvoke),
    ):
        events = [
            event
            async for event in planner.stream_plan(
                {"query": "test", "user_id": "user", "conversation_history": []}
            )
        ]
    assert [event["type"] for event in events] == ["plan"]
    assert "private chain" not in json.dumps(events)


async def verify_routing():
    greeting = await RouteAgent().execute("hello")
    assert greeting["answer"].startswith("Chào bạn")
    validator = SemanticRouterValidator()
    nodes = [{"id": "one", "agent": "InterpreterAgent", "task": "calculate"}]
    result = await validator.validate_plan(nodes)
    assert result[0]["agent"] == "Reasoning"


async def verify_action_workflow():
    state = {
        "steps": [
            {
                "id": "action-one",
                "agent": "Action",
                "task": "Read a document",
                "dependencies": [],
            }
        ],
        "task_status": {"action-one": "running"},
        "completed_tasks": [],
        "req_data": {
            "user_id": "user",
            "token": "token",
            "approve_tools": True,
        },
    }
    with patch("src.workflow.graph.llm", FakeEvaluationModel()):
        result = await execute_tool_node(state, FakeActionTool(), "Action")
    assert result["task_status"]["action-one"] == "completed"
    assert result["last_agent_result"] == "Action completed"
    interrupt_nodes = getattr(supervisor.app, "interrupt_before_nodes", [])
    assert "action" not in interrupt_nodes


async def verify_trimmed_results():
    result = await sanitizer_node(
        {
            "consolidated_results": ["old" * 20000, "trimmed result"],
            "results_trimmed": True,
        }
    )
    assert result["consolidated_results"] == ["trimmed result"]


def verify_registry():
    enum_members = set(PromptType)
    prompt_members = set(RegistryCore._prompts)
    assert enum_members == prompt_members
    assert registry.get(PromptType.QUICK_REPLIES)
    assert registry.get(PromptType.PROMPT_INJECTION_DETECTOR)
    assert "flawless" not in registry.get(PromptType.CHAT_ASSISTANT).lower()
    assert "never add a period" not in registry.get(PromptType.GRAMMAR_CHECK).lower()
    brain_prompt = registry.get(PromptType.BRAIN_SYSTEM)
    assert '"nodes"' in brain_prompt
    assert '"steps" array' not in brain_prompt
    assert "InterpreterAgent" not in brain_prompt
    for prompt_type, prompt in RegistryCore._prompts.items():
        if prompt_type is PromptType.MEMORY_BANK_PHASE1:
            continue
        fields = [
            field_name
            for _, field_name, _, _ in string.Formatter().parse(prompt)
            if field_name
        ]
        assert not any(
            field_name.startswith('"')
            or field_name.startswith("{")
            or "\n" in field_name
            for field_name in fields
        )
    style_request = StyleImitationRequest(
        text="Target",
        style_sample="Reference",
        target_length=100,
    )
    assert style_request.style_sample == "Reference"


def verify_logging():
    body = json.dumps(
        {"query": "private", "password": "hidden", "nested": {"token": "hidden"}}
    ).encode()
    summary = summarize_payload(body)
    rendered = json.dumps(summary)
    assert "private" not in rendered
    assert "hidden" not in rendered
    assert "password" not in rendered
    assert "[sensitive]" in rendered


def verify_source_contracts():
    for path in SOURCE.rglob("*.py"):
        text = path.read_text()
        compile(text, str(path), "exec")
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        assert not any(token.type == tokenize.COMMENT for token in tokens), path
        tree = ast.parse(text)
        invalid_strings = [
            node
            for token in ast.walk(tree)
            for node in [token]
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and (
                "\u2026" in node.value
                or "..." in node.value
                or any(ord(char) >= 0x1F000 for char in node.value)
            )
        ]
        assert not invalid_strings, path


async def main():
    verify_registry()
    verify_logging()
    verify_source_contracts()
    await verify_runtime()
    await verify_planner_privacy()
    await verify_routing()
    await verify_action_workflow()
    await verify_trimmed_results()
    print("agentic ai contracts passed")


asyncio.run(main())
