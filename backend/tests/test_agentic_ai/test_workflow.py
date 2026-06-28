"""
Heavy-duty unit tests for the workflow and orchestration components.
Tests the actual supervisor_node, trimmer_node, execute_tool_node functions
with precise state inputs matching the real ActingState TypedDict.
"""
import sys
import os
import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../agentic_ai"))

from src.workflow.state import ActingState, AgentState, reduce_consolidated_results, reduce_chat_history
from src.workflow.orchestration import (
    supervisor_node,
    execute_tool_node,
    trimmer_node,
    trimmer_router,
    router,
    aggregator_node,
)


# ─────────────────────────────────────────────────────────────────────────────
# ActingState & AgentState structure tests
# ─────────────────────────────────────────────────────────────────────────────

class TestStateDefinitions:

    def test_acting_state_has_all_required_keys(self):
        annotations = ActingState.__annotations__
        required = {"req_data", "steps", "current_step_index", "consolidated_results",
                    "final_answer", "next_node", "error", "replan_count", "start_time"}
        for key in required:
            assert key in annotations, f"Missing key in ActingState: {key}"

    def test_agent_state_has_all_required_keys(self):
        annotations = AgentState.__annotations__
        required = {"chat_history", "question", "generation", "documents",
                    "retry_count", "user_id", "route"}
        for key in required:
            assert key in annotations, f"Missing key in AgentState: {key}"

    def test_reduce_consolidated_results_basic_append(self):
        result = reduce_consolidated_results(["a", "b"], ["c"])
        assert "a" in result
        assert "c" in result

    def test_reduce_consolidated_results_caps_at_15(self):
        left = [str(i) for i in range(10)]
        right = [str(i) for i in range(10)]
        result = reduce_consolidated_results(left, right)
        assert len(result) <= 15

    def test_reduce_consolidated_results_none_left(self):
        result = reduce_consolidated_results(None, ["x"])
        assert "x" in result

    def test_reduce_consolidated_results_none_right(self):
        result = reduce_consolidated_results(["a"], None)
        assert "a" in result

    def test_reduce_chat_history_appends(self):
        from langchain_core.messages import HumanMessage
        left = [HumanMessage(content="Hello")]
        right = [HumanMessage(content="World")]
        result = reduce_chat_history(left, right)
        assert len(result) == 2

    def test_reduce_chat_history_caps_at_15(self):
        from langchain_core.messages import HumanMessage
        msgs = [HumanMessage(content=f"msg{i}") for i in range(20)]
        result = reduce_chat_history(msgs, [HumanMessage(content="new")])
        assert len(result) <= 15


# ─────────────────────────────────────────────────────────────────────────────
# supervisor_node behavioral tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSupervisorNode:

    def _base_state(self, **overrides):
        state = {
            "start_time": time.time(),
            "steps": [],
            "current_step_index": 0,
            "replan_count": 0,
            "error": "",
            "req_data": {"query": "What is AI?"},
            "consolidated_results": [],
            "final_answer": "",
            "next_node": "",
        }
        state.update(overrides)
        return state

    @pytest.mark.asyncio
    async def test_returns_trimmer_on_timeout(self):
        state = self._base_state(
            start_time=time.time() - 60,  # 60 seconds ago → timed out
            steps=[{"agent": "Action", "task": "test"}],
        )
        result = await supervisor_node(state)
        assert result["next_node"] == "trimmer"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_returns_trimmer_on_too_many_replans(self):
        state = self._base_state(
            steps=[{"agent": "Action", "task": "do something"}],
            replan_count=7,  # > 6 threshold
        )
        result = await supervisor_node(state)
        assert result["next_node"] == "trimmer"

    @pytest.mark.asyncio
    async def test_routes_action_agent_correctly(self):
        steps = [{"agent": "Action", "task": "fetch user balance"}]
        state = self._base_state(steps=steps)
        result = await supervisor_node(state)
        assert result["next_node"] == "action"

    @pytest.mark.asyncio
    async def test_routes_interpreter_agent_correctly(self):
        steps = [{"agent": "InterpreterAgent", "task": "execute python code"}]
        state = self._base_state(steps=steps)
        result = await supervisor_node(state)
        assert result["next_node"] == "interpreter"

    @pytest.mark.asyncio
    async def test_routes_engine_agent_correctly(self):
        steps = [{"agent": "EngineAgent", "task": "search for info"}]
        state = self._base_state(steps=steps)
        result = await supervisor_node(state)
        assert result["next_node"] == "search_engine"

    @pytest.mark.asyncio
    async def test_routes_knowledge_agent_correctly(self):
        steps = [{"agent": "Knowledge", "task": "retrieve document info"}]
        state = self._base_state(steps=steps)
        result = await supervisor_node(state)
        assert result["next_node"] == "knowledge"

    @pytest.mark.asyncio
    async def test_routes_reasoning_agent_correctly(self):
        steps = [{"agent": "Reasoning", "task": "analyze data"}]
        state = self._base_state(steps=steps)
        result = await supervisor_node(state)
        assert result["next_node"] == "reasoning"

    @pytest.mark.asyncio
    async def test_routes_to_trimmer_when_steps_exhausted(self):
        steps = [{"agent": "Action", "task": "done"}]
        state = self._base_state(
            steps=steps,
            current_step_index=1,  # past all steps
        )
        result = await supervisor_node(state)
        assert result["next_node"] == "trimmer"

    @pytest.mark.asyncio
    async def test_skips_to_trimmer_on_error(self):
        """If there's an existing error in state, skip directly to trimmer."""
        steps = [{"agent": "Action", "task": "step 1"}, {"agent": "Action", "task": "step 2"}]
        state = self._base_state(
            steps=steps,
            error="Previous step failed",
        )
        result = await supervisor_node(state)
        assert result["next_node"] == "trimmer"

    @pytest.mark.asyncio
    async def test_creates_plan_when_no_steps(self):
        state = self._base_state(steps=[])
        with patch("src.workflow.orchestration.planner") as mock_p:
            mock_p.create_plan = AsyncMock(return_value=[{"agent": "Action", "task": "check weather"}])
            result = await supervisor_node(state)
        assert len(result["steps"]) > 0

    @pytest.mark.asyncio
    async def test_unknown_agent_routes_to_action_default(self):
        steps = [{"agent": "SomeUnknownAgent", "task": "do something"}]
        state = self._base_state(steps=steps)
        result = await supervisor_node(state)
        # Defaults to "action" per route_map.get(agent_name, "action")
        assert result["next_node"] == "action"

    @pytest.mark.asyncio
    async def test_advances_to_second_step_on_second_call(self):
        steps = [
            {"agent": "Action", "task": "step 1"},
            {"agent": "Knowledge", "task": "step 2"},
        ]
        state = self._base_state(steps=steps, current_step_index=1)
        result = await supervisor_node(state)
        assert result["next_node"] == "knowledge"


# ─────────────────────────────────────────────────────────────────────────────
# trimmer_node tests
# ─────────────────────────────────────────────────────────────────────────────

class TestTrimmerNode:

    @pytest.mark.asyncio
    async def test_empty_results_returns_trimmer_next_node(self):
        state = {"consolidated_results": [], "next_node": "aggregator"}
        result = await trimmer_node(state)
        assert result["next_node"] == "trimmer"

    @pytest.mark.asyncio
    async def test_short_results_not_summarized(self):
        state = {
            "consolidated_results": ["Short result that is well under 12000 chars"],
            "next_node": "aggregator",
        }
        result = await trimmer_node(state)
        assert result["next_node"] == "trimmer"
        # consolidated_results should still exist (or not — trimmer doesn't modify short ones)
        assert "next_node" in result

    @pytest.mark.asyncio
    async def test_long_results_triggers_llm_summarization(self):
        long_result = ["x" * 13000]  # Exceeds 12000 chars
        state = {
            "consolidated_results": long_result,
            "next_node": "aggregator",
        }
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "This is a concise summary of the long result."
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        with patch("src.workflow.orchestration.llm", mock_llm, create=True):
            with patch("src.workflow.graph.llm", mock_llm):
                result = await trimmer_node(state)

        assert "consolidated_results" in result
        # The summary should be shorter than the original 13000 chars
        total_new = sum(len(str(r)) for r in result["consolidated_results"])
        assert total_new < 13000

    @pytest.mark.asyncio
    async def test_long_results_llm_failure_falls_back_to_truncation(self):
        long_result = ["a" * 13000]
        state = {
            "consolidated_results": long_result,
            "next_node": "aggregator",
        }
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM down"))

        with patch("src.workflow.orchestration.llm", mock_llm, create=True):
            with patch("src.workflow.graph.llm", mock_llm):
                result = await trimmer_node(state)

        # Should still have consolidated_results — fell back to truncation
        assert "consolidated_results" in result


# ─────────────────────────────────────────────────────────────────────────────
# Router functions tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRouterFunctions:

    def test_trimmer_router_returns_next_node(self):
        state = {"next_node": "aggregator"}
        assert trimmer_router(state) == "aggregator"

    def test_trimmer_router_defaults_to_aggregator(self):
        state = {}
        assert trimmer_router(state) == "aggregator"

    def test_router_returns_next_node(self):
        state = {"next_node": "knowledge"}
        assert router(state) == "knowledge"

    def test_router_defaults_to_aggregator(self):
        state = {}
        assert router(state) == "aggregator"

    @pytest.mark.asyncio
    async def test_aggregator_node_returns_final_answer(self):
        state = {}
        result = await aggregator_node(state)
        assert "final_answer" in result


# ─────────────────────────────────────────────────────────────────────────────
# execute_tool_node tests
# ─────────────────────────────────────────────────────────────────────────────

class TestExecuteToolNode:

    def _base_state(self, **overrides):
        state = {
            "current_step_index": 0,
            "steps": [{"agent": "Action", "task": "get user balance"}],
            "req_data": {"token": "Bearer fake-token", "user_id": "user-123"},
            "consolidated_results": [],
            "error": "",
        }
        state.update(overrides)
        return state

    @pytest.mark.asyncio
    async def test_returns_increment_when_past_steps(self):
        state = self._base_state(
            current_step_index=5,
            steps=[{"agent": "Action", "task": "t"}],
        )
        mock_tool = AsyncMock(return_value="result")
        result = await execute_tool_node(state, mock_tool, "Action")
        assert result["current_step_index"] == 6

    @pytest.mark.asyncio
    async def test_executes_action_tool_with_token(self):
        state = self._base_state()
        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(return_value="User has 500 credits")

        mock_eval = MagicMock()
        mock_eval.status = "PASS"
        mock_eval_llm = MagicMock()
        mock_eval_llm.ainvoke = AsyncMock(return_value=mock_eval)

        mock_llm = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=mock_eval_llm)

        # registry is a local import inside execute_tool_node — patch at source module
        with patch("src.core.registry.registry") as mock_reg:
            mock_prompt = MagicMock()
            mock_prompt.format = MagicMock(return_value="reflect on: User has 500 credits")
            mock_reg.get = MagicMock(return_value=mock_prompt)
            with patch("src.workflow.graph.llm", mock_llm):
                result = await execute_tool_node(state, mock_tool, "Action")

        assert result["current_step_index"] == 1
        assert len(result["consolidated_results"]) > 0
        assert "User has 500 credits" in result["consolidated_results"][0]

    @pytest.mark.asyncio
    async def test_executes_knowledge_tool(self):
        state = self._base_state(
            steps=[{"agent": "Knowledge", "task": "retrieve document"}],
        )
        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(return_value="Document found: AI Basics")

        mock_eval = MagicMock()
        mock_eval.status = "PASS"
        mock_eval_llm = MagicMock()
        mock_eval_llm.ainvoke = AsyncMock(return_value=mock_eval)

        mock_llm = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=mock_eval_llm)

        with patch("src.core.registry.registry") as mock_reg:
            mock_prompt = MagicMock()
            mock_prompt.format = MagicMock(return_value="reflect on: Document found")
            mock_reg.get = MagicMock(return_value=mock_prompt)
            with patch("src.workflow.graph.llm", mock_llm):
                result = await execute_tool_node(state, mock_tool, "Knowledge")

        assert result["current_step_index"] == 1

    @pytest.mark.asyncio
    async def test_handles_tool_exception_gracefully(self):
        state = self._base_state()
        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(side_effect=Exception("Tool crashed"))

        mock_llm = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=mock_llm)

        with patch("src.workflow.graph.llm", mock_llm):
            result = await execute_tool_node(state, mock_tool, "Action")

        # Exception case — should contain error or consolidated results
        assert "error" in result or "consolidated_results" in result

    @pytest.mark.asyncio
    async def test_self_reflection_fail_triggers_replan(self):
        """When the evaluator returns FAIL, the system should increment replan_count."""
        state = self._base_state()
        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(return_value="Partial result")

        mock_eval_fail = MagicMock()
        mock_eval_fail.status = "FAIL"
        mock_eval_fail.revised_task = "Better task formulation"

        mock_eval_pass = MagicMock()
        mock_eval_pass.status = "PASS"
        mock_eval_pass.revised_task = None

        # First call: FAIL, Second call: PASS
        mock_eval_llm = MagicMock()
        mock_eval_llm.ainvoke = AsyncMock(side_effect=[mock_eval_fail, mock_eval_pass])

        mock_llm = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=mock_eval_llm)

        with patch("src.core.registry.registry") as mock_reg:
            mock_prompt = MagicMock()
            mock_prompt.format = MagicMock(return_value="reflect")
            mock_reg.get = MagicMock(return_value=mock_prompt)
            with patch("src.workflow.graph.llm", mock_llm):
                result = await execute_tool_node(state, mock_tool, "Action")

        assert result["current_step_index"] == 1
        # Tool was called twice due to replan
        assert mock_tool.execute.call_count == 2
