from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException
from loguru import logger

from src.harness.hill_climbing import hill_climbing_loop

router = APIRouter(prefix="/hill-climbing", tags=["Loop 4 - Hill Climbing"])

@router.get("/dashboard")
async def get_dashboard():
    return hill_climbing_loop.get_dashboard()

@router.get("/issues")
async def get_issues(limit: int = 50):
    return {
        "issues": hill_climbing_loop.get_issues(limit=limit),
    }

@router.get("/improvements")
async def get_improvements(status: Optional[str] = None, limit: int = 50):
    return {
        "improvements": hill_climbing_loop.get_suggestions(
            status_filter=status, limit=limit
        ),
    }

@router.post("/improvements/{improvement_id}/approve")
async def approve_improvement(improvement_id: str, approver: str = "admin"):
    success = await hill_climbing_loop.approve_improvement(improvement_id, approver=approver)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Improvement {improvement_id} could not be approved. Check status and existence."
        )
    return {
        "status": "approved_and_applied",
        "improvement_id": improvement_id,
        "applied_by": approver,
    }

@router.post("/improvements/{improvement_id}/reject")
async def reject_improvement(improvement_id: str):
    success = await hill_climbing_loop.reject_improvement(improvement_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Improvement {improvement_id} not found"
        )
    return {
        "status": "rejected",
        "improvement_id": improvement_id,
    }

@router.post("/improvements/{improvement_id}/rollback")
async def rollback_improvement(improvement_id: str):
    success = await hill_climbing_loop.rollback_improvement(improvement_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Improvement {improvement_id} could not be rolled back. It may not be applied or lacks rollback config."
        )
    return {
        "status": "rolled_back",
        "improvement_id": improvement_id,
    }

@router.post("/run")
async def run_analysis():
    logger.info("Hill climbing analysis triggered manually via API")
    result = await hill_climbing_loop.analyze_and_improve()
    return result

@router.get("/history")
async def get_analysis_history(limit: int = 10):
    return {
        "history": hill_climbing_loop.get_analysis_history(limit=limit),
    }

@router.get("/config")
async def get_config():
    return {
        "auto_apply": hill_climbing_loop.auto_apply,
        "min_traces_before_analysis": hill_climbing_loop.trace_analyzer.min_traces,
        "analysis_lookback_hours": hill_climbing_loop.trace_analyzer.lookback_hours,
        "issue_thresholds": {
            "failure_rate": hill_climbing_loop.issue_detector.FAILURE_RATE_THRESHOLD,
            "tool_failures": hill_climbing_loop.issue_detector.TOOL_FAILURE_THRESHOLD,
            "security_violations": hill_climbing_loop.issue_detector.SECURITY_VIOLATION_THRESHOLD,
            "slow_duration_ms": hill_climbing_loop.issue_detector.SLOW_DURATION_MS_THRESHOLD,
        },
    }

@router.patch("/config")
async def update_config(
    auto_apply: Optional[bool] = Body(default=None),
    min_traces: Optional[int] = Body(default=None),
    lookback_hours: Optional[int] = Body(default=None),
):
    if auto_apply is not None:
        hill_climbing_loop.auto_apply = auto_apply
    if min_traces is not None:
        hill_climbing_loop.trace_analyzer.min_traces = min_traces
    if lookback_hours is not None:
        hill_climbing_loop.trace_analyzer.lookback_hours = lookback_hours
    return {
        "status": "updated",
        "auto_apply": hill_climbing_loop.auto_apply,
        "min_traces": hill_climbing_loop.trace_analyzer.min_traces,
        "lookback_hours": hill_climbing_loop.trace_analyzer.lookback_hours,
    }
