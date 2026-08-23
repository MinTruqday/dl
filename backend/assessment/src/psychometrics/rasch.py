import math


def estimate_item_parameter(
    correct: int,
    total: int,
    ability_estimates: list[float] | None = None,
    observed_scores: list[float] | None = None,
):
    if total <= 0:
        raise ValueError("Cần dữ liệu phản hồi")
    probability = (correct + 0.5) / (total + 1)
    item_b = -math.log(probability / (1 - probability))
    standard_error = math.sqrt(1 / (total * probability * (1 - probability)))
    difficulty = max(1.0, min(5.0, 3 + item_b))
    result = {
        "difficulty": round(difficulty, 4),
        "irt_b": round(item_b, 4),
        "standard_error": round(standard_error, 4),
        "sample_size": total,
    }
    if (
        ability_estimates
        and observed_scores
        and len(ability_estimates) == total
        and len(observed_scores) == total
    ):
        expected = [1 / (1 + math.exp(-(theta - item_b))) for theta in ability_estimates]
        variances = [max(probability * (1 - probability), 1e-6) for probability in expected]
        residuals = [
            (value - probability) ** 2 for value, probability in zip(observed_scores, expected)
        ]
        outfit = (
            sum(residual / variance for residual, variance in zip(residuals, variances)) / total
        )
        infit = sum(residuals) / sum(variances)
        result.update(
            {
                "infit_mnsq": round(infit, 4),
                "outfit_mnsq": round(outfit, 4),
                "item_fit_status": "productive"
                if 0.7 <= infit <= 1.3 and 0.7 <= outfit <= 1.3
                else "review",
            }
        )
    else:
        result.update(
            {"infit_mnsq": None, "outfit_mnsq": None, "item_fit_status": "insufficient_context"}
        )
    return result
