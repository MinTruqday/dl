import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, List, Optional
from src.schemas.evaluation import HallucinationJudgment, RelevanceJudgment

from loguru import logger


@dataclass
class GraderResult:
    grader_name: str
    passed: bool
    score: float = 1.0
    feedback: str = ""
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RubricResult:
    passed: bool
    grader_results: List[GraderResult] = field(default_factory=list)
    combined_feedback: str = ""
    attempt: int = 1

    @property
    def failed_graders(self) -> List[GraderResult]:
        return [g for g in self.grader_results if not g.passed]

    @property
    def average_score(self) -> float:
        if not self.grader_results:
            return 0.0
        return sum(g.score for g in self.grader_results) / len(self.grader_results)


class BaseGrader(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def grade(self, response: str, context: dict) -> GraderResult:
        raise NotImplementedError


class ResponseLengthGrader(BaseGrader):
    def __init__(self, min_length: int = 10, max_length: int = 50_000):
        self.min_length = min_length
        self.max_length = max_length

    @property
    def name(self) -> str:
        return "response_length"

    async def grade(self, response: str, context: dict) -> GraderResult:
        text = response.strip()
        if not text:
            return GraderResult(
                grader_name=self.name,
                passed=False,
                score=0.0,
                feedback="Empty response content. Please provide meaningful information",
            )
        if len(text) < self.min_length:
            return GraderResult(
                grader_name=self.name,
                passed=False,
                score=len(text) / self.min_length,
                feedback=f"Response does not meet minimum length requirement ({len(text)}/{self.min_length} characters)",
            )
        if len(text) > self.max_length:
            return GraderResult(
                grader_name=self.name,
                passed=False,
                score=0.5,
                feedback=f"Response exceeds maximum length limit ({len(text)}/{self.max_length} characters)",
            )
        return GraderResult(grader_name=self.name, passed=True, score=1.0)


class ErrorPrefixGrader(BaseGrader):
    @property
    def name(self) -> str:
        return "error_prefix"

    async def grade(self, response: str, context: dict) -> GraderResult:
        import json

        text = response.strip()
        lowered = text.lower()
        failed_statuses = {
            "action_execution_failed",
            "approval_required",
            "execution_step_failed",
            "response_generation_failed",
            "task_evaluation_failed",
            "task_execution_failed",
            "tool_execution_failed",
            "tool_selection_failed",
            "tool_selection_validation_failed",
            "tool_unavailable",
        }
        try:
            payload = json.loads(text)
        except (TypeError, json.JSONDecodeError):
            payload = None
        if (
            isinstance(payload, dict) and payload.get("status") in failed_statuses
        ) or lowered.startswith(("error:", "execution error:", "failed:")):
            return GraderResult(
                grader_name=self.name,
                passed=False,
                score=0.0,
                feedback="Response contains a machine readable execution failure",
            )
        return GraderResult(grader_name=self.name, passed=True, score=1.0)


class ToolResultGrader(BaseGrader):
    @property
    def name(self) -> str:
        return "tool_result"

    async def grade(self, response: str, context: dict) -> GraderResult:
        tool_error = context.get("tool_error")
        if tool_error:
            return GraderResult(
                grader_name=self.name,
                passed=False,
                score=0.0,
                feedback=f"Tool execution failed: {str(tool_error)[:200]}. Please adjust input parameters or switch tools.",
            )
        return GraderResult(grader_name=self.name, passed=True, score=1.0)


class KeywordPresenceGrader(BaseGrader):
    def __init__(self, required_keywords: List[str], case_sensitive: bool = False):
        self.required_keywords = required_keywords
        self.case_sensitive = case_sensitive

    @property
    def name(self) -> str:
        return "keyword_presence"

    async def grade(self, response: str, context: dict) -> GraderResult:
        text = response if self.case_sensitive else response.lower()
        missing = []
        for kw in self.required_keywords:
            needle = kw if self.case_sensitive else kw.lower()
            if needle not in text:
                missing.append(kw)
        if missing:
            return GraderResult(
                grader_name=self.name,
                passed=False,
                score=1.0 - len(missing) / len(self.required_keywords),
                feedback=f"Response is missing required keywords: {', '.join(missing)}",
            )
        return GraderResult(grader_name=self.name, passed=True, score=1.0)


class HallucinationGrader(BaseGrader):
    @property
    def name(self) -> str:
        return "hallucination_judge"

    async def grade(self, response: str, context: dict) -> GraderResult:
        try:
            from src.workflow.graph import llm

            evaluator = llm.with_structured_output(HallucinationJudgment)
            query = context.get("query", "user query")
            from src.core.registry import registry, PromptType

            prompt = registry.get(PromptType.RUBRIC_HALLUCINATION_JUDGE).format(
                query=query[:200], response=response[:500]
            )
            result: HallucinationJudgment = await evaluator.ainvoke(prompt)
            if result.is_hallucination_or_refusal and result.confidence > 0.7:
                return GraderResult(
                    grader_name=self.name,
                    passed=False,
                    score=1.0 - result.confidence,
                    feedback=f"System detected signs of data hallucination with confidence {result.confidence:.2f}: {result.explanation}",
                )
        except Exception:
            logger.exception("Hallucination grader unavailable")
            return GraderResult(
                grader_name=self.name,
                passed=False,
                score=0.0,
                feedback="Hallucination grader unavailable",
            )
        return GraderResult(grader_name=self.name, passed=True, score=1.0)


class RelevanceGrader(BaseGrader):
    @property
    def name(self) -> str:
        return "relevance_judge"

    async def grade(self, response: str, context: dict) -> GraderResult:
        query = context.get("query", "")
        if not query:
            return GraderResult(grader_name=self.name, passed=True, score=1.0)
        try:
            from src.workflow.graph import llm

            evaluator = llm.with_structured_output(RelevanceJudgment)
            from src.core.registry import registry, PromptType

            prompt = registry.get(PromptType.RUBRIC_RELEVANCE_JUDGE).format(
                query=query[:300], response=response[:500]
            )
            result: RelevanceJudgment = await evaluator.ainvoke(prompt)
            if not result.is_relevant or result.relevance_score < 0.5:
                return GraderResult(
                    grader_name=self.name,
                    passed=False,
                    score=result.relevance_score,
                    feedback=f"Response relevance is insufficient with score {result.relevance_score:.2f}: {result.feedback}",
                )
            return GraderResult(grader_name=self.name, passed=True, score=result.relevance_score)
        except Exception:
            logger.exception("Relevance grader unavailable")
            return GraderResult(
                grader_name=self.name,
                passed=False,
                score=0.0,
                feedback="Relevance grader unavailable",
            )


class Rubric:
    def __init__(self, graders: List[BaseGrader], name: str = "default"):
        self.graders = graders
        self.name = name

    async def evaluate(self, response: str, context: dict, attempt: int = 1) -> RubricResult:
        tasks = [g.grade(response, context) for g in self.graders]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        resolved: List[GraderResult] = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.warning(f"Grader {self.graders[i].name} raised {res}")
                resolved.append(
                    GraderResult(
                        grader_name=self.graders[i].name,
                        passed=False,
                        score=0.0,
                        feedback="Grader execution failed",
                    )
                )
            else:
                resolved.append(res)
        failed = [r for r in resolved if not r.passed]
        passed = len(failed) == 0
        combined_feedback = "\n".join([f"[{r.grader_name}] {r.feedback}" for r in failed])
        return RubricResult(
            passed=passed,
            grader_results=resolved,
            combined_feedback=combined_feedback,
            attempt=attempt,
        )


def create_standard_rubric(use_llm_judge: bool = False) -> Rubric:
    graders: List[BaseGrader] = [ResponseLengthGrader(min_length=10), ErrorPrefixGrader()]
    if use_llm_judge:
        graders.append(HallucinationGrader())
    return Rubric(graders=graders, name="standard")


def create_document_rubric(use_llm_judge: bool = False) -> Rubric:
    graders: List[BaseGrader] = [
        ResponseLengthGrader(min_length=20),
        ErrorPrefixGrader(),
        ToolResultGrader(),
    ]
    if use_llm_judge:
        graders.extend([HallucinationGrader(), RelevanceGrader()])
    return Rubric(graders=graders, name="document")


AgentCallable = Callable[[str, dict], Coroutine[Any, Any, str]]


class RubricMiddleware:
    """
    <module_purpose>
    <purpose>Applies deterministic evaluation rubrics to LLM outputs.</purpose>
    <metis_behavior>Rejects outputs strictly based on configured policies without leniency.</metis_behavior>
    </module_purpose>
    """

    def __init__(self, rubric: Rubric, max_retries: int = 3, retry_delay_seconds: float = 0.5):
        self.rubric = rubric
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self._history: list[RubricResult] = []

    async def run(
        self,
        agent_callable: AgentCallable,
        args: tuple = (),
        kwargs: dict = None,
        context: dict = None,
        feedback_injector: Optional[Callable[[str, str], tuple]] = None,
    ) -> tuple[str, RubricResult]:
        if kwargs is None:
            kwargs = {}
        if context is None:
            context = {}

        current_args = args
        current_kwargs = kwargs
        last_response = ""
        last_rubric_result = None

        for attempt in range(1, self.max_retries + 1):
            logger.info(
                f"RubricMiddleware attempt {attempt}/{self.max_retries} (rubric={self.rubric.name})"
            )
            try:
                last_response = await agent_callable(*current_args, **current_kwargs)
            except Exception as e:
                logger.exception(f"Agent callable failed on attempt {attempt}")
                last_response = f"Execution error: {e}"

            rubric_result = await self.rubric.evaluate(
                response=last_response, context=context, attempt=attempt
            )
            last_rubric_result = rubric_result
            self._history.append(rubric_result)

            if rubric_result.passed:
                logger.info(
                    f"RubricMiddleware PASSED on attempt {attempt} (score={rubric_result.average_score:.2f})"
                )
                return last_response, rubric_result

            logger.warning(
                f"RubricMiddleware: FAILED on attempt {attempt}. "
                f"Failed: {[g.grader_name for g in rubric_result.failed_graders]}. Retrying"
            )
            if attempt < self.max_retries:
                if feedback_injector:
                    new_args, new_kwargs = feedback_injector(
                        last_response, rubric_result.combined_feedback
                    )
                    current_args = new_args
                    current_kwargs = new_kwargs
                await asyncio.sleep(self.retry_delay_seconds)

        logger.warning(f"RubricMiddleware max retries ({self.max_retries}) reached")
        return last_response, last_rubric_result

    def get_history(self) -> list[RubricResult]:
        return list(self._history)

    def clear_history(self):
        self._history.clear()


standard_rubric_middleware = RubricMiddleware(
    rubric=create_standard_rubric(use_llm_judge=False), max_retries=3
)

document_rubric_middleware = RubricMiddleware(
    rubric=create_document_rubric(use_llm_judge=False), max_retries=2
)
