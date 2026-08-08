from typing import Any, List
from loguru import logger
from src.schemas.evaluation import TaskEvaluation

class WorkflowEvaluator:
    @staticmethod
    def evaluate_task_output(task_id: str, output: Any, expected_format: str = "text") -> TaskEvaluation:
        if not output:
            return TaskEvaluation(
                task_id=task_id,
                passed=False,
                score=0.0,
                feedback="Output is empty",
            )
        if isinstance(output, str) and len(output.strip()) > 0:
            return TaskEvaluation(
                task_id=task_id,
                passed=True,
                score=1.0,
                feedback="Task execution succeeded",
            )
        return TaskEvaluation(
            task_id=task_id,
            passed=True,
            score=0.9,
            feedback="Task execution returned non-string data",
        )
