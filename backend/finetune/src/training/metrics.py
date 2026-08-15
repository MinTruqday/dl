import math
from collections import Counter

from src.core.models import generate_text


def compute_bleu(reference: str, hypothesis: str, max_n: int = 4) -> float:
    reference_tokens = reference.lower().split()
    hypothesis_tokens = hypothesis.lower().split()
    if not reference_tokens or not hypothesis_tokens:
        return 0.0
    penalty = min(
        1.0,
        math.exp(1 - len(reference_tokens) / max(len(hypothesis_tokens), 1)),
    )
    precisions = []
    for size in range(1, max_n + 1):
        reference_ngrams = Counter(
            tuple(reference_tokens[index : index + size])
            for index in range(len(reference_tokens) - size + 1)
        )
        hypothesis_ngrams = Counter(
            tuple(hypothesis_tokens[index : index + size])
            for index in range(len(hypothesis_tokens) - size + 1)
        )
        matched = sum(
            min(count, reference_ngrams[ngram])
            for ngram, count in hypothesis_ngrams.items()
        )
        precisions.append(matched / max(sum(hypothesis_ngrams.values()), 1))
    if any(score == 0 for score in precisions):
        return 0.0
    return penalty * math.exp(sum(math.log(score) for score in precisions) / max_n)


def compute_rouge_l(reference: str, hypothesis: str) -> float:
    left, right = reference.lower().split(), hypothesis.lower().split()
    if not left or not right:
        return 0.0
    table = [[0] * (len(right) + 1) for _ in range(len(left) + 1)]
    for row in range(1, len(left) + 1):
        for column in range(1, len(right) + 1):
            table[row][column] = (
                table[row - 1][column - 1] + 1
                if left[row - 1] == right[column - 1]
                else max(table[row - 1][column], table[row][column - 1])
            )
    common = table[-1][-1]
    precision, recall = common / len(right), common / len(left)
    return 2 * precision * recall / max(precision + recall, 1e-12)


async def evaluate_samples(samples: list[dict], model: str) -> dict:
    results = []
    for sample in samples:
        prompt = "\n".join(
            value
            for value in (sample.get("instruction", ""), sample.get("input", ""))
            if value
        )
        actual = await generate_text(prompt, model)
        expected = sample.get("output", "")
        results.append(
            {
                "instruction": sample.get("instruction", ""),
                "expected": expected,
                "actual": actual,
                "bleu": round(compute_bleu(expected, actual), 4),
                "rouge_l": round(compute_rouge_l(expected, actual), 4),
            }
        )
    return {
        "model": model,
        "total_samples": len(results),
        "average_bleu": round(
            sum(item["bleu"] for item in results) / max(len(results), 1), 4
        ),
        "average_rouge_l": round(
            sum(item["rouge_l"] for item in results) / max(len(results), 1), 4
        ),
        "results": results,
    }
