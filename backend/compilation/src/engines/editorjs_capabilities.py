import json
from functools import lru_cache
from pathlib import Path


MANIFEST_PATH = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "word-feature-manifest.json"
)
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
            or not title
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
            or normalized in str(feature.get("mode") or "").lower()
        )
    ]
    page = selected[offset:offset + limit]
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
