from src.runtime.models import VeriqRunState


def trusted_outcome(state: VeriqRunState):
    return (
        state.status == "COMPLETED"
        and state.proposal is not None
        and state.proposal.get("verification", {}).get("verified") is True
        and state.approval_status in {None, "APPROVED", "REJECTED"}
        and all(
            result.get("status") == "COMPLETED" for result in state.specialist_results
        )
    )
