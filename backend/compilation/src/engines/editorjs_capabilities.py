import json
from functools import lru_cache
from pathlib import Path


MANIFEST_PATH = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "word-feature-manifest.json"
)

VERIFIED_PERSISTENT_COMMANDS = {
    "DocLibAutoSaveSwitch": {
        "effect": "auto_save",
        "defaultParameters": {"enabled": True},
    },
    "DocLibAutoScroll": {
        "effect": "auto_scroll",
        "defaultParameters": {"enabled": True},
    },
    "DocLibAllMarkup": {
        "effect": "review_markup",
        "defaultParameters": {"enabled": True},
    },
    "DocLibBalloons": {
        "effect": "review_balloons",
        "defaultParameters": {"enabled": True},
    },
    "DocLibAutoCorrectCapsLockOff": {
        "effect": "editor_setting",
        "defaultParameters": {"setting": "autoCorrectCapsLockOff", "enabled": True},
    },
    "DocLibAutoCorrectInitialCaps": {
        "effect": "editor_setting",
        "defaultParameters": {"setting": "autoCorrectInitialCaps", "enabled": True},
    },
    "DocLibAutoCorrectSentenceCaps": {
        "effect": "editor_setting",
        "defaultParameters": {"setting": "autoCorrectSentenceCaps", "enabled": True},
    },
    "DocLibAutoCorrectSmartQuotes": {
        "effect": "editor_setting",
        "defaultParameters": {"setting": "autoCorrectSmartQuotes", "enabled": True},
    },
    "DocLibAutoFormatAsYouType": {
        "effect": "editor_setting",
        "defaultParameters": {"setting": "autoFormatAsYouType", "enabled": True},
    },
    "DocLibColumnsOne": {"effect": "columns", "defaultParameters": {"count": 1}},
    "DocLibColumnsTwo": {"effect": "columns", "defaultParameters": {"count": 2}},
    "DocLibColumnsThree": {"effect": "columns", "defaultParameters": {"count": 3}},
    "DocLibCustomWatermark": {
        "effect": "watermark",
        "defaultParameters": {"text": "TÀI LIỆU"},
    },
    "DocLibLineSpacing": {
        "effect": "line_spacing",
        "defaultParameters": {"value": 1.5},
    },
    "DocLibWidowOrphanControl": {
        "effect": "widow_orphan_control",
        "defaultParameters": {"lines": 2},
    },
    "DocLibKeepLinesTogether": {
        "effect": "keep_lines_together",
        "defaultParameters": {},
    },
    "DocLibDontHyphenate": {
        "effect": "hyphenation",
        "defaultParameters": {"value": "none"},
    },
    "DocLibParagraphSpacingSet": {
        "effect": "paragraph_spacing",
        "defaultParameters": {"before": 0, "after": 8},
    },
    "DocLibOrientation": {
        "effect": "orientation",
        "defaultParameters": {"value": "landscape"},
    },
    "DocLibPaperSize": {
        "effect": "paper_size",
        "defaultParameters": {"value": "A4"},
    },
    "DocLibZoom": {"effect": "zoom", "defaultParameters": {"percent": 100}},
}

VERIFIED_STRUCTURE_COMMANDS = {
    "DocLib3DModels": {
        "effect": "insert_media",
        "defaultParameters": {"block_type": "shape", "effect": "3DModels"},
    },
    "DocLib3DRotation": {
        "effect": "insert_media",
        "defaultParameters": {"block_type": "shape", "effect": "3DRotation"},
    },
    "DocLibAlignObjects": {
        "effect": "insert_media",
        "defaultParameters": {"block_type": "image", "effect": "AlignObjects"},
    },
    "DocLibAutoFit": {
        "effect": "table_autofit",
        "defaultParameters": {"block_index": -1},
    },
    "DocLibActiveXCheckBox": {
        "effect": "insert_block",
        "defaultParameters": {"block_type": "formCheckBox", "data": {"label": "", "checked": False}},
    },
    "DocLibActiveXComboBox": {
        "effect": "insert_block",
        "defaultParameters": {"block_type": "formDropdown", "data": {"label": "", "options": []}},
    },
    "DocLibActiveXCommandButton": {
        "effect": "insert_block",
        "defaultParameters": {"block_type": "formButton", "data": {"label": ""}},
    },
    "DocLibActiveXListBox": {
        "effect": "insert_block",
        "defaultParameters": {"block_type": "formList", "data": {"label": "", "options": []}},
    },
    "DocLibActiveXTextBox": {
        "effect": "insert_block",
        "defaultParameters": {"block_type": "formText", "data": {"label": "", "value": ""}},
    },
    "DocLibActiveXToggleButton": {
        "effect": "insert_block",
        "defaultParameters": {"block_type": "formToggle", "data": {"label": "", "checked": False}},
    },
    "DocLibAltText": {
        "effect": "insert_block",
        "defaultParameters": {"block_type": "image", "data": {"title": "", "effect": "AltText", "url": ""}},
    },
    "DocLibArtisticEffects": {
        "effect": "insert_block",
        "defaultParameters": {"block_type": "image", "data": {"title": "", "effect": "ArtisticEffects", "url": ""}},
    },
    "DocLibBevel": {
        "effect": "insert_block",
        "defaultParameters": {"block_type": "image", "data": {"title": "", "effect": "Bevel", "url": ""}},
    },
    "DocLibBlankPage": {
        "effect": "insert_break",
        "defaultParameters": {"index": -1, "kind": "BlankPage"},
    },
    "DocLibColumnBreak": {
        "effect": "insert_break",
        "defaultParameters": {"index": -1, "kind": "ColumnBreak"},
    },
    "DocLibConvertTableToText": {
        "effect": "table_to_text",
        "defaultParameters": {"block_index": -1, "separator": "\t"},
    },
    "DocLibConvertTextToTable": {
        "effect": "text_to_table",
        "defaultParameters": {"block_index": -1, "column_separator": "\t"},
    },
    "DocLibInsertAbove": {
        "effect": "insert_table_row",
        "defaultParameters": {"block_index": -1, "row_index": 0, "position": "above"},
    },
    "DocLibInsertBelow": {
        "effect": "insert_table_row",
        "defaultParameters": {"block_index": -1, "row_index": 0, "position": "below"},
    },
}

VERIFIED_TEXT_COMMANDS = {
    "DocLibAllCaps": {
        "effect": "format_block",
        "defaultParameters": {"block_index": -1, "style": "uppercase"},
    },
    "DocLibClearFormatting": {
        "effect": "format_block",
        "defaultParameters": {"block_index": -1, "style": "clear"},
    },
    "DocLibBold": {
        "effect": "format_block",
        "defaultParameters": {"block_index": -1, "style": "bold"},
    },
    "DocLibItalic": {
        "effect": "format_block",
        "defaultParameters": {"block_index": -1, "style": "italic"},
    },
    "DocLibWordUnderline": {
        "effect": "format_block",
        "defaultParameters": {"block_index": -1, "style": "underline"},
    },
    "DocLibTextHighlightColorPicker": {
        "effect": "format_block",
        "defaultParameters": {"block_index": -1, "style": "highlight"},
    },
    "DocLibAlignLeft": {
        "effect": "align_block",
        "defaultParameters": {"block_index": -1, "alignment": "left"},
    },
    "DocLibAlignCenter": {
        "effect": "align_block",
        "defaultParameters": {"block_index": -1, "alignment": "center"},
    },
    "DocLibAlignRight": {
        "effect": "align_block",
        "defaultParameters": {"block_index": -1, "alignment": "right"},
    },
    "DocLibAlignJustify": {
        "effect": "align_block",
        "defaultParameters": {"block_index": -1, "alignment": "justify"},
    },
}

VERIFIED_BLOCK_COMMANDS = {
    "DocLibAltText": {
        "effect": "image_alt_text",
        "defaultParameters": {"block_index": -1, "text": ""},
    },
    "DocLibGridlines": {
        "effect": "table_gridlines",
        "defaultParameters": {"block_index": -1, "visible": True},
    },
}

VERIFIED_ANALYSIS_COMMANDS = {
    "DocLibAccessibilityChecker": {
        "effect": "accessibility_check",
        "defaultParameters": {},
    },
    "DocLibAutoCheckForErrors": {
        "effect": "proofread_document",
        "defaultParameters": {"language": "vi"},
    },
    "DocLibDocumentInspector": {
        "effect": "inspect_document",
        "defaultParameters": {},
    },
    "DocLibWordCount": {
        "effect": "word_count",
        "defaultParameters": {},
    },
}

VERIFIED_DOCUMENT_COMMANDS = {
    **{
        feature_id: {
            **contract,
            "executionKind": "persistent_document_command",
        }
        for feature_id, contract in VERIFIED_PERSISTENT_COMMANDS.items()
    },
    **{
        feature_id: {
            **contract,
            "executionKind": "document_structure_command",
        }
        for feature_id, contract in VERIFIED_STRUCTURE_COMMANDS.items()
    },
    **{
        feature_id: {
            **contract,
            "executionKind": "document_text_command",
        }
        for feature_id, contract in VERIFIED_TEXT_COMMANDS.items()
    },
    **{
        feature_id: {
            **contract,
            "executionKind": "document_block_command",
        }
        for feature_id, contract in VERIFIED_BLOCK_COMMANDS.items()
    },
    **{
        feature_id: {
            **contract,
            "executionKind": "document_analysis_command",
        }
        for feature_id, contract in VERIFIED_ANALYSIS_COMMANDS.items()
    },
}


def command_execution(feature_id):
    command = VERIFIED_DOCUMENT_COMMANDS.get(feature_id)
    if command is None:
        return {"executionStatus": "unavailable"}
    return {
        "executionStatus": "verified",
        **command,
    }


def capability_with_execution(feature):
    return {**feature, **command_execution(feature["id"])}


def validate_document_command_state(parsed_content):
    state = parsed_content.get("documentCommandState")
    if state is None:
        return {"schemaVersion": 1, "commands": {}}
    if not isinstance(state, dict) or state.get("schemaVersion", 1) != 1:
        raise ValueError("Trạng thái lệnh tài liệu không hợp lệ")
    commands = state.get("commands")
    if not isinstance(commands, dict) or len(commands) > 50:
        raise ValueError("Danh sách lệnh tài liệu không hợp lệ")
    normalized = {}
    capabilities = capabilities_by_id()
    for feature_id, command_value in commands.items():
        contract = VERIFIED_PERSISTENT_COMMANDS.get(feature_id)
        feature = capabilities.get(feature_id)
        if contract is None or feature is None:
            continue
        if not isinstance(command_value, dict):
            raise ValueError("Lệnh tài liệu chưa được xác minh")
        if (
            command_value.get("mode") != feature.get("mode")
            or not isinstance(command_value.get("enabled"), bool)
            or not isinstance(command_value.get("appliedAt"), (int, float))
        ):
            raise ValueError("Dữ liệu lệnh tài liệu không khớp capability")
        parameters = command_value.get("parameters", {})
        if not isinstance(parameters, dict) or len(parameters) > 10:
            raise ValueError("Tham số lệnh tài liệu không hợp lệ")
        parameters = {**contract["defaultParameters"], **parameters}
        effect = contract["effect"]
        if effect == "columns":
            count = parameters.get("count")
            if (
                not isinstance(count, int)
                or isinstance(count, bool)
                or count != contract["defaultParameters"]["count"]
            ):
                raise ValueError("Số cột không hợp lệ")
            parameters = {"count": count}
        elif effect == "zoom":
            percent = parameters.get("percent")
            if not isinstance(percent, (int, float)) or isinstance(percent, bool) or not 50 <= percent <= 200:
                raise ValueError("Tỷ lệ thu phóng không hợp lệ")
            parameters = {"percent": percent}
        elif effect == "line_spacing":
            value = parameters.get("value")
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 1 <= value <= 3:
                raise ValueError("Giãn dòng không hợp lệ")
            parameters = {"value": value}
        elif effect == "widow_orphan_control":
            lines = parameters.get("lines")
            if not isinstance(lines, int) or isinstance(lines, bool) or not 2 <= lines <= 4:
                raise ValueError("Số dòng góa và mồ côi không hợp lệ")
            parameters = {"lines": lines}
        elif effect == "keep_lines_together":
            if parameters:
                raise ValueError("Tham số giữ các dòng cùng nhau không hợp lệ")
        elif effect == "hyphenation":
            if parameters.get("value") != "none" or set(parameters) != {"value"}:
                raise ValueError("Chế độ ngắt từ không hợp lệ")
            parameters = {"value": "none"}
        elif effect == "paragraph_spacing":
            before = parameters.get("before")
            after = parameters.get("after")
            if (
                isinstance(before, bool)
                or not isinstance(before, (int, float))
                or not 0 <= before <= 72
                or isinstance(after, bool)
                or not isinstance(after, (int, float))
                or not 0 <= after <= 72
                or set(parameters) != {"before", "after"}
            ):
                raise ValueError("Khoảng cách đoạn không hợp lệ")
            parameters = {"before": before, "after": after}
        elif effect == "orientation":
            value = parameters.get("value")
            if value not in {"portrait", "landscape"}:
                raise ValueError("Hướng giấy không hợp lệ")
            parameters = {"value": value}
        elif effect == "paper_size":
            value = parameters.get("value")
            if value not in {"A4", "Letter", "Legal"}:
                raise ValueError("Khổ giấy không hợp lệ")
            parameters = {"value": value}
        elif effect == "watermark":
            text = parameters.get("text")
            if not isinstance(text, str) or not text.strip() or len(text) > 120:
                raise ValueError("Nội dung hình mờ không hợp lệ")
            parameters = {"text": text.strip()}
        normalized[feature_id] = {
            "mode": command_value["mode"],
            "enabled": command_value["enabled"],
            "appliedAt": command_value["appliedAt"],
            "parameters": parameters,
            "effect": effect,
        }
    return {"schemaVersion": 1, "commands": normalized}
@lru_cache(maxsize=1)
def capability_manifest():
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    features = payload.get("features")
    if payload.get("schemaVersion") != 1 or not isinstance(features, list):
        raise RuntimeError("EditorJS capability manifest is invalid")
    ids = set()
    icons = set()
    tool_keys = set()
    for feature in features:
        feature_id = feature.get("id")
        title = feature.get("title")
        icon = feature.get("icon")
        product = feature.get("product")
        tool_key = feature.get("toolKey")
        if (
            not isinstance(feature_id, str)
            or not feature_id.startswith("DocLib")
            or feature_id in ids
            or not isinstance(title, str)
            or not title.startswith("DocLib ")
            or not isinstance(icon, str)
            or icon in icons
            or product != "doclib"
        ):
            raise RuntimeError("EditorJS capability manifest contains invalid data")
        if tool_key is not None:
            if not isinstance(tool_key, str) or tool_key in tool_keys:
                raise RuntimeError("EditorJS capability tool key is invalid")
            tool_keys.add(tool_key)
        ids.add(feature_id)
        icons.add(icon)
    if len(features) != 2449 or len(tool_keys) != 2296:
        raise RuntimeError("EditorJS capability manifest count is invalid")
    return payload


@lru_cache(maxsize=1)
def capabilities_by_id():
    return {
        feature["id"]: feature
        for feature in capability_manifest()["features"]
    }


@lru_cache(maxsize=1)
def capabilities_by_tool_key():
    return {
        feature["toolKey"]: feature
        for feature in capability_manifest()["features"]
        if feature.get("toolKey")
    }


def capability_page(
    query="",
    offset=0,
    limit=100,
    include_icons=False,
):
    normalized = query.strip().lower()
    features = capability_manifest()["features"]
    selected = [
        feature
        for feature in features
        if (
            not normalized
            or normalized in feature["id"].lower()
            or normalized in feature["title"].lower()
            or normalized
            in str(feature.get("description") or "").lower()
            or normalized in str(feature.get("mode") or "").lower()
        )
    ]
    page = [capability_with_execution(feature) for feature in selected[offset:offset + limit]]
    if not include_icons:
        page = [
            {
                key: value
                for key, value in feature.items()
                if key != "icon"
            }
            for feature in page
        ]
    return {
        "total": len(selected),
        "offset": offset,
        "limit": limit,
        "items": page,
    }


def validate_command_block(block):
    block_type = block.get("type")
    feature = capabilities_by_tool_key().get(block_type)
    if feature is None:
        return False
    data = block.get("data")
    if not isinstance(data, dict):
        raise ValueError("Dữ liệu lệnh EditorJS không hợp lệ")
    if (
        data.get("feature") != feature["id"]
        or data.get("mode") != feature["mode"]
        or not isinstance(data.get("applied"), bool)
    ):
        raise ValueError("Dữ liệu lệnh EditorJS không khớp capability")
    return True
