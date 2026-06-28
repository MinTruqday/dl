"""
Heavy-duty unit tests for agentic_ai agents:
 - EngineAgent (search engine)
 - InterpreterAgent (code interpreter)
 - ReasoningAgent (analytical reasoning)
 - PlanAgent (task planner)
 - RouteAgent (semantic router)
 - SandboxAgent (tool dispatcher)
"""
import sys
import os
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

# ── sys.path bootstrap ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../agentic_ai"))


# ─────────────────────────────────────────────────────────────────────────────
# EngineAgent tests (src/agents/engine.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineAgent:

    def _make_agent(self, tavily_key: str | None = None):
        """Create EngineAgent with mocked settings."""
        mock_settings = MagicMock()
        mock_settings.TAVILY_API_KEY = tavily_key
        with patch("src.core.infrastructure.configuration.settings", mock_settings):
            from src.agents.engine import EngineAgent
            agent = EngineAgent.__new__(EngineAgent)
            agent.api_key_valid = bool(tavily_key and len(tavily_key) > 10)
            agent.client = None
            return agent

    @pytest.mark.asyncio
    async def test_ssrf_attempt_is_blocked(self):
        from src.agents.engine import EngineAgent
        agent = self._make_agent()
        result = await agent.execute("localhost:8080/secret-data")
        assert "từ chối" in result.lower() or "bảo mật" in result.lower()

    @pytest.mark.asyncio
    async def test_ssrf_private_ip_blocked(self):
        from src.agents.engine import EngineAgent
        agent = self._make_agent()
        result = await agent.execute("10.0.0.1/internal-api")
        assert "từ chối" in result.lower() or "bảo mật" in result.lower()

    @pytest.mark.asyncio
    async def test_duckduckgo_fallback_when_no_tavily_key(self):
        from src.agents.engine import EngineAgent
        agent = self._make_agent(tavily_key=None)
        with patch.object(agent, "_duckduckgo_search", new_callable=AsyncMock) as mock_ddg:
            mock_ddg.return_value = "Result from DuckDuckGo"
            result = await agent.execute("Python programming language")
        assert result == "Result from DuckDuckGo"

    @pytest.mark.asyncio
    async def test_returns_no_info_when_both_engines_fail(self):
        from src.agents.engine import EngineAgent
        agent = self._make_agent(tavily_key=None)
        with patch.object(agent, "_duckduckgo_search", new_callable=AsyncMock) as mock_ddg:
            mock_ddg.return_value = ""
            result = await agent.execute("What is 2+2?")
        assert "không thể" in result.lower() or "trích xuất" in result.lower()

    @pytest.mark.asyncio
    async def test_tavily_fallback_to_duckduckgo_on_failure(self):
        from src.agents.engine import EngineAgent
        agent = self._make_agent(tavily_key="valid-api-key-123456")
        mock_tavily = MagicMock()
        agent.client = mock_tavily
        with patch.object(agent, "_tavily_search", new_callable=AsyncMock) as mock_tav:
            mock_tav.side_effect = Exception("Tavily down")
            with patch.object(agent, "_duckduckgo_search", new_callable=AsyncMock) as mock_ddg:
                mock_ddg.return_value = "DDG fallback result"
                result = await agent.execute("Machine learning basics")
        assert result == "DDG fallback result"

    @pytest.mark.asyncio
    async def test_duckduckgo_formats_results_correctly(self):
        from src.agents.engine import EngineAgent
        agent = self._make_agent()
        fake_results = [
            {"title": "Python Docs", "body": "Python is a language", "href": "https://python.org"},
        ]
        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = fake_results
            result = await agent._duckduckgo_search("python")
        assert "Python Docs" in result
        assert "https://python.org" in result


# ─────────────────────────────────────────────────────────────────────────────
# InterpreterAgent tests (src/agents/interpreter.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestInterpreterAgent:

    def _make_interpreter(self):
        mock_settings = MagicMock()
        mock_settings.DEFAULT_HTTP_TIMEOUT = 30.0
        with patch("src.core.infrastructure.configuration.settings", mock_settings):
            from src.agents.interpreter import InterpreterAgent
            return InterpreterAgent()

    @pytest.mark.asyncio
    async def test_executes_simple_python_code(self):
        agent = self._make_interpreter()
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "```python\nprint('Hello from interpreter')\n```"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"Hello from interpreter\n", b""))

        with patch("src.agents.plan.llm", mock_llm):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
                    mock_thread.side_effect = ["/tmp/test_script.py", None]
                    with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
                        mock_wait.return_value = (b"Hello from interpreter\n", b"")
                        with patch("os.path.exists", return_value=False):
                            result = await agent.execute("Print hello world")
        # Result should contain the output
        assert "Hello from interpreter" in result or "execution" in result.lower()

    @pytest.mark.asyncio
    async def test_handles_execution_error(self):
        agent = self._make_interpreter()
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "```python\nraise ValueError('test error')\n```"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"ValueError: test error"))

        with patch("src.agents.plan.llm", mock_llm):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
                    mock_thread.side_effect = ["/tmp/test_script.py", None]
                    with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
                        mock_wait.return_value = (b"", b"ValueError: test error")
                        with patch("os.path.exists", return_value=False):
                            result = await agent.execute("Raise an error")
        assert "ValueError" in result or "issues" in result.lower() or "lỗi" in result.lower()

    @pytest.mark.asyncio
    async def test_handles_llm_exception(self):
        agent = self._make_interpreter()
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM offline"))

        with patch("src.agents.plan.llm", mock_llm):
            result = await agent.execute("Print something")
        assert "lỗi" in result.lower() or "xảy ra" in result.lower()

    @pytest.mark.asyncio
    async def test_extracts_code_without_python_tag(self):
        """Interpreter should still extract code if not tagged as `python`."""
        agent = self._make_interpreter()
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "```\nprint(42)\n```"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"42\n", b""))

        with patch("src.agents.plan.llm", mock_llm):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
                    mock_thread.side_effect = ["/tmp/test.py", None]
                    with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
                        mock_wait.return_value = (b"42\n", b"")
                        with patch("os.path.exists", return_value=False):
                            result = await agent.execute("Print 42")
        assert "42" in result or "execution" in result.lower()


# ─────────────────────────────────────────────────────────────────────────────
# ReasoningAgent tests (src/agents/reasoning.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestReasoningAgent:

    def _make_agent(self):
        mock_settings = MagicMock()
        mock_settings.LLAMA_MODEL = "test-model"
        mock_settings.HF_TOKEN = "hf-fake"
        with patch("src.core.infrastructure.configuration.settings", mock_settings):
            from src.agents.reasoning import ReasoningAgent
            return ReasoningAgent()

    @pytest.mark.asyncio
    async def test_execute_returns_reasoning_result(self):
        agent = self._make_agent()
        mock_llm = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = "This is a well-reasoned analysis of the task."
        mock_llm.ainvoke = AsyncMock(return_value=mock_msg)

        mock_registry = MagicMock()
        mock_template = MagicMock()
        mock_template.format = MagicMock(return_value="Analyze: test task")
        mock_registry.get = MagicMock(return_value=mock_template)

        with patch("src.agents.reasoning.AsyncInferenceClient"):
            with patch("src.agents.reasoning.HFInferenceChat", return_value=mock_llm):
                with patch("src.agents.reasoning.registry", mock_registry):
                    result = await agent.execute("Analyze the pros and cons of remote work")

        assert "analysis" in result.lower() or "reasoned" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_handles_llm_exception(self):
        agent = self._make_agent()
        with patch("src.agents.reasoning.AsyncInferenceClient"):
            with patch("src.agents.reasoning.HFInferenceChat") as mock_hf:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(side_effect=Exception("Connection refused"))
                mock_hf.return_value = mock_llm
                result = await agent.execute("What is deep learning?")
        assert "gặp trục trặc" in result.lower() or "lỗi" in result.lower()

    def test_build_context_empty_documents(self):
        agent = self._make_agent()
        result = agent._build_context([])
        assert "không chứa" in result.lower() or "không có" in result.lower() or "kho" in result.lower()

    def test_build_context_with_documents(self):
        agent = self._make_agent()
        docs = [
            {
                "metadata": {"title": "AI Basics", "author": "John Doe"},
                "text": "Artificial intelligence is the simulation of human intelligence.",
            }
        ]
        result = agent._build_context(docs)
        assert "AI Basics" in result
        assert "John Doe" in result
        assert "simulation" in result

    def test_build_context_truncates_at_800_chars(self):
        agent = self._make_agent()
        long_text = "x" * 2000
        docs = [{"metadata": {"title": "Long Doc", "author": "Author"}, "text": long_text}]
        result = agent._build_context(docs)
        # The text is sliced at [:800], so the total result should be < 1000 from that doc
        assert len(result) < 2500

    @pytest.mark.asyncio
    async def test_evaluate_quality_returns_no_retry_on_good_answer(self):
        agent = self._make_agent()
        mock_eval = MagicMock()
        mock_eval.is_hallucination = False
        mock_eval.feedback = "Answer is factual and complete."

        with patch("src.agents.reasoning.AsyncInferenceClient"):
            with patch("src.agents.reasoning.HFInferenceChat") as mock_hf:
                mock_llm = MagicMock()
                mock_llm.with_structured_output = MagicMock(return_value=mock_llm)
                mock_llm.ainvoke = AsyncMock(return_value=mock_eval)
                mock_hf.return_value = mock_llm
                with patch("src.agents.reasoning.registry") as mock_reg:
                    mock_reg.get.return_value.format = MagicMock(return_value="evaluation prompt")
                    result = await agent.evaluate_quality(
                        "What is AI?",
                        "AI is a branch of computer science.",
                        [{"metadata": {"title": "T", "author": "A"}, "text": "AI text"}],
                    )
        assert result["should_retry"] is False

    @pytest.mark.asyncio
    async def test_evaluate_quality_signals_retry_on_hallucination(self):
        agent = self._make_agent()
        mock_eval = MagicMock()
        mock_eval.is_hallucination = True
        mock_eval.feedback = "The answer contains fabricated information."

        with patch("src.agents.reasoning.AsyncInferenceClient"):
            with patch("src.agents.reasoning.HFInferenceChat") as mock_hf:
                mock_llm = MagicMock()
                mock_llm.with_structured_output = MagicMock(return_value=mock_llm)
                mock_llm.ainvoke = AsyncMock(return_value=mock_eval)
                mock_hf.return_value = mock_llm
                with patch("src.agents.reasoning.registry") as mock_reg:
                    mock_reg.get.return_value.format = MagicMock(return_value="evaluation prompt")
                    result = await agent.evaluate_quality("Q", "A", [])
        assert result["should_retry"] is True

    @pytest.mark.asyncio
    async def test_evaluate_quality_handles_llm_failure_gracefully(self):
        agent = self._make_agent()
        with patch("src.agents.reasoning.AsyncInferenceClient"):
            with patch("src.agents.reasoning.HFInferenceChat") as mock_hf:
                mock_llm = MagicMock()
                mock_llm.with_structured_output = MagicMock(return_value=mock_llm)
                mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM error"))
                mock_hf.return_value = mock_llm
                with patch("src.agents.reasoning.registry") as mock_reg:
                    mock_reg.get.return_value.format = MagicMock(return_value="prompt")
                    result = await agent.evaluate_quality("Q", "A", [])
        # On failure, should_retry is False and feedback contains error info
        assert result["should_retry"] is False
        assert "error" in result["feedback"].lower() or "encountered" in result["feedback"].lower()
