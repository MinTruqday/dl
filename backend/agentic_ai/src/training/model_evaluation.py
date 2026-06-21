import math
from collections import Counter

from loguru import logger
from src.harness.evaluation import (
    EvalReport,
    EvaluationHarness,
    _compute_bleu,
    _compute_rouge_l,
    _llm_judge,
    evaluation,
)


async def llm_judge_score(
    instruction: str,
    expected: str,
    actual: str,
    hf_token: str = "",
    judge_model: str = "",
) -> dict:
    return await _llm_judge(instruction, expected, actual)


async def evaluate_model_full(
    test_samples: list,
    model_name: str,
    hf_token: str = None,
    judge_model: str = None,
) -> dict:
    use_judge = bool(judge_model)
    harness = EvaluationHarness()
    harness._dataset = test_samples
    return await harness.run_benchmark(model_name=model_name, use_judge=use_judge)


def compute_bleu(reference: str, hypothesis: str, max_n: int = 4) -> float:
    return _compute_bleu(reference, hypothesis, max_n)


def compute_rouge_l(reference: str, hypothesis: str) -> float:
    return _compute_rouge_l(reference, hypothesis)
