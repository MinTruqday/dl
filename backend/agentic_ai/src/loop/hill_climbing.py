

import asyncio
import json
from uuid6 import uuid7
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from loguru import logger
from pydantic import BaseModel, Field


IssueCategory = Literal[
    "execution_failure",
    "prompt_quality",
    "tool_failure",
    "grader_too_strict",
    "grader_too_lenient",
    "timeout",
    "hallucination",
    "routing_error",
    "security_violation",
    "performance",
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


class ImprovementProposal(BaseModel):
    issue_id: str
    improvement_type: Literal[
        "prompt_tweak",
        "tool_config",
        "grader_config",
        "routing_rule",
    ]
    title: str
    description: str
    proposed_change: str
    proposed_config: Dict[str, Any] = Field(default_factory=dict)
    impact_score: float = Field(ge=0.0, le=1.0)


class ImprovementProposalBatch(BaseModel):
    proposals: List[ImprovementProposal] = Field(default_factory=list)



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
            logger.exception("TraceAnalysisAgent failed to fetch traces")
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

            from src.core.registry import registry, PromptType
            prompt = registry.get(PromptType.TRACE_ANALYSIS).format(
                stats_str=stats_str, sample_str=sample_str
            )
            result = await llm.ainvoke(prompt)
            return result.content.strip()
        except Exception as e:
            logger.exception("TraceAnalysisAgent LLM analysis failed")
            return ""



class IssueDetector:
    def __init__(self):
        from src.core.infrastructure.configuration import settings

        self.FAILURE_RATE_THRESHOLD = settings.AGENT_FAILURE_RATE_THRESHOLD
        self.TOOL_FAILURE_THRESHOLD = settings.AGENT_TOOL_FAILURE_THRESHOLD
        self.SECURITY_VIOLATION_THRESHOLD = (
            settings.AGENT_SECURITY_VIOLATION_THRESHOLD
        )
        self.SLOW_DURATION_MS_THRESHOLD = (
            settings.AGENT_SLOW_DURATION_MS_THRESHOLD
        )

    def detect_from_stats(self, stats: Dict, traces: List[Dict]) -> List[DetectedIssue]:
        issues: List[DetectedIssue] = []

        if stats.get("failure_rate", 0) > self.FAILURE_RATE_THRESHOLD:
            issues.append(DetectedIssue(
                issue_id=str(uuid7()),
                category="execution_failure",
                title="high_agent_failure_rate",
                description=json.dumps(
                    {
                        "failure_rate": stats["failure_rate"],
                        "threshold": self.FAILURE_RATE_THRESHOLD,
                    }
                ),
                affected_component="workflow/orchestration",
                evidence_count=int(stats["failure_rate"] * stats["total_traces"]),
                severity="high" if stats["failure_rate"] > 0.3 else "medium",
                example_session_ids=[t.get("session_id", "") for t in traces[:3] if t.get("status") == "failed"],
            ))

        for tool_name, failure_count in stats.get("tool_failures", {}).items():
            if failure_count >= self.TOOL_FAILURE_THRESHOLD:
                issues.append(DetectedIssue(
                    issue_id=str(uuid7()),
                    category="tool_failure",
                    title="recurring_tool_failure",
                    description=json.dumps(
                        {
                            "tool_name": tool_name,
                            "failure_count": failure_count,
                            "threshold": self.TOOL_FAILURE_THRESHOLD,
                        }
                    ),
                    affected_component=f"tools/{tool_name}",
                    evidence_count=failure_count,
                    severity="critical" if failure_count > 10 else "high",
                ))

        if stats.get("security_violations", 0) >= self.SECURITY_VIOLATION_THRESHOLD:
            issues.append(DetectedIssue(
                issue_id=str(uuid7()),
                category="security_violation",
                title="security_violation_spike",
                description=json.dumps(
                    {
                        "violation_count": stats["security_violations"],
                        "threshold": self.SECURITY_VIOLATION_THRESHOLD,
                    }
                ),
                affected_component="harness/security",
                evidence_count=stats["security_violations"],
                severity="critical",
            ))

        if stats.get("avg_duration_ms", 0) > self.SLOW_DURATION_MS_THRESHOLD:
            issues.append(DetectedIssue(
                issue_id=str(uuid7()),
                category="performance",
                title="high_average_response_time",
                description=json.dumps(
                    {
                        "average_duration_ms": stats["avg_duration_ms"],
                        "threshold_ms": self.SLOW_DURATION_MS_THRESHOLD,
                    }
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
        if not issues:
            return []

        try:
            from src.core.registry import PromptType, registry
            from src.workflow.graph import llm

            issue_payload = [
                {
                    "issue_id": issue.issue_id,
                    "category": issue.category,
                    "affected_component": issue.affected_component,
                    "evidence_count": issue.evidence_count,
                    "severity": issue.severity,
                    "example_session_ids": issue.example_session_ids,
                }
                for issue in issues
            ]
            prompt = registry.get(PromptType.HARNESS_IMPROVEMENT).format(
                issues=json.dumps(issue_payload, default=str),
                analysis=llm_analysis,
            )
            model = llm.with_structured_output(ImprovementProposalBatch)
            result = await model.ainvoke(prompt)
            valid_issue_ids = {issue.issue_id for issue in issues}
            suggestions = [
                ImprovementSuggestion(
                    improvement_id=str(uuid7()),
                    issue_id=proposal.issue_id,
                    improvement_type=proposal.improvement_type,
                    title=proposal.title,
                    description=proposal.description,
                    proposed_change=proposal.proposed_change,
                    proposed_config=proposal.proposed_config,
                    impact_score=proposal.impact_score,
                )
                for proposal in result.proposals
                if proposal.issue_id in valid_issue_ids
            ]
            logger.info(
                f"HarnessImprover generated {len(suggestions)} improvement suggestions"
            )
            return suggestions
        except Exception:
            logger.exception("Harness improvement proposal generation failed")
            return []



class PromptVersionControl:
    def __init__(self):
        self._versions: Dict[str, List[Dict]] = {}

    def snapshot(self, prompt_type: str, content: str) -> str:
        version_id = str(uuid7())[:8]
        if prompt_type not in self._versions:
            self._versions[prompt_type] = []
        self._versions[prompt_type].append({
            "version_id": version_id,
            "content": content,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"PromptVersionControl snapshotted {prompt_type} (version={version_id})")
        return version_id

    def restore(self, prompt_type: str, version_id: str) -> Optional[str]:
        versions = self._versions.get(prompt_type, [])
        for index in range(len(versions) - 1, -1, -1):
            version = versions[index]
            if version["version_id"] == version_id:
                del versions[index:]
                logger.info(
                    f"PromptVersionControl restored {prompt_type} to version {version_id}"
                )
                return version["content"]
        logger.warning(
            f"PromptVersionControl version {version_id} not found for {prompt_type}"
        )
        return None

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
            logger.exception(f"PromptOptimizer failed to apply improvement {suggestion.improvement_id}")
            return False

    async def _apply_prompt_tweak(self, config: Dict, suggestion: ImprovementSuggestion) -> bool:
        try:
            from src.core.registry import PromptType, registry
            prompt_type_str = config.get("prompt_type")
            if not prompt_type_str or prompt_type_str not in PromptType.__members__:
                return False
            prompt_type = PromptType[prompt_type_str]
            current_content = registry.get_base(prompt_type)

            if config.get("action") == "append_suffix":
                suffix = config.get("suffix", "")
                if not suffix:
                    return False
                new_content = current_content + suffix
            elif config.get("action") == "replace":
                new_content = config.get("new_content")
                if not new_content:
                    return False
            else:
                return False

            version_id = self.version_control.snapshot(
                prompt_type_str,
                current_content,
            )
            suggestion.rollback_config = {
                "version_id": version_id,
                "prompt_type": prompt_type_str,
            }
            registry.update(prompt_type, new_content)
            logger.info(
                f"PromptOptimizer updated {prompt_type_str} version={version_id}"
            )
            return True
        except Exception as e:
            logger.exception("PromptOptimizer prompt tweak failed")
        return False

    async def _apply_tool_config(self, config: Dict, suggestion: ImprovementSuggestion) -> bool:
        tool_name = config.get("tool_name", "")
        logger.info(
            f"PromptOptimizer: tool config improvement for '{tool_name}' logged. "
            f"Requires manual deployment: {suggestion.proposed_change}"
        )
        return False

    async def _apply_grader_config(self, config: Dict, suggestion: ImprovementSuggestion) -> bool:
        try:
            if config.get("component") == "governance/role_policies":
                from src.harness.governance import ROLE_POLICIES
                role = config.get("role")
                field_name = config.get("field")
                value = config.get("value")
                if (
                    config.get("action") == "set"
                    and role in ROLE_POLICIES
                    and field_name in ROLE_POLICIES[role]
                    and isinstance(value, (int, float, bool))
                ):
                    ROLE_POLICIES[role][field_name] = value
                    logger.info(f"PromptOptimizer updated governance {role}.{field_name} = {value}")
                    return True
        except Exception as e:
            logger.exception("PromptOptimizer grader config failed")
        return False

    async def _apply_routing_rule(self, config: Dict, suggestion: ImprovementSuggestion) -> bool:
        logger.info(f"PromptOptimizer routing rule change logged {suggestion.proposed_change}")
        return False

    async def rollback_improvement(self, suggestion: ImprovementSuggestion) -> bool:
        if not suggestion.rollback_config:
            logger.warning(f"PromptOptimizer no rollback config for {suggestion.improvement_id}")
            return False
        try:
            if suggestion.improvement_type == "prompt_tweak":
                from src.core.registry import PromptType, registry
                prompt_type_str = suggestion.rollback_config.get("prompt_type")
                version_id = suggestion.rollback_config.get("version_id")
                prev_content = self.version_control.restore(
                    prompt_type_str,
                    version_id,
                )
                if prev_content:
                    prompt_type = PromptType[prompt_type_str]
                    registry.update(prompt_type, prev_content)
                    logger.info(f"PromptOptimizer rolled back {prompt_type_str}")
                    return True
        except Exception as e:
            logger.exception("PromptOptimizer rollback failed")
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
