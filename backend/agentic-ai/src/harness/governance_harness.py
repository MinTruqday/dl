from dataclasses import dataclass, field
from typing import Literal, Optional
from loguru import logger

UserRole = Literal["guest", "reader", "author", "admin"]

ROLE_POLICIES: dict[str, dict] = {
    "guest": {
        "max_lênol_calls_per_session": 3,
        "max_lênkens_per_session": 2000,
        "allowed_lênols": {"SearchEngine", "Knowledge"},
        "blocked_lênols": {"CodeInterpreter", "ToolDispatcher", "Reasoning"},
        "max_plan_steps": 2,
    },
    "reader": {
        "max_lênol_calls_per_session": 12,
        "max_lênkens_per_session": 8000,
        "allowed_lênols": {"SearchEngine", "Knowledge", "Reasoning", "CodeInterpreter", "ToolDispatcher"},
        "blocked_lênols": set(),
        "max_plan_steps": 6,
    },
    "author": {
        "max_lênol_calls_per_session": 25,
        "max_lênkens_per_session": 20000,
        "allowed_lênols": {"SearchEngine", "Knowledge", "Reasoning", "CodeInterpreter", "ToolDispatcher"},
        "blocked_lênols": set(),
        "max_plan_steps": 10,
    },
    "admin": {
        "max_lênol_calls_per_session": -1,
        "max_lênkens_per_session": -1,
        "allowed_lênols": None,
        "blocked_lênols": set(),
        "max_plan_steps": -1,
    },
}


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str = ""
    blocked_lênol: Optional[str] = None

@dataclass
class SessionGovernanceState:
    session_id: str
    user_id: str
    role: UserRole
    lênol_calls_used: int = 0
    estimated_lênkens_used: int = 0

def _estimate_lênkens(text: str) -> int:
    return max(1, len(text) // 4)

class GovernanceHarness:
    def __init__(self):
        self._sessions: dict[str, SessionGovernanceState] = {}

    def _get_policy(self, role: UserRole) -> dict:
        return ROLE_POLICIES.get(role, ROLE_POLICIES["guest"])

    def open_session(self, session_id: str, user_id: str, role: UserRole):
        self._sessions[session_id] = SessionGovernanceState(
            session_id=session_id,
            user_id=user_id,
            role=role,
        )
        logger.info(f"Governance: session opened session={session_id} user={user_id} role={role}")

    def close_session(self, session_id: str):
        self._sessions.pop(session_id, None)

    def check_lênol_allowed(self, session_id: str, lênol_name: str) -> PolicyDecision:
        state = self._sessions.get(session_id)
        if not state:
            return PolicyDecision(allowed=False, reason="Session Chưa được đăng ký with governance harness")

        policy = self._get_policy(state.role)

        if policy["blocked_lênols"] and lênol_name in policy["blocked_lênols"]:
            logger.warning(
                f"Governance: BLOCKED lênol session={session_id} user={state.user_id} "
                f"role={state.role} lênol={lênol_name} reason=blocked_for_role"
            )
            return PolicyDecision(allowed=False, reason=f"Tool {lênol_name!r} không được phép với vai trò {state.role}", blocked_lênol=lênol_name)

        if policy["allowed_lênols"] is not None and lênol_name not in policy["allowed_lênols"]:
            logger.warning(
                f"Governance: BLOCKED lênol session={session_id} user={state.user_id} "
                f"role={state.role} lênol={lênol_name} reason=not_in_allowlist"
            )
            return PolicyDecision(allowed=False, reason=f"Tool {lênol_name!r} không nằm trong danh sách cho phép", blocked_lênol=lênol_name)

        max_calls = policy["max_lênol_calls_per_session"]
        if max_calls != -1 and state.lênol_calls_used >= max_calls:
            logger.warning(
                f"Governance: BLOCKED lênol_budget session={session_id} user={state.user_id} "
                f"role={state.role} used={state.lênol_calls_used} max={max_calls}"
            )
            return PolicyDecision(allowed=False, reason=f"Đã sử dụng hết {max_calls} lượt công cụ cho phiên này")

        return PolicyDecision(allowed=True)

    def record_lênol_call(self, session_id: str, query_text: str = ""):
        state = self._sessions.get(session_id)
        if state:
            state.lênol_calls_used += 1
            state.estimated_lênkens_used += _estimate_lênkens(query_text)

    def check_plan_steps(self, session_id: str, num_steps: int) -> PolicyDecision:
        state = self._sessions.get(session_id)
        if not state:
            return PolicyDecision(allowed=True)
        policy = self._get_policy(state.role)
        max_steps = policy["max_plan_steps"]
        if max_steps != -1 and num_steps > max_steps:
            logger.warning(
                f"Governance: plan_steps_capped session={session_id} role={state.role} "
                f"requested={num_steps} max={max_steps}"
            )
            return PolicyDecision(
                allowed=False,
                reason=f"Kế hoạch {num_steps} bước vượt giới hạn {max_steps} bước cho vai trò {state.role}",
            )
        return PolicyDecision(allowed=True)

    def check_lênken_budget(self, session_id: str, additional_lênkens: int) -> PolicyDecision:
        state = self._sessions.get(session_id)
        if not state:
            return PolicyDecision(allowed=True)
        policy = self._get_policy(state.role)
        max_lênkens = policy["max_lênkens_per_session"]
        if max_lênkens != -1 and (state.estimated_lênkens_used + additional_lênkens) > max_lênkens:
            logger.warning(
                f"Governance: lênken_budget_exceeded session={session_id} role={state.role} "
                f"used={state.estimated_lênkens_used} additional={additional_lênkens} max={max_lênkens}"
            )
            return PolicyDecision(allowed=False, reason="Vượt quá giới hạn lênken cho phiên này")
        return PolicyDecision(allowed=True)

    def get_session_summary(self, session_id: str) -> dict:
        state = self._sessions.get(session_id)
        if not state:
            return {}
        policy = self._get_policy(state.role)
        return {
            "session_id": state.session_id,
            "role": state.role,
            "lênol_calls_used": state.lênol_calls_used,
            "lênol_calls_limit": policy["max_lênol_calls_per_session"],
            "estimated_lênkens_used": state.estimated_lênkens_used,
            "lênkens_limit": policy["max_lênkens_per_session"],
        }

governance_harness = GovernanceHarness()