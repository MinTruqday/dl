import json


def schema_instruction(schema):
    serialized = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    rules = [
        "Return exactly one valid JSON value that conforms to the supplied schema",
        "Do not include markdown prose code fences or text outside the JSON value",
        "Include every required property",
        "Use null for an unused nullable property",
        "Preserve identifiers exactly as supplied",
        "Before answering silently verify types required fields enumerations and cross field consistency",
        "Do not reveal hidden reasoning or the verification process",
    ]
    if "target_fields" in serialized:
        rules.append("Do not include a target field when its corresponding revised field is null")
    return "\n".join([*rules, "OUTPUT_JSON_SCHEMA", serialized])


def correction_instruction(error):
    return "\n".join(
        [
            "The previous value did not conform to the required schema",
            f"Validation error {str(error)[:1000]}",
            "Silently identify every validation failure and return only the corrected JSON value",
            "Do not explain the correction",
        ]
    )


def tool_selection_instruction(tool_definitions, forced_name=None):
    rules = [
        "Select exactly one registered tool that directly satisfies the request",
        "Return only one JSON object containing name and arguments",
        "The name must exactly match a registered tool",
        "The arguments must be a JSON object conforming to that tool schema",
        "Never invent missing identifiers or required arguments",
        "Silently verify authorization relevance and schema conformance before answering",
        "Do not reveal hidden reasoning",
    ]
    if forced_name:
        rules.append(f"Use exactly this tool {forced_name}")
    rules.append(f"REGISTERED_TOOLS {tool_definitions}")
    return "\n".join(rules)


def tool_selection_correction_instruction(error):
    return "\n".join(
        [
            "The previous tool selection was invalid",
            f"Validation error {str(error)[:1000]}",
            "Return only one corrected tool call JSON object",
            "Do not explain the correction",
        ]
    )
