from datetime import datetime, timedelta, timezone


def normalize_delivery_policy(policy: dict):
    allowed = {
        "delivery_mode",
        "review_answers",
        "navigation",
        "attempt_limit",
        "duration_minutes",
        "shuffle_options",
        "shuffle_questions",
        "allow_review_flags",
    }
    unknown = sorted(set(policy) - allowed)
    if unknown:
        raise ValueError(f"Chính sách làm bài không được hỗ trợ {','.join(unknown)}")
    normalized = {
        "delivery_mode": "fixed",
        "review_answers": False,
        "navigation": "free",
        "attempt_limit": 1,
        "duration_minutes": None,
        "shuffle_options": False,
        "shuffle_questions": False,
        "allow_review_flags": True,
        **policy,
    }
    if normalized["delivery_mode"] != "fixed":
        raise ValueError("Phiên bản lõi chỉ hỗ trợ bài đánh giá cố định")
    if normalized["navigation"] not in {"free", "linear"}:
        raise ValueError("Chính sách điều hướng không hợp lệ")
    attempt_limit = normalized.get("attempt_limit")
    if (
        not isinstance(attempt_limit, int)
        or isinstance(attempt_limit, bool)
        or attempt_limit < 1
        or attempt_limit > 100
    ):
        raise ValueError("Giới hạn số lần làm không hợp lệ")
    duration = normalized.get("duration_minutes")
    if duration is not None and (
        not isinstance(duration, int)
        or isinstance(duration, bool)
        or duration < 1
        or duration > 1440
    ):
        raise ValueError("Thời lượng làm bài không hợp lệ")
    for field in ["review_answers", "shuffle_options", "shuffle_questions", "allow_review_flags"]:
        if not isinstance(normalized[field], bool):
            raise ValueError(f"Giá trị {field} không hợp lệ")
    return normalized


def ensure_aware(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def assignment_access(assignment: dict | None, current_time: datetime):
    if not assignment:
        return "available"
    available_from = ensure_aware(assignment.get("available_from"))
    due_at = ensure_aware(assignment.get("due_at"))
    if available_from and current_time < available_from:
        return "upcoming"
    if due_at and current_time > due_at:
        return "expired"
    return "available"


def attempt_deadline(started_at: datetime, policy: dict, assignment: dict | None):
    deadlines = []
    duration = policy.get("duration_minutes")
    if duration:
        deadlines.append(ensure_aware(started_at) + timedelta(minutes=int(duration)))
    if assignment and assignment.get("due_at"):
        deadlines.append(ensure_aware(assignment["due_at"]))
    return min(deadlines) if deadlines else None


def attempt_expired(attempt: dict, current_time: datetime):
    expires_at = ensure_aware(attempt.get("expires_at"))
    return bool(expires_at and current_time >= expires_at)
