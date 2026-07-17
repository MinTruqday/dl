import uuid
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis.asyncio as aioredis

import os
REDIS_URI = os.getenv("REDIS_URI", "redis://redis:6379")



@pytest.fixture
async def redis_client():
    client = aioredis.from_url(REDIS_URI, decode_responses=True)
    try:
        await client.ping()
    except Exception as exc:
        pytest.fail(f"Cannot reach Redis at {REDIS_URI}: {exc}")
    yield client
    await client.aclose()


@pytest.fixture
def session_id() -> str:
    return f"test_session_{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def bank(redis_client):
    from src.proactive.bank import ProactiveMemoryBank
    instance = ProactiveMemoryBank()
    instance._redis = redis_client
    return instance


class TestMemoryBankCRUD:
    @pytest.mark.asyncio
    async def test_empty_bank_returned_for_new_session(self, bank, session_id):
        result = await bank.get_bank(session_id)
        assert result.session_id == session_id
        assert result.status == ""
        assert result.knowledge == []
        assert result.procedural == []

    @pytest.mark.asyncio
    async def test_update_status_persists(self, bank, session_id):
        await bank.update_status(session_id, "Working on step 2, Redis auth failing")
        result = await bank.get_bank(session_id)
        assert "Redis auth" in result.status

    @pytest.mark.asyncio
    async def test_save_knowledge_creates_entry(self, bank, session_id):
        await bank.save_knowledge(
            session_id,
            entry_id="req_user_auth",
            content="User must be authenticated via JWT before any tool call",
            category="task_fact",
        )
        result = await bank.get_bank(session_id)
        assert len(result.knowledge) == 1
        entry = result.knowledge[0]
        assert entry.id == "req_user_auth"
        assert "JWT" in entry.content
        assert entry.category == "task_fact"

    @pytest.mark.asyncio
    async def test_save_knowledge_updates_existing_entry(self, bank, session_id):
        await bank.save_knowledge(session_id, "path_config", "/app/config.yaml", "path")
        await bank.save_knowledge(session_id, "path_config", "/app/config/settings.yaml (corrected)", "path")
        result = await bank.get_bank(session_id)
        path_entries = [e for e in result.knowledge if e.id == "path_config"]
        assert len(path_entries) == 1
        assert "corrected" in path_entries[0].content

    @pytest.mark.asyncio
    async def test_save_procedural_creates_entry(self, bank, session_id):
        await bank.save_procedural(
            session_id,
            entry_id="fail_redis_conn",
            content="redis.exceptions.ConnectionError: Connection refused on port 6379",
            category="bug",
        )
        result = await bank.get_bank(session_id)
        assert len(result.procedural) == 1
        assert result.procedural[0].id == "fail_redis_conn"
        assert result.procedural[0].category == "bug"

    @pytest.mark.asyncio
    async def test_delete_removes_from_knowledge(self, bank, session_id):
        await bank.save_knowledge(session_id, "obsolete_fact", "No longer relevant", "env_fact")
        before = await bank.get_bank(session_id)
        assert "obsolete_fact" in {e.id for e in before.knowledge}
        await bank.delete_entry(session_id, "obsolete_fact")
        after = await bank.get_bank(session_id)
        assert "obsolete_fact" not in {e.id for e in after.knowledge}

    @pytest.mark.asyncio
    async def test_delete_removes_from_procedural(self, bank, session_id):
        await bank.save_procedural(session_id, "stale_attempt", "Old approach", "attempt")
        await bank.delete_entry(session_id, "stale_attempt")
        result = await bank.get_bank(session_id)
        assert all(e.id != "stale_attempt" for e in result.procedural)

    @pytest.mark.asyncio
    async def test_clear_bank_removes_all(self, bank, session_id):
        await bank.save_knowledge(session_id, "k1", "fact one", "task_fact")
        await bank.save_procedural(session_id, "p1", "attempt one", "attempt")
        await bank.clear_bank(session_id)
        result = await bank.get_bank(session_id)
        assert result.knowledge == []
        assert result.procedural == []
        assert result.status == ""

    @pytest.mark.asyncio
    async def test_multiple_entries_accumulated(self, bank, session_id):
        for i in range(5):
            await bank.save_knowledge(session_id, f"fact_{i}", f"Fact content {i}", "task_fact")
        for i in range(3):
            await bank.save_procedural(session_id, f"proc_{i}", f"Attempt {i} failed", "attempt")
        result = await bank.get_bank(session_id)
        assert len(result.knowledge) == 5
        assert len(result.procedural) == 3


class TestBankSerialization:
    @pytest.mark.asyncio
    async def test_unicode_content_survives_round_trip(self, bank, session_id):
        content = "Người dùng cần xác thực JWT trước mọi thao tác"
        await bank.save_knowledge(session_id, "unicode_fact", content, "task_fact")
        result = await bank.get_bank(session_id)
        assert result.knowledge[0].content == content

    @pytest.mark.asyncio
    async def test_created_at_is_iso8601(self, bank, session_id):
        await bank.save_knowledge(session_id, "ts_fact", "timestamp test", "env_fact")
        result = await bank.get_bank(session_id)
        from datetime import datetime
        parsed = datetime.fromisoformat(result.knowledge[0].created_at)
        assert parsed is not None

    @pytest.mark.asyncio
    async def test_access_count_increments_on_update(self, bank, session_id):
        await bank.save_knowledge(session_id, "count_entry", "initial content", "task_fact")
        await bank.save_knowledge(session_id, "count_entry", "updated content", "task_fact")
        result = await bank.get_bank(session_id)
        entry = next(e for e in result.knowledge if e.id == "count_entry")
        assert entry.access_count >= 1


class TestSessionIsolation:
    @pytest.mark.asyncio
    async def test_different_sessions_do_not_share_state(self, bank):
        sid_a = f"session_a_{uuid.uuid4().hex[:6]}"
        sid_b = f"session_b_{uuid.uuid4().hex[:6]}"
        await bank.save_knowledge(sid_a, "fact_a", "Only in session A", "task_fact")
        await bank.save_knowledge(sid_b, "fact_b", "Only in session B", "env_fact")
        a_ids = {e.id for e in (await bank.get_bank(sid_a)).knowledge}
        b_ids = {e.id for e in (await bank.get_bank(sid_b)).knowledge}
        assert "fact_a" in a_ids and "fact_b" not in a_ids
        assert "fact_b" in b_ids and "fact_a" not in b_ids


class TestPhase1Parsing:
    def test_parse_single_tool_call(self):
        from src.proactive.agent import _parse_phase1_tool_calls
        raw = '<tool_call>{"name": "memory_save_knowledge", "args": {"id": "req_auth", "content": "JWT required", "category": "task_fact"}}</tool_call>'
        calls = _parse_phase1_tool_calls(raw)
        assert len(calls) == 1
        assert calls[0]["name"] == "memory_save_knowledge"
        assert calls[0]["args"]["id"] == "req_auth"

    def test_parse_multiple_tool_calls(self):
        from src.proactive.agent import _parse_phase1_tool_calls
        raw = (
            '<tool_call>{"name": "memory_update_status", "args": {"status": "Step 2"}}</tool_call>\n'
            '<tool_call>{"name": "memory_save_procedural", "args": {"id": "fail_001", "content": "pip failed", "category": "bug"}}</tool_call>\n'
            '<tool_call>{"name": "memory_delete", "args": {"id": "old_fact"}}</tool_call>'
        )
        calls = _parse_phase1_tool_calls(raw)
        assert len(calls) == 3
        names = {c["name"] for c in calls}
        assert {"memory_update_status", "memory_save_procedural", "memory_delete"} == names

    def test_parse_no_tool_calls_returns_empty(self):
        from src.proactive.agent import _parse_phase1_tool_calls
        assert _parse_phase1_tool_calls("Nothing new to save.") == []

    def test_malformed_json_skipped_gracefully(self):
        from src.proactive.agent import _parse_phase1_tool_calls
        raw = (
            '<tool_call>{"name": "memory_save_knowledge", "args": {"id": "ok", "content": "valid", "category": "task_fact"}}</tool_call>\n'
            '<tool_call>{not valid json at all</tool_call>'
        )
        calls = _parse_phase1_tool_calls(raw)
        assert len(calls) == 1
        assert calls[0]["name"] == "memory_save_knowledge"


class TestPhase2Parsing:
    def test_parse_intervention_with_context(self):
        from src.proactive.agent import _parse_phase2_output
        raw = "<context_for_action>\nReminder: JWT required (req_auth) before any tool call.\n</context_for_action>"
        result = _parse_phase2_output(raw)
        assert result is not None
        assert "JWT" in result

    def test_parse_no_intervention_tag(self):
        from src.proactive.agent import _parse_phase2_output
        assert _parse_phase2_output("<no_intervention/>") is None

    def test_parse_no_intervention_with_whitespace(self):
        from src.proactive.agent import _parse_phase2_output
        assert _parse_phase2_output("\n  <no_intervention/>  \n") is None

    def test_parse_empty_context_tag_returns_none(self):
        from src.proactive.agent import _parse_phase2_output
        assert _parse_phase2_output("<context_for_action>   </context_for_action>") is None

    def test_parse_garbage_output_returns_none(self):
        from src.proactive.agent import _parse_phase2_output
        assert _parse_phase2_output("I think the agent is fine.") is None


class TestTrajectoryFormatting:
    def test_window_truncates_to_last_k(self):
        from src.proactive.agent import _format_trajectory_window
        trajectory = [{"role": "user", "content": f"message {i}"} for i in range(20)]
        lines = [l for l in _format_trajectory_window(trajectory, window=8).split("\n") if l.startswith("[TURN")]
        assert len(lines) == 8

    def test_long_content_is_truncated(self):
        from src.proactive.agent import _format_trajectory_window
        result = _format_trajectory_window([{"role": "assistant", "content": "x" * 2000}], window=8)
        assert "[...TRUNCATED...]" in result

    def test_empty_trajectory(self):
        from src.proactive.agent import _format_trajectory_window
        assert _format_trajectory_window([], window=8) == "(no trajectory)"


class TestMiddlewareTriggerLogic:
    def test_triggers_on_step_1(self):
        from src.proactive.middleware import _should_trigger
        assert _should_trigger(1) is True

    def test_triggers_on_interval(self):
        from src.proactive.middleware import _should_trigger
        assert all(_should_trigger(s) for s in [5, 10, 15, 20])

    def test_does_not_trigger_on_non_interval(self):
        from src.proactive.middleware import _should_trigger
        assert all(not _should_trigger(s) for s in [2, 3, 6, 7, 11])

    def test_triggers_on_force_failure(self):
        from src.proactive.middleware import _should_trigger
        assert _should_trigger(3, force_on_failure=True) is True
        assert _should_trigger(7, force_on_failure=True) is True

    def test_wrap_memory_context_format(self):
        from src.proactive.middleware import wrap_memory_context
        wrapped = wrap_memory_context("JWT required")
        assert "<memory_context>" in wrapped
        assert "JWT required" in wrapped
        assert "</memory_context>" in wrapped


class TestMiddlewarePipelineIntegration:
    @pytest.mark.asyncio
    async def test_returns_none_on_non_trigger_step(self, session_id):
        from src.proactive.middleware import MemoryMiddleware
        result = await MemoryMiddleware().process(
            session_id=session_id,
            trajectory=[{"role": "user", "content": "hello"}],
            step_count=3,
            task_description="Test task",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_calls_agent_on_trigger_step(self, session_id):
        from src.proactive.middleware import MemoryMiddleware
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value="JWT is required before proceeding")
        with patch("src.proactive.middleware.proactive_memory_agent", mock_agent):
            result = await MemoryMiddleware().process(
                session_id=session_id,
                trajectory=[{"role": "user", "content": "do something"}],
                step_count=5,
                task_description="Authenticated tool use task",
            )
        mock_agent.run.assert_called_once()
        assert result is not None
        assert "<memory_context>" in result and "JWT" in result

    @pytest.mark.asyncio
    async def test_returns_none_when_agent_silent(self, session_id):
        from src.proactive.middleware import MemoryMiddleware
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=None)
        with patch("src.proactive.middleware.proactive_memory_agent", mock_agent):
            result = await MemoryMiddleware().process(
                session_id=session_id,
                trajectory=[{"role": "user", "content": "task"}],
                step_count=5,
                task_description="Task",
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_fault_tolerant_on_agent_crash(self, session_id):
        from src.proactive.middleware import MemoryMiddleware
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(side_effect=RuntimeError("Simulated LLM crash"))
        with patch("src.proactive.middleware.proactive_memory_agent", mock_agent):
            result = await MemoryMiddleware().process(
                session_id=session_id,
                trajectory=[{"role": "user", "content": "task"}],
                step_count=5,
                task_description="Task",
            )
        assert result is None


class TestProactiveAgentWithMockLLM:
    @pytest.mark.asyncio
    async def test_phase1_dispatches_all_tool_types(self, bank, session_id):
        from langchain_core.messages import AIMessage
        from src.proactive.agent import ProactiveMemoryAgent

        llm_out = (
            '<tool_call>{"name": "memory_update_status", "args": {"status": "Auth flow in progress"}}</tool_call>\n'
            '<tool_call>{"name": "memory_save_knowledge", "args": {"id": "req_jwt", "content": "JWT must be in Authorization header", "category": "task_fact"}}</tool_call>\n'
            '<tool_call>{"name": "memory_save_procedural", "args": {"id": "fail_missing_header", "content": "Request without header returned 401", "category": "bug"}}</tool_call>'
        )
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content=llm_out))
        agent = ProactiveMemoryAgent(bank=bank)
        with patch.object(agent, "_build_llm", return_value=mock_llm):
            updated = await agent._run_phase1(
                session_id=session_id,
                task_description="Implement authenticated API endpoint",
                trajectory_window="[TURN 1] USER: Build the auth flow",
                bank=await bank.get_bank(session_id),
            )
        assert updated.status == "Auth flow in progress"
        assert "req_jwt" in {e.id for e in updated.knowledge}
        assert "fail_missing_header" in {e.id for e in updated.procedural}

    @pytest.mark.asyncio
    async def test_phase2_returns_intervention_string(self, bank, session_id):
        from langchain_core.messages import AIMessage
        from src.proactive.agent import ProactiveMemoryAgent

        await bank.save_knowledge(session_id, "req_jwt_check", "JWT required on every request", "task_fact")
        current_bank = await bank.get_bank(session_id)
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content=(
            "<context_for_action>req_jwt_check: JWT must be present in the Authorization header.</context_for_action>"
        )))
        agent = ProactiveMemoryAgent(bank=bank)
        with patch.object(agent, "_build_llm", return_value=mock_llm):
            intervention = await agent._run_phase2(
                session_id=session_id,
                task_description="Implement authenticated API endpoint",
                trajectory_window="[TURN 1] USER: Make the API call",
                bank=current_bank,
            )
        assert intervention is not None
        assert "req_jwt_check" in intervention

    @pytest.mark.asyncio
    async def test_phase2_returns_none_when_silent(self, bank, session_id):
        from langchain_core.messages import AIMessage
        from src.proactive.agent import ProactiveMemoryAgent

        await bank.save_knowledge(session_id, "env_port", "Service runs on port 8080", "env_fact")
        current_bank = await bank.get_bank(session_id)
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="<no_intervention/>"))
        agent = ProactiveMemoryAgent(bank=bank)
        with patch.object(agent, "_build_llm", return_value=mock_llm):
            intervention = await agent._run_phase2(
                session_id=session_id,
                task_description="Task",
                trajectory_window="[TURN 1] USER: context already visible",
                bank=current_bank,
            )
        assert intervention is None

    @pytest.mark.asyncio
    async def test_phase1_llm_failure_does_not_crash(self, bank, session_id):
        from src.proactive.agent import ProactiveMemoryAgent
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=RuntimeError("HF endpoint timeout"))
        agent = ProactiveMemoryAgent(bank=bank)
        with patch.object(agent, "_build_llm", return_value=mock_llm):
            result_bank = await agent._run_phase1(
                session_id=session_id,
                task_description="Task",
                trajectory_window="window",
                bank=await bank.get_bank(session_id),
            )
        assert result_bank is not None

    @pytest.mark.asyncio
    async def test_phase2_llm_failure_returns_none(self, bank, session_id):
        from langchain_core.messages import AIMessage
        from src.proactive.agent import ProactiveMemoryAgent

        await bank.save_knowledge(session_id, "k1", "some fact", "task_fact")
        current_bank = await bank.get_bank(session_id)
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=ConnectionError("Network error"))
        agent = ProactiveMemoryAgent(bank=bank)
        with patch.object(agent, "_build_llm", return_value=mock_llm):
            result = await agent._run_phase2(
                session_id=session_id,
                task_description="Task",
                trajectory_window="window",
                bank=current_bank,
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_full_run_end_to_end(self, bank, session_id):
        from langchain_core.messages import AIMessage
        from src.proactive.agent import ProactiveMemoryAgent

        trajectory = [
            {"role": "user", "content": "Implement auth using JWT tokens"},
            {"role": "assistant", "content": "Starting implementation"},
            {"role": "user", "content": "Also make sure Redis is used for session store"},
            {"role": "assistant", "content": "Ok, will use Redis"},
        ]

        phase1_output = (
            '<tool_call>{"name": "memory_save_knowledge", "args": {"id": "req_jwt", "content": "JWT auth required", "category": "task_fact"}}</tool_call>\n'
            '<tool_call>{"name": "memory_save_knowledge", "args": {"id": "req_redis_session", "content": "Redis must be used for session store", "category": "task_fact"}}</tool_call>'
        )
        phase2_output = (
            "<context_for_action>req_redis_session: Redis session store is required. "
            "Ensure the session manager is initialized before handling requests.</context_for_action>"
        )

        call_count = 0

        async def mock_ainvoke(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            return AIMessage(content=phase1_output if call_count == 1 else phase2_output)

        mock_llm = MagicMock()
        mock_llm.ainvoke = mock_ainvoke
        agent = ProactiveMemoryAgent(bank=bank)
        with patch.object(agent, "_build_llm", return_value=mock_llm):
            intervention = await agent.run(
                session_id=session_id,
                task_description="Build authenticated service with Redis sessions",
                trajectory=trajectory,
            )

        final_bank = await bank.get_bank(session_id)
        knowledge_ids = {e.id for e in final_bank.knowledge}
        assert "req_jwt" in knowledge_ids
        assert "req_redis_session" in knowledge_ids
        assert intervention is not None
        assert "redis" in intervention.lower() or "Redis" in intervention


class TestBankFormatSnapshot:
    @pytest.mark.asyncio
    async def test_empty_bank_snapshot(self, bank, session_id):
        b = await bank.get_bank(session_id)
        assert bank.format_bank_snapshot(b) == "(empty bank)"

    @pytest.mark.asyncio
    async def test_snapshot_contains_all_entries(self, bank, session_id):
        await bank.save_knowledge(session_id, "fact_1", "JWT required", "task_fact")
        await bank.save_knowledge(session_id, "fact_2", "Port is 8080", "env_fact")
        await bank.save_procedural(session_id, "proc_1", "Command failed", "bug")
        snapshot = bank.format_bank_snapshot(await bank.get_bank(session_id))
        assert "[KNOWLEDGE]" in snapshot
        assert "[PROCEDURAL]" in snapshot
        for item in ["fact_1", "fact_2", "proc_1", "JWT required", "Command failed"]:
            assert item in snapshot


class TestRegistryPrompts:
    def test_memory_bank_phase1_prompt_registered(self):
        from src.core.registry import PromptType, registry
        prompt = registry.get(PromptType.MEMORY_BANK_PHASE1)
        assert len(prompt) > 100
        for keyword in ["memory_save_knowledge", "memory_save_procedural", "memory_update_status", "memory_delete", "<examples>", "<edge_cases>"]:
            assert keyword in prompt

    def test_memory_bank_phase2_prompt_registered(self):
        from src.core.registry import PromptType, registry
        prompt = registry.get(PromptType.MEMORY_BANK_PHASE2)
        assert len(prompt) > 100
        for keyword in ["<context_for_action>", "<no_intervention/>", "<examples>", "<edge_cases>"]:
            assert keyword in prompt

    def test_both_prompts_contain_metis_system_base(self):
        from src.core.registry import PromptType, registry
        for pt in [PromptType.MEMORY_BANK_PHASE1, PromptType.MEMORY_BANK_PHASE2]:
            assert "metis_behavior" in registry.get(pt)
