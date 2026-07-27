import json
import re
from typing import Any, Type


class StructuredOutputError(ValueError):
    pass


def _balanced_candidates(text: str):
    for start, character in enumerate(text):
        if character not in "[{":
            continue
        stack = []
        quoted = False
        escaped = False
        for index in range(start, len(text)):
            current = text[index]
            if quoted:
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    quoted = False
                continue
            if current == '"':
                quoted = True
            elif current in "[{":
                stack.append(current)
            elif current in "]}":
                if not stack:
                    break
                opening = stack.pop()
                if (opening, current) not in {("[", "]"), ("{", "}")}:
                    break
                if not stack:
                    yield text[start : index + 1]
                    break


def extract_json_value(text: Any) -> Any:
    if isinstance(text, (dict, list)):
        return text
    if not isinstance(text, str) or not text.strip():
        raise StructuredOutputError("Model output is empty")
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    candidates = [cleaned]
    candidates.extend(
        match.group(1).strip()
        for match in re.finditer(
            r"```(?:json)?\s*([\s\S]*?)```",
            cleaned,
            flags=re.IGNORECASE,
        )
    )
    candidates.extend(_balanced_candidates(cleaned))
    failures = []
    for candidate in candidates:
        variants = [
            candidate,
            re.sub(r",\s*([}\]])", r"\1", candidate),
        ]
        for variant in variants:
            try:
                return json.loads(variant)
            except (TypeError, json.JSONDecodeError) as error:
                failures.append(str(error))
    detail = failures[-1] if failures else "No JSON object or array found"
    raise StructuredOutputError(f"Invalid structured model output: {detail}")


def validate_structured_output(text: Any, schema: Type[Any]) -> Any:
    value = extract_json_value(text)
    if hasattr(schema, "model_validate"):
        return schema.model_validate(value)
    return schema.parse_obj(value)
