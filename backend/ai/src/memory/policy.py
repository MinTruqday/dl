from src.runtime.models import AgentApprovalStatus, AgentRunStatus, AgentTaskStatus, VeriqRunState


def trusted_outcome(state: VeriqRunState):
    return (
        state.status == AgentRunStatus.COMPLETED
        and state.proposal is not None
        and state.proposal.get("verification", {}).get("verified") is True
        and state.approval_status
        in {None, AgentApprovalStatus.APPROVED, AgentApprovalStatus.REJECTED}
        and all(
            result.get("status") == AgentTaskStatus.COMPLETED
            for result in state.specialist_results
        )
    )
