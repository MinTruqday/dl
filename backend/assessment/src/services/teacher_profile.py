from datetime import datetime, timezone
from uuid import uuid4
from collections import Counter

from pymongo import ReturnDocument

from src.core.database import database


def profile_now():
    return datetime.now(timezone.utc)


async def persist_teacher_profile_event(
    teacher_id: str, event_type: str, payload: dict, idempotency_key: str
):
    event = {
        "_id": f"TPE-{uuid4().hex}",
        "teacher_id": teacher_id,
        "event_type": event_type,
        "payload": payload,
        "idempotency_key": idempotency_key,
        "created_at": profile_now(),
    }
    persisted = await database.value.teacher_profile_events.find_one_and_update(
        {"teacher_id": teacher_id, "idempotency_key": idempotency_key},
        {"$setOnInsert": event},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    if persisted["_id"] != event["_id"]:
        return persisted, False
    events = (
        await database.value.teacher_profile_events.find({"teacher_id": teacher_id})
        .sort("created_at", -1)
        .limit(5000)
        .to_list(5000)
    )
    question_type_counts = {}
    difficulty_values = []
    edit_counts = {}
    pedagogy_signal_counts: Counter[str] = Counter()
    pedagogy_solution_patterns: Counter[str] = Counter()
    pedagogy_presentation_preferences: Counter[str] = Counter()
    pedagogy_confidences = []
    for signal in events:
        signal_payload = signal.get("payload", {})
        if signal.get("event_type") == "question_type_selected" and signal_payload.get(
            "question_type"
        ):
            question_type = str(signal_payload["question_type"])
            question_type_counts[question_type] = question_type_counts.get(question_type, 0) + 1
        if signal.get("event_type") == "difficulty_targeted" and isinstance(
            signal_payload.get("target_difficulty"), (int, float)
        ):
            difficulty_values.append(float(signal_payload["target_difficulty"]))
        if signal.get("event_type") == "manual_edit":
            fields = signal_payload.get("fields") or (
                [signal_payload.get("field")] if signal_payload.get("field") else []
            )
            for field_value in fields:
                field = str(field_value)
                edit_counts[field] = edit_counts.get(field, 0) + 1
        if signal.get("event_type") == "pedagogy_context_observed":
            pedagogy = signal_payload.get("pedagogical_context") or {}
            pedagogy_signal_counts.update(pedagogy.get("signals") or [])
            pedagogy_solution_patterns.update(pedagogy.get("preferred_solution_patterns") or [])
            pedagogy_presentation_preferences.update(pedagogy.get("presentation_preferences") or [])
            confidence = pedagogy.get("confidence")
            if isinstance(confidence, (int, float)):
                pedagogy_confidences.append(float(confidence))
    inferred = {
        "accepted_generation_count": sum(
            signal.get("event_type") == "generation_accepted" for signal in events
        ),
        "rejected_generation_count": sum(
            signal.get("event_type") == "generation_rejected" for signal in events
        ),
        "question_type_counts": question_type_counts,
        "average_target_difficulty": round(sum(difficulty_values) / len(difficulty_values), 3)
        if difficulty_values
        else None,
        "manual_edit_field_counts": edit_counts,
        "material_usage_count": sum(
            signal.get("event_type") == "material_used" for signal in events
        ),
        "pedagogy_signal_counts": dict(pedagogy_signal_counts),
        "pedagogy_solution_patterns": dict(pedagogy_solution_patterns),
        "pedagogy_presentation_preferences": dict(pedagogy_presentation_preferences),
        "pedagogy_confidence": round(sum(pedagogy_confidences) / len(pedagogy_confidences), 3)
        if pedagogy_confidences
        else 0.0,
        "signal_count": len(events),
    }
    timestamp = profile_now()
    await database.value.teacher_profiles.update_one(
        {"user_id": teacher_id},
        {
            "$set": {"inferred_preferences": inferred, "updated_at": timestamp},
            "$setOnInsert": {
                "_id": f"TP-{uuid4().hex}",
                "user_id": teacher_id,
                "explicit_preferences": {},
                "use_own_materials": True,
                "created_at": timestamp,
            },
        },
        upsert=True,
    )
    return persisted, True
