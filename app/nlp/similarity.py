import math


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimensions")

    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return sum(left_value * right_value for left_value, right_value in zip(left, right)) / (
        left_norm * right_norm
    )


def normalize_cosine(value: float) -> float:
    return max(0.0, min(1.0, (value + 1.0) / 2.0))
