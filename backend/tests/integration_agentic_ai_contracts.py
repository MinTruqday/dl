import ast
import asyncio
import json
import string
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from src.agents.react.planning import PlanAgent
from src.agents.react.routing import RouteAgent, SemanticRouterValidator
from src.core.model_runtime import run_chat_completion
from src.core.infrastructure.configuration import settings
from src.core.registry import PromptType, RegistryCore, registry
from src.harness.failure import failure
from src.schemas.inference import StyleImitationRequest
from src.workflow.orchestration import execute_tool_node, sanitizer_node, supervisor
from src.utils.local_models import LocalModelClient


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
        from src.schemas.planning import ExecutionPlan, PlanNode

        return ExecutionPlan(
            reasoning="Knowledge retrieval is required",
            nodes=[
                PlanNode(
                    id="one", agent="Knowledge", task="Retrieve relevant documents", dependencies=[]
                )
            ],
        )


class FakeEvaluationModel:
    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, prompt):
        return SimpleNamespace(status="PASS", feedback="", revised_task="")


class FakeActionTool:
    async def execute(
        self,
        action,
        params,
        user_id,
        token,
        auto_approve=False,
        approval_policy="manual",
        session_id="",
        approval_id=None,
    ):
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

    routed_client = LocalModelClient()
    model_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Configured model"))]
    )
    routed_client._primary_completion = AsyncMock(return_value=model_response)
    routed = await routed_client.chat_completion(
        messages=[{"role": "user", "content": "route"}],
        model=settings.LLM_MODEL,
        max_tokens=16,
        temperature=0,
    )
    assert routed.choices[0].message.content == "Configured model"
    routed_client._primary_completion.assert_awaited_once()


async def verify_planner_privacy():
    planner = PlanAgent.__new__(PlanAgent)
    planner.llm = FakePlanModel()
    from langchain_core.output_parsers import JsonOutputParser
    from src.schemas.planning import ExecutionPlan

    planner.parser = JsonOutputParser(pydantic_object=ExecutionPlan)
    planner.structured_llm = FakePlanModel()
    planner._redis = None
    with patch("src.agents.react.planning.memory_manager.get_memories", return_value=""):
        events = [
            event
            async for event in planner.stream_plan(
                {"query": "test", "user_id": "user", "conversation_history": []}
            )
        ]
    assert [event["type"] for event in events] == ["plan"]
    assert "private chain" not in json.dumps(events)

    class FailingPlanModel:
        async def ainvoke(self, messages):
            raise ValueError("invalid structured output")

    planner.structured_llm = FailingPlanModel()
    with patch("src.agents.react.planning.memory_manager.get_memories", return_value=""):
        failed_events = [
            event
            async for event in planner.stream_plan(
                {"query": "test", "user_id": "user", "conversation_history": []}
            )
        ]
    assert failed_events == [{"type": "error", "code": "planning_model_failed"}]

    from pydantic import ValidationError
    from src.schemas.planning import ExecutionPlan, PlanNode

    try:
        ExecutionPlan(
            reasoning="Invalid dependency order",
            nodes=[
                PlanNode(
                    id="one", agent="Knowledge", task="Retrieve documents", dependencies=["two"]
                )
            ],
        )
        raise AssertionError("Invalid plan dependency was accepted")
    except ValidationError:
        pass


async def verify_routing():
    class FakeEmbedder:
        async def embed_query(self, text):
            lowered = text.lower()
            if "chat" in lowered or "greeting" in lowered or "hello" in lowered:
                return [1.0, 0.0]
            return [0.0, 1.0]

    router = RouteAgent()
    router._get_embedder = lambda: FakeEmbedder()
    greeting = await router.execute("hello")
    assert greeting == {"route": "chat", "answer": ""}
    validator = SemanticRouterValidator()
    nodes = [{"id": "one", "agent": "InterpreterAgent", "task": "calculate"}]
    result = await validator.validate_plan(nodes)
    assert result[0]["agent"] == "InterpreterAgent"


async def verify_action_workflow():
    state = {
        "steps": [
            {"id": "action-one", "agent": "Action", "task": "Read a document", "dependencies": []}
        ],
        "task_status": {"action-one": "running"},
        "completed_tasks": [],
        "req_data": {"user_id": "user", "token": "token", "approve_tools": True},
    }
    with patch("src.workflow.graph.llm", FakeEvaluationModel()):
        result = await execute_tool_node(state, FakeActionTool(), "Action")
    assert result["task_status"]["action-one"] == "completed"
    assert result["last_agent_result"] == "Action completed"
    interrupt_nodes = getattr(supervisor.app, "interrupt_before_nodes", [])
    assert "action" not in interrupt_nodes


async def verify_trimmed_results():
    result = await sanitizer_node(
        {"consolidated_results": ["old" * 20000, "trimmed result"], "results_trimmed": True}
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
        fields = [
            field_name for _, field_name, _, _ in string.Formatter().parse(prompt) if field_name
        ]
        assert not any(
            field_name.startswith('"') or field_name.startswith("{") or "\n" in field_name
            for field_name in fields
        )
    style_request = StyleImitationRequest(
        text="Target", style_sample="Reference", target_length=100
    )
    assert style_request.style_sample == "Reference"


def verify_source_contracts():
    for path in SOURCE.rglob("*.py"):
        text = path.read_text()
        compile(text, str(path), "exec")
        tree = ast.parse(text)
        invalid_strings = [
            node
            for token in ast.walk(tree)
            for node in [token]
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and (
                chr(0x2026) in node.value
                or "." * 3 in node.value
                or any(ord(char) >= 0x1F000 for char in node.value)
            )
        ]
        assert not invalid_strings, path
        lowered_source = text.casefold()
        assert "qwen" not in lowered_source, path

    interaction_source = "\n".join(
        path.read_text() for path in (SOURCE / "api" / "interaction").glob("*.py")
    )
    assert "public_agent_names" not in interaction_source
    assert '"label"' not in interaction_source
    assert "event: error" in interaction_source
    assert interaction_source.count('yield "event: done\\ndata: [DONE]\\n\\n"') >= 5
    assert '"prompt_injection_blocked"' in interaction_source
    assert '"pii_redacted"' in interaction_source
    assert "session_id=session_id" in interaction_source

    security_source = (SOURCE / "harness" / "security.py").read_text()
    assert "review_markers" not in security_source
    assert "suspicious_markers" in security_source
    assert "requires_ai_review = category != \"none\"" in security_source
    assert '("credential_leak", "prompt_injection")' in security_source

    workspace_source = (SOURCE / "services" / "workspace.py").read_text()
    assert not any("À" <= character <= "ỹ" for character in workspace_source)
    tools_source = (SOURCE / "tools" / "__init__.py").read_text()
    assert "execute_mcp_tool" in tools_source
async def main():
    verify_registry()
    verify_source_contracts()
    await verify_runtime()
    await verify_planner_privacy()
    await verify_routing()
    await verify_action_workflow()
    await verify_trimmed_results()
    print("agentic ai contracts passed")


asyncio.run(main())
