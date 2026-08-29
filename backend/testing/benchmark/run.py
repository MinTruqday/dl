import json
from pathlib import Path

from src.api.api_artifacts import lexical_similarity
from src.services.change_analysis import classify_test_impact, semantic_changes
from src.services.linters import duplicate_score


ROOT = Path(__file__).parent
VERSIONS = {
    "provider": "deterministic",
    "model": "agentic-hybrid-v1",
    "prompt_version": "qa-v1",
    "tool_schema_version": "1",
    "retrieval_version": "project-filter-v1",
}


def labels(sample):
    task = sample["task"]
    value = sample["input"]
    if task == "semantic_diff":
        return {item["type"] for item in semantic_changes(value["before"], value["after"])}
    if task == "impact_analysis":
        changes = semantic_changes(value["before"], value["after"])
        return {
            item["id"]
            for item in value["tests"]
            if classify_test_impact(
                {
                    "_id": item["id"],
                    "test_case_id": item["id"],
                    "test_case_key": item["key"],
                    "plain_text_projection": item["text"],
                },
                changes,
                item.get("direct_trace", False),
            )["classification"]
            != "STILL_VALID"
        }
    if task == "trace_recovery":
        return {
            item["id"]
            for item in value["tests"]
            if lexical_similarity(value["requirement"], item["text"]) >= value["threshold"]
        }
    if task == "duplicate_detection":
        score, _ = duplicate_score(value["left"], value["right"])
        return {"duplicate"} if score >= value["threshold"] else set()
    if task == "test_generation":
        supported = {"happy_path", "negative", "boundary", "validation"}
        return set(value["requested_categories"]) & supported
    raise ValueError(f"Unknown benchmark task {task}")


def score(predicted, expected):
    true_positive = len(predicted & expected)
    precision = true_positive / len(predicted) if predicted else int(not expected)
    recall = true_positive / len(expected) if expected else int(not predicted)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def evaluate_all():
    results = []
    for path in sorted(ROOT.glob("*/samples.json")):
        for sample in json.loads(path.read_text(encoding="utf-8")):
            predicted = labels(sample)
            expected = set(sample["ground_truth"]["labels"])
            results.append(
                {
                    "id": sample["id"],
                    "task": sample["task"],
                    "tags": sample["tags"],
                    "predicted": sorted(predicted),
                    "expected": sorted(expected),
                    **score(predicted, expected),
                }
            )
    aggregate = {
        metric: round(sum(item[metric] for item in results) / len(results), 4)
        for metric in ["precision", "recall", "f1"]
    }
    return {"versions": VERSIONS, "aggregate": aggregate, "samples": results}


if __name__ == "__main__":
    print(json.dumps(evaluate_all(), ensure_ascii=False, indent=2))
