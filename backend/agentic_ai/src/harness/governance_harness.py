from dataclasses import dataclass, field
from typing import Literal, Optional
from loguru import logger

UserRole = Literal["guest", "reader", "author", "admin"]

ROLE_POLICIES: dict[str, dict] = {
    "guest": {"max_tool_calls_per_session": 3, "max_tokens_per_session": 2000, "allowed_tools": {"SearchEngine", "Knowledge"}, "blocked_tools": {"CodeInterpreter", "Action", "Reasoning"}, "max_plan_steps": 2},
    "reader": {"max_tool_calls_per_session": 12, "max_tokens_per_session": 8000, "allowed_tools": {"SearchEngine", "Knowledge", "Reasoning", "CodeInterpreter", "Action"}, "blocked_tools": set(), "max_plan_steps": 6},
    "author": {"max_tool_calls_per_session": 25, "max_tokens_per_session": 20000, "allowed_tools": {"SearchEngine", "Knowledge", "Reasoning", "CodeInterpreter", "Action"}, "blocked_tools": set(), "max_plan_steps": 10},
    "admin": {"max_tool_calls_per_session": -1, "max_tokens_per_session": -1, "allowed_tools": None, "blocked_tools": set(), "max_plan_steps": -1},
}

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str = ""
    blocked_tool: Optional[str] = None

@dataclass
class SessionGovernanceState:
    session_id: str
    user_id: str
    role: UserRole
    tool_calls_used: int = 0
    estimated_tokens_used: int = 0

def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)

class GovernanceHarness:
    def __init__(self):
        self._sessions: dict[str, SessionGovernanceState] = {}

    def _get_policy(self, role: UserRole) -> dict:
        return ROLE_POLICIES.get(role, ROLE_POLICIES["guest"])

    def open_session(self, session_id: str, user_id: str, role: UserRole):
        self._sessions[session_id] = SessionGovernanceState(session_id=session_id, user_id=user_id, role=role)
        logger.info("The organizational governance access control framework systematically authorized managing new actively operational authenticated dynamic tracking session")

    def close_session(self, session_id: str):
        self._sessions.pop(session_id, None)

    def check_tool_allowed(self, session_id: str, tool_name: str) -> PolicyDecision:
        state = self._sessions.get(session_id)
        if not state:
            return PolicyDecision(allowed=False, reason="The designated operational execution session technically circumvented active administrative governance systematic explicit validation security arrays")
        policy = self._get_policy(state.role)
        if policy["blocked_tools"] and tool_name in policy["blocked_tools"]:
            logger.warning("The operational dynamic governance logic decisively suspended requested system invocation matching missing authorization parameters")
            return PolicyDecision(allowed=False, reason="The requested active operation currently requires elevated authenticated security clearances absolutely unavailable bypassing operational authorization", blocked_tool=tool_name)
        if policy["allowed_tools"] is not None and tool_name not in policy["allowed_tools"]:
            logger.warning("The operational dynamic governance logic decisively suspended requested system invocation matching missing authorization parameters")
            return PolicyDecision(allowed=False, reason="The precisely targeted execution module completely lacks essential whitelisting permissions tracking current authenticated processing constraints", blocked_tool=tool_name)
        max_calls = policy["max_tool_calls_per_session"]
        if max_calls != -1 and state.tool_calls_used >= max_calls:
            logger.warning("The governance diagnostic module blocked active routing exceeding maximum explicit processing limitations defined logically")
            return PolicyDecision(allowed=False, reason="The processing execution array strictly exceeded globally mapped active functional algorithmic invocations operational structural limits")
        return PolicyDecision(allowed=True)

    def record_tool_call(self, session_id: str, query_text: str = ""):
        state = self._sessions.get(session_id)
        if state:
            state.tool_calls_used += 1
            state.estimated_tokens_used += _estimate_tokens(query_text)

    def check_plan_steps(self, session_id: str, num_steps: int) -> PolicyDecision:
        state = self._sessions.get(session_id)
        if not state:
            return PolicyDecision(allowed=True)
        policy = self._get_policy(state.role)
        max_steps = policy["max_plan_steps"]
        if max_steps != -1 and num_steps > max_steps:
            logger.warning("The governance diagnostic module blocked active routing exceeding maximum explicit processing limitations defined logically")
            return PolicyDecision(allowed=False, reason="The evaluated dynamic execution logic fundamentally exceeds explicitly mapped complex authorization systematic parameters permitted currently")
        return PolicyDecision(allowed=True)

    def check_token_budget(self, session_id: str, additional_tokens: int) -> PolicyDecision:
        state = self._sessions.get(session_id)
        if not state:
            return PolicyDecision(allowed=True)
        policy = self._get_policy(state.role)
        max_tokens = policy["max_tokens_per_session"]
        if max_tokens != -1 and (state.estimated_tokens_used + additional_tokens) > max_tokens:
            logger.warning("The governance diagnostic module blocked active routing exceeding maximum explicit processing limitations defined logically")
            return PolicyDecision(allowed=False, reason="The explicitly evaluated active processing algorithmic network session aggressively surpassed mapped permitted total memory boundaries")
        return PolicyDecision(allowed=True)

    def get_session_summary(self, session_id: str) -> dict:
        state = self._sessions.get(session_id)
        if not state:
            return {}
        policy = self._get_policy(state.role)
        return {"session_id": state.session_id, "role": state.role, "tool_calls_used": state.tool_calls_used, "tool_calls_limit": policy["max_tool_calls_per_session"], "estimated_tokens_used": state.estimated_tokens_used, "tokens_limit": policy["max_tokens_per_session"]}

governance_harness = GovernanceHarness()