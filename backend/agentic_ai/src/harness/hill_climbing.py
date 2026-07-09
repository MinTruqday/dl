

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from loguru import logger


IssueCategory = Literal[
    "prompt_quality",
    "tool_failure",
    "grader_too_strict",
    "grader_too_lenient",
    "timeout",
    "hallucination",
    "routing_error",
    "token_budget",
]

ImprovementStatus = Literal["pending", "approved", "applied", "rejected", "rolled_back"]


@dataclass
class DetectedIssue:
    issue_id: str
    category: IssueCategory
    title: str
    description: str
    affected_component: str
    evidence_count: int
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    first_seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    example_session_ids: List[str] = field(default_factory=list)


@dataclass
class ImprovementSuggestion:
    improvement_id: str
    issue_id: str
    improvement_type: Literal["prompt_tweak", "tool_config", "grader_config", "routing_rule"]
    title: str
    description: str
    proposed_change: str
    proposed_config: Dict[str, Any]
    status: ImprovementStatus = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    applied_at: Optional[datetime] = None
    applied_by: str = "system"
    rollback_config: Optional[Dict[str, Any]] = None
    impact_score: float = 0.5



class TraceAnalysisAgent:

    def __init__(self, lookback_hours: int = 24, min_traces: int = 5):
        self.lookback_hours = lookback_hours
        self.min_traces = min_traces

    async def fetch_recent_traces(self) -> List[Dict[str, Any]]:
        try:
            from src.repositories.agent import AgentRepository
            cutoff = datetime.now(timezone.utc) - timedelta(hours=self.lookback_hours)
            traces = await AgentRepository.get_traces_since(cutoff)
            logger.info(f"TraceAnalysisAgent fetched {len(traces)} traces from last {self.lookback_hours}h")
            return traces
        except Exception as e:
            logger.exception(f"TraceAnalysisAgent failed to fetch traces {e}")
            return []

    def compute_trace_stats(self, traces: List[Dict]) -> Dict[str, Any]:
        if not traces:
            return {}

        total = len(traces)
        failed = sum(1 for t in traces if t.get("status") in ["failed", "timeout"])
        tool_failures: Dict[str, int] = {}
        security_violations = 0
        avg_duration_ms = 0
        avg_tool_calls = 0
        avg_llm_calls = 0

        for t in traces:
            security_violations += t.get("security_violations", 0)
            avg_duration_ms += t.get("total_duration_ms", 0)
            avg_tool_calls += t.get("total_tool_calls", 0)
            avg_llm_calls += t.get("total_llm_calls", 0)
            for tool_name, breakdown in t.get("tool_call_breakdown", {}).items():
                if breakdown.get("errors", 0) > 0:
                    tool_failures[tool_name] = tool_failures.get(tool_name, 0) + breakdown["errors"]

        return {
            "total_traces": total,
            "failure_rate": round(failed / total, 3) if total else 0,
            "tool_failures": tool_failures,
            "security_violations": security_violations,
            "avg_duration_ms": round(avg_duration_ms / total) if total else 0,
            "avg_tool_calls": round(avg_tool_calls / total, 1) if total else 0,
            "avg_llm_calls": round(avg_llm_calls / total, 1) if total else 0,
        }

    async def analyze_with_llm(self, stats: Dict, traces_sample: List[Dict]) -> str:
        try:
            from src.workflow.graph import llm

            sample_str = json.dumps(traces_sample[:3], default=str, indent=2)[:2000]
            stats_str = json.dumps(stats, indent=2)

            prompt = (
                f"You are an expert AI system analyst. Analyze these agent execution traces "
                f"and identify systemic issues.\n\n"
                f"Aggregate Stats:\n{stats_str}\n\n"
                f"Sample Traces:\n{sample_str}\n\n"
                f"Identify: (1) recurring tool failures, (2) prompt quality issues, "
                f"(3) routing errors, (4) hallucination patterns, (5) performance bottlenecks. "
                f"Be specific and actionable."
            )
            result = await llm.ainvoke(prompt)
            return result.content.strip()
        except Exception as e:
            logger.exception(f"TraceAnalysisAgent LLM analysis failed {e}")
            return ""



class IssueDetector:
    FAILURE_RATE_THRESHOLD = 0.15
    TOOL_FAILURE_THRESHOLD = 3
    SECURITY_VIOLATION_THRESHOLD = 5
    SLOW_DURATION_MS_THRESHOLD = 30_000

    def detect_from_stats(self, stats: Dict, traces: List[Dict]) -> List[DetectedIssue]:
        issues: List[DetectedIssue] = []

        if stats.get("failure_rate", 0) > self.FAILURE_RATE_THRESHOLD:
            issues.append(DetectedIssue(
                issue_id=str(uuid.uuid4()),
                category="prompt_quality",
                title="High Agent Failure Rate",
                description=(
                    f"Agent failure rate is {stats['failure_rate']:.1%} "
                    f"(threshold: {self.FAILURE_RATE_THRESHOLD:.1%}). "
                    f"This may indicate prompt quality issues or task routing problems."
                ),
                affected_component="workflow/orchestration",
                evidence_count=int(stats["failure_rate"] * stats["total_traces"]),
                severity="high" if stats["failure_rate"] > 0.3 else "medium",
                example_session_ids=[t.get("session_id", "") for t in traces[:3] if t.get("status") == "failed"],
            ))

        for tool_name, failure_count in stats.get("tool_failures", {}).items():
            if failure_count >= self.TOOL_FAILURE_THRESHOLD:
                issues.append(DetectedIssue(
                    issue_id=str(uuid.uuid4()),
                    category="tool_failure",
                    title=f"Recurring Tool Failure: {tool_name}",
                    description=(
                        f"Tool '{tool_name}' has failed {failure_count} times in the last traces. "
                        f"This may indicate parameter issues, API timeouts, or tool misconfiguration."
                    ),
                    affected_component=f"tools/{tool_name}",
                    evidence_count=failure_count,
                    severity="critical" if failure_count > 10 else "high",
                ))

        if stats.get("security_violations", 0) >= self.SECURITY_VIOLATION_THRESHOLD:
            issues.append(DetectedIssue(
                issue_id=str(uuid.uuid4()),
                category="routing_error",
                title="Security Violation Spike",
                description=(
                    f"Detected {stats['security_violations']} security violations. "
                    f"The security prompts may need strengthening or routing rules updated."
                ),
                affected_component="harness/security",
                evidence_count=stats["security_violations"],
                severity="critical",
            ))

        if stats.get("avg_duration_ms", 0) > self.SLOW_DURATION_MS_THRESHOLD:
            issues.append(DetectedIssue(
                issue_id=str(uuid.uuid4()),
                category="timeout",
                title="High Average Response Time",
                description=(
                    f"Average response time is {stats['avg_duration_ms']}ms "
                    f"(threshold: {self.SLOW_DURATION_MS_THRESHOLD}ms). "
                    f"Consider reducing plan complexity or increasing timeouts."
                ),
                affected_component="harness/orchestration",
                evidence_count=stats["total_traces"],
                severity="medium",
            ))

        logger.info(f"IssueDetector found {len(issues)} issues from trace stats")
        return issues



class HarnessImprover:
    async def generate_suggestions(
        self, issues: List[DetectedIssue], llm_analysis: str = ""
    ) -> List[ImprovementSuggestion]:
        suggestions: List[ImprovementSuggestion] = []

        for issue in issues:
            suggestion = await self._suggest_for_issue(issue, llm_analysis)
            if suggestion:
                suggestions.append(suggestion)

        logger.info(f"HarnessImprover generated {len(suggestions)} improvement suggestions")
        return suggestions

    async def _suggest_for_issue(
        self, issue: DetectedIssue, llm_analysis: str
    ) -> Optional[ImprovementSuggestion]:
        if issue.category == "prompt_quality":
            return ImprovementSuggestion(
                improvement_id=str(uuid.uuid4()),
                issue_id=issue.issue_id,
                improvement_type="prompt_tweak",
                title=f"Improve prompt for: {issue.title}",
                description=(
                    f"The agent is failing frequently ({issue.evidence_count} times). "
                    f"Suggest adding more explicit instructions, examples, or constraints "
                    f"to the system prompt to reduce ambiguity."
                ),
                proposed_change="Add clarifying instructions and few-shot examples to BRAIN_SYSTEM prompt",
                proposed_config={
                    "prompt_type": "BRAIN_SYSTEM",
                    "action": "append_suffix",
                    "suffix": (
                        "\n\nIMPORTANT: If you are uncertain about how to proceed, "
                        "choose the Knowledge agent to gather more information before acting. "
                        "Never leave a response empty or say 'I cannot help with this'."
                    ),
                },
                impact_score=0.7,
            )

        elif issue.category == "tool_failure":
            tool_name = issue.affected_component.split("/")[-1]
            return ImprovementSuggestion(
                improvement_id=str(uuid.uuid4()),
                issue_id=issue.issue_id,
                improvement_type="tool_config",
                title=f"Fix tool configuration: {tool_name}",
                description=(
                    f"Tool '{tool_name}' is failing repeatedly. "
                    f"Suggest increasing timeout and retry count."
                ),
                proposed_change=f"Increase timeout and retries for tool '{tool_name}'",
                proposed_config={
                    "tool_name": tool_name,
                    "config_key": "timeout",
                    "action": "increase_by",
                    "value": 10.0,
                    "max_retries_action": "increase_by",
                    "max_retries_value": 1,
                },
                impact_score=0.6,
            )

        elif issue.category == "timeout":
            return ImprovementSuggestion(
                improvement_id=str(uuid.uuid4()),
                issue_id=issue.issue_id,
                improvement_type="grader_config",
                title="Reduce plan complexity threshold",
                description="High response times suggest plans are too complex. Reduce max_plan_steps.",
                proposed_change="Reduce max_plan_steps for reader role from 6 to 4",
                proposed_config={
                    "component": "governance/role_policies",
                    "role": "reader",
                    "field": "max_plan_steps",
                    "action": "set",
                    "value": 4,
                },
                impact_score=0.5,
            )

        elif issue.category == "routing_error":
            return ImprovementSuggestion(
                improvement_id=str(uuid.uuid4()),
                issue_id=issue.issue_id,
                improvement_type="prompt_tweak",
                title="Strengthen security prompt",
                description="Security violations detected. Strengthen the security scanning prompt.",
                proposed_change="Add stricter keywords to security scanner",
                proposed_config={
                    "component": "harness/security",
                    "action": "add_blocked_patterns",
                    "patterns": ["jailbreak", "ignore previous instructions", "pretend you are"],
                },
                impact_score=0.8,
            )

        return None



class PromptVersionControl:
    def __init__(self):
        self._versions: Dict[str, List[Dict]] = {}

    def snapshot(self, prompt_type: str, content: str) -> str:
        version_id = str(uuid.uuid4())[:8]
        if prompt_type not in self._versions:
            self._versions[prompt_type] = []
        self._versions[prompt_type].append({
            "version_id": version_id,
            "content": content,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"PromptVersionControl snapshotted {prompt_type} (version={version_id})")
        return version_id

    def rollback(self, prompt_type: str) -> Optional[str]:
        versions = self._versions.get(prompt_type, [])
        if len(versions) < 2:
            logger.warning(f"PromptVersionControl no previous version for {prompt_type}")
            return None
        versions.pop()
        prev = versions[-1]
        logger.info(f"PromptVersionControl rolled back {prompt_type} to version {prev['version_id']}")
        return prev["content"]

    def get_history(self, prompt_type: str) -> List[Dict]:
        return list(self._versions.get(prompt_type, []))


class PromptOptimizer:
    def __init__(self):
        self.version_control = PromptVersionControl()

    async def apply_improvement(self, suggestion: ImprovementSuggestion) -> bool:
        config = suggestion.proposed_config
        action = config.get("action")

        try:
            if suggestion.improvement_type == "prompt_tweak":
                return await self._apply_prompt_tweak(config, suggestion)
            elif suggestion.improvement_type == "tool_config":
                return await self._apply_tool_config(config, suggestion)
            elif suggestion.improvement_type == "grader_config":
                return await self._apply_grader_config(config, suggestion)
            elif suggestion.improvement_type == "routing_rule":
                return await self._apply_routing_rule(config, suggestion)
            else:
                logger.warning(f"PromptOptimizer unknown improvement type '{suggestion.improvement_type}'")
                return False
        except Exception as e:
            logger.exception(f"PromptOptimizer failed to apply improvement {suggestion.improvement_id} {e}")
            return False

    async def _apply_prompt_tweak(self, config: Dict, suggestion: ImprovementSuggestion) -> bool:
        try:
            from src.core.registry import PromptType, registry
            prompt_type_str = config.get("prompt_type", "BRAIN_SYSTEM")
            prompt_type = PromptType[prompt_type_str]
            current_content = registry.get(prompt_type)

            version_id = self.version_control.snapshot(prompt_type_str, current_content)
            suggestion.rollback_config = {"version_id": version_id, "prompt_type": prompt_type_str}

            if config.get("action") == "append_suffix":
                new_content = current_content + config.get("suffix", "")
                registry.update(prompt_type, new_content)
                logger.info(f"PromptOptimizer applied prompt suffix to {prompt_type_str} (version={version_id})")
                return True
            elif config.get("action") == "replace":
                new_content = config.get("new_content", current_content)
                registry.update(prompt_type, new_content)
                return True
        except Exception as e:
            logger.exception(f"PromptOptimizer prompt tweak failed {e}")
        return False

    async def _apply_tool_config(self, config: Dict, suggestion: ImprovementSuggestion) -> bool:
        tool_name = config.get("tool_name", "")
        logger.info(
            f"PromptOptimizer: tool config improvement for '{tool_name}' logged. "
            f"Requires manual deployment: {suggestion.proposed_change}"
        )
        return True

    async def _apply_grader_config(self, config: Dict, suggestion: ImprovementSuggestion) -> bool:
        try:
            if config.get("component") == "governance/role_policies":
                from src.harness.governance import ROLE_POLICIES
                role = config.get("role", "reader")
                field_name = config.get("field")
                value = config.get("value")
                if role in ROLE_POLICIES and field_name and value is not None:
                    ROLE_POLICIES[role][field_name] = value
                    logger.info(f"PromptOptimizer updated governance {role}.{field_name} = {value}")
                    return True
        except Exception as e:
            logger.exception(f"PromptOptimizer grader config failed {e}")
        return False

    async def _apply_routing_rule(self, config: Dict, suggestion: ImprovementSuggestion) -> bool:
        logger.info(f"PromptOptimizer routing rule change logged {suggestion.proposed_change}")
        return True

    async def rollback_improvement(self, suggestion: ImprovementSuggestion) -> bool:
        if not suggestion.rollback_config:
            logger.warning(f"PromptOptimizer no rollback config for {suggestion.improvement_id}")
            return False
        try:
            if suggestion.improvement_type == "prompt_tweak":
                from src.core.registry import PromptType, registry
                prompt_type_str = suggestion.rollback_config.get("prompt_type")
                prev_content = self.version_control.rollback(prompt_type_str)
                if prev_content:
                    prompt_type = PromptType[prompt_type_str]
                    registry.update(prompt_type, prev_content)
                    logger.info(f"PromptOptimizer rolled back {prompt_type_str}")
                    return True
        except Exception as e:
            logger.exception(f"PromptOptimizer rollback failed {e}")
        return False



class HillClimbingLoop:
    def __init__(
        self,
        auto_apply: bool = False,
        min_traces_before_analysis: int = 10,
        analysis_lookback_hours: int = 24,
    ):
        self.auto_apply = auto_apply
        self.trace_analyzer = TraceAnalysisAgent(
            lookback_hours=analysis_lookback_hours,
            min_traces=min_traces_before_analysis,
        )
        self.issue_detector = IssueDetector()
        self.harness_improver = HarnessImprover()
        self.prompt_optimizer = PromptOptimizer()

        self._detected_issues: List[DetectedIssue] = []
        self._suggestions: List[ImprovementSuggestion] = []
        self._analysis_history: List[Dict] = []
        self._lock = asyncio.Lock()

    async def analyze_and_improve(self) -> Dict[str, Any]:
        async with self._lock:
            logger.info("HillClimbingLoop starting analysis cycle")
            start = datetime.now(timezone.utc)

            traces = await self.trace_analyzer.fetch_recent_traces()
            if len(traces) < self.trace_analyzer.min_traces:
                logger.info(f"HillClimbingLoop insufficient traces ({len(traces)} < {self.trace_analyzer.min_traces}), skipping")
                return {"status": "skipped", "reason": "insufficient_traces", "traces_available": len(traces)}

            stats = self.trace_analyzer.compute_trace_stats(traces)

            llm_analysis = await self.trace_analyzer.analyze_with_llm(stats, traces[:5])

            new_issues = self.issue_detector.detect_from_stats(stats, traces)
            self._detected_issues.extend(new_issues)

            new_suggestions = await self.harness_improver.generate_suggestions(new_issues, llm_analysis)
            self._suggestions.extend(new_suggestions)

            applied = []
            if self.auto_apply:
                for suggestion in new_suggestions:
                    success = await self.prompt_optimizer.apply_improvement(suggestion)
                    suggestion.status = "applied" if success else "pending"
                    suggestion.applied_at = datetime.now(timezone.utc) if success else None
                    if success:
                        applied.append(suggestion.improvement_id)
            else:
                for suggestion in new_suggestions:
                    suggestion.status = "pending"

            duration_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
            cycle_result = {
                "status": "completed",
                "traces_analyzed": len(traces),
                "stats": stats,
                "issues_found": len(new_issues),
                "suggestions_generated": len(new_suggestions),
                "improvements_applied": len(applied),
                "pending_review": len(new_suggestions) - len(applied),
                "duration_ms": duration_ms,
                "timestamp": start.isoformat(),
            }
            self._analysis_history.append(cycle_result)
            logger.info(
                f"HillClimbingLoop: cycle complete — "
                f"{len(new_issues)} issues, {len(new_suggestions)} suggestions, "
                f"{len(applied)} applied, {duration_ms}ms"
            )
            return cycle_result

    async def approve_improvement(self, improvement_id: str, approver: str = "human") -> bool:
        suggestion = next((s for s in self._suggestions if s.improvement_id == improvement_id), None)
        if not suggestion:
            logger.warning(f"HillClimbingLoop improvement {improvement_id} not found")
            return False
        if suggestion.status != "pending":
            logger.warning(f"HillClimbingLoop improvement {improvement_id} is not pending (status={suggestion.status})")
            return False

        success = await self.prompt_optimizer.apply_improvement(suggestion)
        suggestion.status = "applied" if success else "pending"
        suggestion.applied_at = datetime.now(timezone.utc) if success else None
        suggestion.applied_by = approver
        logger.info(f"HillClimbingLoop improvement {improvement_id} {'applied' if success else 'failed'} by {approver}")
        return success

    async def reject_improvement(self, improvement_id: str) -> bool:
        suggestion = next((s for s in self._suggestions if s.improvement_id == improvement_id), None)
        if not suggestion:
            return False
        suggestion.status = "rejected"
        logger.info(f"HillClimbingLoop improvement {improvement_id} rejected")
        return True

    async def rollback_improvement(self, improvement_id: str) -> bool:
        suggestion = next((s for s in self._suggestions if s.improvement_id == improvement_id), None)
        if not suggestion or suggestion.status != "applied":
            return False
        success = await self.prompt_optimizer.rollback_improvement(suggestion)
        if success:
            suggestion.status = "rolled_back"
        return success

    def get_issues(self, limit: int = 50) -> List[Dict]:
        return [
            {
                "issue_id": i.issue_id,
                "category": i.category,
                "title": i.title,
                "description": i.description,
                "affected_component": i.affected_component,
                "evidence_count": i.evidence_count,
                "severity": i.severity,
                "first_seen_at": i.first_seen_at.isoformat(),
                "last_seen_at": i.last_seen_at.isoformat(),
            }
            for i in reversed(self._detected_issues[-limit:])
        ]

    def get_suggestions(self, status_filter: Optional[str] = None, limit: int = 50) -> List[Dict]:
        suggestions = self._suggestions
        if status_filter:
            suggestions = [s for s in suggestions if s.status == status_filter]
        return [
            {
                "improvement_id": s.improvement_id,
                "issue_id": s.issue_id,
                "improvement_type": s.improvement_type,
                "title": s.title,
                "description": s.description,
                "proposed_change": s.proposed_change,
                "status": s.status,
                "impact_score": s.impact_score,
                "created_at": s.created_at.isoformat(),
                "applied_at": s.applied_at.isoformat() if s.applied_at else None,
                "applied_by": s.applied_by,
            }
            for s in reversed(suggestions[-limit:])
        ]

    def get_analysis_history(self, limit: int = 10) -> List[Dict]:
        return list(reversed(self._analysis_history[-limit:]))

    def get_dashboard(self) -> Dict[str, Any]:
        pending = sum(1 for s in self._suggestions if s.status == "pending")
        applied = sum(1 for s in self._suggestions if s.status == "applied")
        rejected = sum(1 for s in self._suggestions if s.status == "rejected")
        return {
            "total_issues_detected": len(self._detected_issues),
            "total_suggestions": len(self._suggestions),
            "pending_review": pending,
            "applied": applied,
            "rejected": rejected,
            "analysis_cycles": len(self._analysis_history),
            "last_cycle": self._analysis_history[-1] if self._analysis_history else None,
        }


hill_climbing_loop = HillClimbingLoop(auto_apply=False)
