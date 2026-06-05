import httpx
from loguru import logger
from collections import Counter
import math


def compute_bleu(reference: str, hypothesis: str, max_n: int = 4) -> float:
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()
    if not ref_tokens or not hyp_tokens:
        return 0.0

    brevity_penalty = min(1.0, math.exp(1 - len(ref_tokens) / max(len(hyp_tokens), 1)))
    precisions = []
    for n in range(1, max_n + 1):
        ref_ngrams = Counter(tuple(ref_tokens[i:i + n]) for i in range(len(ref_tokens) - n + 1))
        hyp_ngrams = Counter(tuple(hyp_tokens[i:i + n]) for i in range(len(hyp_tokens) - n + 1))
        clipped = sum(min(hyp_ngrams[ng], ref_ngrams[ng]) for ng in hyp_ngrams)
        total = max(sum(hyp_ngrams.values()), 1)
        precisions.append(clipped / total)

    if any(p == 0 for p in precisions):
        return 0.0

    log_avg = sum(math.log(p) for p in precisions) / len(precisions)
    return brevity_penalty * math.exp(log_avg)


def compute_rouge_l(reference: str, hypothesis: str) -> float:
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()
    if not ref_tokens or not hyp_tokens:
        return 0.0

    m, n = len(ref_tokens), len(hyp_tokens)
    lcs_table = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_tokens[i - 1] == hyp_tokens[j - 1]:
                lcs_table[i][j] = lcs_table[i - 1][j - 1] + 1
            else:
                lcs_table[i][j] = max(lcs_table[i - 1][j], lcs_table[i][j - 1])

    lcs_len = lcs_table[m][n]
    precision = lcs_len / n if n > 0 else 0
    recall = lcs_len / m if m > 0 else 0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


from huggingface_hub import AsyncInferenceClient

async def llm_judge_score(
    instruction: str, expected: str, actual: str,
    hf_token: str, judge_model: str
) -> dict:
    judge_prompt = (
        "You are an expert evaluator. Score the AI response compared to the expected answer.\n"
        "Criteria: accuracy (0-10), completeness (0-10), relevance (0-10).\n"
        "Return ONLY a JSON object: {\"accuracy\": N, \"completeness\": N, \"relevance\": N, \"explanation\": \"text\"}\n\n"
        f"Question: {instruction}\n\n"
        f"Expected Answer: {expected}\n\n"
        f"AI Response: {actual}\n\n"
        "JSON Score:"
    )

    try:
        client = AsyncInferenceClient(model=judge_model, token=hf_token)
        messages = [{"role": "user", "content": judge_prompt}]
        resp = await client.chat_completion(messages=messages, max_tokens=256, temperature=0.1)
        raw = resp.choices[0].message.content.strip()

        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]

        import json
        scores = json.loads(raw.strip())
        return {
            "accuracy": min(max(scores.get("accuracy", 0), 0), 10),
            "completeness": min(max(scores.get("completeness", 0), 0), 10),
            "relevance": min(max(scores.get("relevance", 0), 0), 10),
            "explanation": scores.get("explanation", ""),
        }
    except Exception as e:
        logger.warning(f"LLM judge failed: {e}")
        return {"accuracy": 0, "completeness": 0, "relevance": 0, "explanation": f"Judge error: {e}"}


async def evaluate_model_full(
    test_samples: list, model_name: str,
    hf_token: str = None, judge_model: str = None
) -> dict:
    results = []
    
    try:
        client = AsyncInferenceClient(model=model_name, token=hf_token)
    except Exception as e:
        return {"error": f"Failed to init client: {e}"}

    for s in test_samples:
        ins = s.get("instruction", "")
        inp = s.get("input", "")
        exp = s.get("output", "")
        prompt = f"{ins}\n{inp}".strip()

        try:
            messages = [{"role": "user", "content": prompt}]
            resp = await client.chat_completion(messages=messages, max_tokens=512, temperature=0.1)
            actual = resp.choices[0].message.content.strip()
        except Exception as e:
            results.append({
                "instruction": ins, "input": inp, "expected": exp,
                "actual": f"Error: {e}",
                "bleu": 0, "rouge_l": 0, "judge_scores": None
            })
            continue

        bleu = round(compute_bleu(exp, actual), 4)
        rouge = round(compute_rouge_l(exp, actual), 4)

        judge_scores = None
        if judge_model:
            judge_scores = await llm_judge_score(ins, exp, actual, hf_token, judge_model)

        results.append({
            "instruction": ins, "input": inp, "expected": exp, "actual": actual,
            "bleu": bleu, "rouge_l": rouge, "judge_scores": judge_scores
        })

    avg_bleu = sum(r["bleu"] for r in results) / len(results) if results else 0
    avg_rouge = sum(r["rouge_l"] for r in results) / len(results) if results else 0

    avg_judge = None
    judge_results = [r["judge_scores"] for r in results if r.get("judge_scores")]
    if judge_results:
        avg_judge = {
            "accuracy": round(sum(j["accuracy"] for j in judge_results) / len(judge_results), 2),
            "completeness": round(sum(j["completeness"] for j in judge_results) / len(judge_results), 2),
            "relevance": round(sum(j["relevance"] for j in judge_results) / len(judge_results), 2),
        }

    return {
        "results": results,
        "average_bleu": round(avg_bleu, 4),
        "average_rouge_l": round(avg_rouge, 4),
        "average_judge_scores": avg_judge,
        "total_samples": len(results),
    }
