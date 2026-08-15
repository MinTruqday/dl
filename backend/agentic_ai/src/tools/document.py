import json
import html
import re
import time
import uuid
from typing import Annotated, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from loguru import logger
from pydantic import Field
from src.tools.http_client import INTERNAL_API_URL, check_system_access, make_api_request
from src.core.infrastructure.configuration import settings


def _uppercase_editor_html(value: str) -> str:
    parts = re.split(r"(<[^>]+>)", value)
    return "".join(
        part
        if part.startswith("<") and part.endswith(">")
        else html.escape(html.unescape(part).upper(), quote=False)
        for part in parts
    )


def _clear_editor_html(value: str) -> str:
    with_breaks = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    plain = html.unescape(re.sub(r"<[^>]+>", "", with_breaks))
    return html.escape(plain, quote=False).replace("\n", "<br>")


def _plain_editor_text(value) -> str:
    if isinstance(value, str):
        return html.unescape(re.sub(r"<[^>]+>", " ", value))
    if isinstance(value, list):
        return " ".join(_plain_editor_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(
            _plain_editor_text(item)
            for key, item in value.items()
            if key in {"text", "content", "title", "caption", "items"}
        )
    return ""


def _document_plain_text(blocks: list) -> str:
    return "\n".join(
        _plain_editor_text(block.get("data", {}))
        for block in blocks
        if isinstance(block, dict)
    ).strip()


@tool
async def search_editorjs_capabilities(
    query: Annotated[str, Field(description="Capability name, EditorJS block key, or Word control to find")] = "",
    offset: Annotated[int, Field(ge=0, description="Zero-based result offset for pagination")] = 0,
    limit: Annotated[int, Field(ge=1, le=200, description="Maximum number of capabilities to return")] = 50,
    config: RunnableConfig = None,
) -> str:
    """
    <module_purpose>
    Search the authoritative DocLib EditorJS capability catalog
    </module_purpose>
    <contract>
    Use this before creating or editing EditorJS blocks when the exact tool key schema or Microsoft Word control mapping is unknown
    Every returned capability belongs to DocLib
    Never invent a block type control ID mode or implementation status
    </contract>
    """
    token = (config or {}).get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    try:
        response = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/soan-thao/editorjs/capabilities",
            headers={"Authorization": token},
            params={
                "query": query,
                "offset": max(offset, 0),
                "limit": min(max(limit, 1), 200),
            },
            timeout=30.0,
        )
        if response.status_code != 200:
            return json.dumps(
                {
                    "status": "capability_search_failed",
                    "upstream_status": response.status_code,
                }
            )
        return json.dumps(
            {
                "status": "success",
                **response.json(),
            },
            ensure_ascii=False,
        )
    except Exception:
        logger.exception("EditorJS capability search failed")
        return json.dumps({"status": "compilation_service_unavailable"})


async def _get_doc_text(document_id: str, token: str) -> str:
    try:
        res = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers={"Authorization": token},
            timeout=30.0,
        )
        if res.status_code == 200:
            return res.json().get("data", {}).get("content", "")
    except Exception:
        logger.exception("Failed to load document content")
    return ""


@tool
async def create_document(
    title: Annotated[str, Field(min_length=1, description="User-visible document title")],
    content_format: Annotated[str, Field(description="Document format: doclib for EditorJS JSON or doclibx for LaTeX source")] = "doclib",
    content: Annotated[str, Field(description="Complete initial EditorJS JSON or LaTeX source; empty creates a valid starter document")] = "",
    description: Annotated[str, Field(description="Optional document description stored with its metadata")] = "",
    config: RunnableConfig = None,
) -> str:
    """
    <module_purpose>
    Create a new EditorJS or LaTeX document owned by the authenticated user
    </module_purpose>
    <contract>
    Use doclib for EditorJS JSON and doclibx for LaTeX source
    EditorJS content must contain a blocks array
    Search EditorJS capabilities before using a block type that is not already present in the document
    Empty content creates a valid starter document for the selected format
    </contract>
    """
    token = (config or {}).get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    normalized_format = content_format.strip().lower()
    if normalized_format not in {"doclib", "doclibx"}:
        return json.dumps({"status": "unsupported_document_format"})
    normalized_content = content
    if normalized_format == "doclib":
        if not normalized_content.strip():
            normalized_content = json.dumps(
                {"time": 0, "blocks": [], "version": "2.30.8"}
            )
        try:
            parsed = json.loads(normalized_content)
        except (TypeError, json.JSONDecodeError):
            parsed = {
                "time": 0,
                "blocks": [
                    {
                        "type": "paragraph",
                        "data": {"text": str(normalized_content)},
                    }
                ],
                "version": "2.30.8",
            }
        if not isinstance(parsed, dict) or not isinstance(parsed.get("blocks"), list):
            return json.dumps({"status": "document_content_invalid"})
        normalized_content = json.dumps(parsed, ensure_ascii=False)
    elif not normalized_content.strip():
        normalized_content = (
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "\\end{document}\n"
        )
    payload = {
        "title": title,
        "description": description,
        "content": normalized_content,
        "content_format": normalized_format,
        "visibility": "private",
    }
    try:
        response = await make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/tai-lieu",
            headers={"Authorization": token},
            json=payload,
            timeout=30.0,
        )
        if response.status_code != 201:
            return json.dumps(
                {
                    "status": "document_creation_failed",
                    "upstream_status": response.status_code,
                }
            )
        data = response.json().get("data", {})
        document_id = data.get("_id") or data.get("id")
        return json.dumps(
            {
                "status": "success",
                "document_id": document_id,
                "title": title,
                "url": f"/tai-lieu/xem-truoc/{document_id}",
                "content_format": normalized_format,
            },
            ensure_ascii=False,
        )
    except Exception:
        logger.exception("Document creation failed")
        return json.dumps({"status": "document_service_unavailable"})


@tool
async def update_document_metadata(
    document_id: Annotated[str, Field(description="Exact identifier of the document to update")],
    title: Annotated[Optional[str], Field(description="Replacement title; omit to preserve the current title")] = None,
    description: Annotated[Optional[str], Field(description="Replacement description; omit to preserve it")] = None,
    category: Annotated[Optional[str], Field(description="Replacement category; omit to preserve it")] = None,
    tags: Annotated[Optional[list[str]], Field(description="Complete replacement tag list; omit to preserve current tags")] = None,
    config: RunnableConfig = None,
) -> str:
    """
    <module_purpose>
    Update editable metadata for one document without changing its content
    </module_purpose>
    <contract>
    Provide the exact document ID and at least one metadata field
    Existing content and format remain unchanged
    </contract>
    """
    token = (config or {}).get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    values = {
        "title": title,
        "description": description,
        "category": category,
        "tags": tags,
    }
    payload = {key: value for key, value in values.items() if value is not None}
    if not payload:
        return json.dumps({"status": "document_update_empty"})
    try:
        response = await make_api_request(
            "PUT",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers={"Authorization": token},
            json=payload,
            timeout=30.0,
        )
        if response.status_code != 200:
            return json.dumps(
                {
                    "status": "document_update_failed",
                    "upstream_status": response.status_code,
                }
            )
        return json.dumps({"status": "success", "document_id": document_id})
    except Exception:
        logger.exception("Document metadata update failed")
        return json.dumps({"status": "document_service_unavailable"})


@tool
async def replace_document_content(
    document_id: Annotated[str, Field(description="Exact identifier of the document whose complete content will be replaced")],
    content: Annotated[str, Field(description="Complete replacement EditorJS JSON or LaTeX source")],
    content_format: Annotated[str, Field(description="Replacement format: doclib for EditorJS JSON or doclibx for LaTeX source")],
    config: RunnableConfig = None,
) -> str:
    """
    <module_purpose>
    Replace the complete EditorJS or LaTeX source of an existing document
    </module_purpose>
    <contract>
    Use doclib for EditorJS JSON and doclibx for LaTeX source
    Search EditorJS capabilities before introducing a new block type
    Prefer surgical edit tools when only a small region needs modification
    </contract>
    """
    token = (config or {}).get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    normalized_format = content_format.strip().lower()
    if normalized_format not in {"doclib", "doclibx"}:
        return json.dumps({"status": "unsupported_document_format"})
    normalized_content = content
    if normalized_format == "doclib":
        try:
            parsed = json.loads(content)
        except (TypeError, json.JSONDecodeError):
            return json.dumps({"status": "document_content_invalid"})
        if not isinstance(parsed, dict) or not isinstance(parsed.get("blocks"), list):
            return json.dumps({"status": "document_content_invalid"})
        normalized_content = json.dumps(parsed, ensure_ascii=False)
    elif not content.strip():
        return json.dumps({"status": "document_content_invalid"})
    try:
        response = await make_api_request(
            "PUT",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}/noi-dung",
            headers={"Authorization": token},
            json={
                "content": normalized_content,
                "content_format": normalized_format,
            },
            timeout=30.0,
        )
        if response.status_code != 200:
            return json.dumps(
                {
                    "status": "document_update_failed",
                    "upstream_status": response.status_code,
                }
            )
        from src.tools.editing import _broadcast_update

        await _broadcast_update(document_id, normalized_content)
        return json.dumps(
            {
                "status": "success",
                "document_id": document_id,
                "content_format": normalized_format,
            }
        )
    except Exception:
        logger.exception("Document content replacement failed")
        return json.dumps({"status": "document_service_unavailable"})


@tool
async def apply_editorjs_command(
    document_id: Annotated[
        str,
        Field(description="Exact identifier of the EditorJS document to update"),
    ],
    feature_id: Annotated[
        str,
        Field(description="Exact DocLib capability ID returned by search_editorjs_capabilities"),
    ],
    enabled: Annotated[
        bool,
        Field(description="Enable or disable the persistent document command"),
    ] = True,
    parameters_json: Annotated[
        str,
        Field(description="Bounded JSON object containing command parameters"),
    ] = "{}",
    config: RunnableConfig = None,
) -> str:
    """
    <module_purpose>
    Apply one registered DocLib command to an EditorJS document through the shared persistent command contract
    </module_purpose>
    <contract>
    Search capabilities first and pass the exact DocLib feature ID
    This tool accepts command capabilities only and rejects core block types without a command mode
    Use edit_document_block when the requested operation creates replaces or deletes content blocks
    </contract>
    """
    token = (config or {}).get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    try:
        parameters = json.loads(parameters_json)
    except (TypeError, json.JSONDecodeError):
        return json.dumps({"status": "command_parameters_invalid"})
    if not isinstance(parameters, dict) or len(parameters) > 50:
        return json.dumps({"status": "command_parameters_invalid"})
    if len(json.dumps(parameters, ensure_ascii=False).encode("utf-8")) > 20000:
        return json.dumps({"status": "command_parameters_too_large"})
    headers = {"Authorization": token}
    try:
        capability_response = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/soan-thao/editorjs/capabilities/{feature_id}",
            headers=headers,
            timeout=30.0,
        )
        if capability_response.status_code == 404:
            return json.dumps({"status": "editorjs_command_not_found"})
        if capability_response.status_code != 200:
            return json.dumps(
                {
                    "status": "capability_lookup_failed",
                    "upstream_status": capability_response.status_code,
                }
            )
        capability = capability_response.json()
        mode = capability.get("mode")
        tool_key = capability.get("toolKey")
        if capability.get("id") != feature_id or not mode or not tool_key:
            return json.dumps({"status": "capability_is_not_a_document_command"})
        execution_kind = capability.get("executionKind")
        if capability.get("executionStatus") != "verified" or execution_kind not in {
            "persistent_document_command",
            "document_structure_command",
            "document_text_command",
            "document_block_command",
            "document_analysis_command",
        }:
            return json.dumps({"status": "document_command_not_verified"})
        if execution_kind != "persistent_document_command" and not enabled:
            return json.dumps({"status": "command_parameters_invalid"})

        defaults = capability.get("defaultParameters")
        if not isinstance(defaults, dict):
            defaults = {}
        parameters = {**defaults, **parameters}
        effect = capability.get("effect")
        if effect == "columns":
            expected_count = defaults.get("count")
            if parameters.get("count") != expected_count or set(parameters) != {"count"}:
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect in {"auto_save", "auto_scroll", "review_markup", "review_balloons"}:
            if not isinstance(parameters.get("enabled"), bool) or set(parameters) != {"enabled"}:
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "editor_setting":
            if (
                not isinstance(parameters.get("setting"), str)
                or not isinstance(parameters.get("enabled"), bool)
                or len(parameters["setting"]) > 80
                or set(parameters) != {"setting", "enabled"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "zoom":
            percent = parameters.get("percent")
            if (
                isinstance(percent, bool)
                or not isinstance(percent, (int, float))
                or not 50 <= percent <= 200
                or set(parameters) != {"percent"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "watermark":
            text = parameters.get("text")
            if (
                not isinstance(text, str)
                or not text.strip()
                or len(text) > 120
                or set(parameters) != {"text"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
            parameters = {"text": text.strip()}
        elif effect == "line_spacing":
            value = parameters.get("value")
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 1 <= value <= 3
                or set(parameters) != {"value"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "widow_orphan_control":
            lines = parameters.get("lines")
            if (
                isinstance(lines, bool)
                or not isinstance(lines, int)
                or not 2 <= lines <= 4
                or set(parameters) != {"lines"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "keep_lines_together":
            if parameters:
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "hyphenation":
            if parameters.get("value") != "none" or set(parameters) != {"value"}:
                return json.dumps({"status": "command_parameters_invalid"})
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
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "orientation":
            if parameters.get("value") not in {"portrait", "landscape"} or set(parameters) != {"value"}:
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "paper_size":
            if parameters.get("value") not in {"A4", "Letter", "Legal"} or set(parameters) != {"value"}:
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "insert_break":
            index = parameters.get("index")
            if (
                isinstance(index, bool)
                or not isinstance(index, int)
                or index < -1
                or parameters.get("kind") != defaults.get("kind")
                or set(parameters) != {"index", "kind"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect in {"table_to_text", "text_to_table"}:
            block_index = parameters.get("block_index")
            separator_key = "separator" if effect == "table_to_text" else "column_separator"
            separator = parameters.get(separator_key)
            if (
                isinstance(block_index, bool)
                or not isinstance(block_index, int)
                or block_index < 0
                or not isinstance(separator, str)
                or not 1 <= len(separator) <= 5
                or set(parameters) != {"block_index", separator_key}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "insert_table_row":
            block_index = parameters.get("block_index")
            row_index = parameters.get("row_index")
            if (
                isinstance(block_index, bool)
                or not isinstance(block_index, int)
                or block_index < 0
                or isinstance(row_index, bool)
                or not isinstance(row_index, int)
                or row_index < 0
                or parameters.get("position") != defaults.get("position")
                or set(parameters) != {"block_index", "row_index", "position"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "format_block":
            block_index = parameters.get("block_index")
            if (
                isinstance(block_index, bool)
                or not isinstance(block_index, int)
                or block_index < 0
                or parameters.get("style") != defaults.get("style")
                or set(parameters) != {"block_index", "style"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "align_block":
            block_index = parameters.get("block_index")
            if (
                isinstance(block_index, bool)
                or not isinstance(block_index, int)
                or block_index < 0
                or parameters.get("alignment") != defaults.get("alignment")
                or set(parameters) != {"block_index", "alignment"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "image_alt_text":
            block_index = parameters.get("block_index")
            text = parameters.get("text")
            if (
                isinstance(block_index, bool)
                or not isinstance(block_index, int)
                or block_index < 0
                or not isinstance(text, str)
                or not text.strip()
                or len(text) > 500
                or set(parameters) != {"block_index", "text"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
            parameters["text"] = text.strip()
        elif effect == "table_gridlines":
            block_index = parameters.get("block_index")
            if (
                isinstance(block_index, bool)
                or not isinstance(block_index, int)
                or block_index < 0
                or not isinstance(parameters.get("visible"), bool)
                or set(parameters) != {"block_index", "visible"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "insert_block":
            block_type = parameters.get("block_type")
            data = parameters.get("data")
            if (
                block_type not in {"formCheckBox", "formDropdown", "formButton", "formList", "formText", "formToggle", "image"}
                or not isinstance(data, dict)
                or len(data) > 12
                or set(parameters) != {"block_type", "data"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "insert_media":
            if (
                parameters.get("block_type") not in {"shape", "image"}
                or not isinstance(parameters.get("effect"), str)
                or len(parameters["effect"]) > 80
                or set(parameters) != {"block_type", "effect"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "table_autofit":
            if (
                isinstance(parameters.get("block_index"), bool)
                or not isinstance(parameters.get("block_index"), int)
                or parameters["block_index"] < 0
                or set(parameters) != {"block_index"}
            ):
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect == "proofread_document":
            if parameters.get("language") not in {"vi", "en"} or set(parameters) != {"language"}:
                return json.dumps({"status": "command_parameters_invalid"})
        elif effect in {"accessibility_check", "inspect_document", "word_count"}:
            if parameters:
                return json.dumps({"status": "command_parameters_invalid"})
        else:
            return json.dumps({"status": "document_command_not_verified"})

        document_response = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers=headers,
            timeout=30.0,
        )
        if document_response.status_code != 200:
            return json.dumps(
                {
                    "status": "document_retrieval_failed",
                    "upstream_status": document_response.status_code,
                }
            )
        document = document_response.json().get("data", {})
        if document.get("content_format", "doclib") not in {"doclib", "json"}:
            return json.dumps({"status": "unsupported_document_format"})
        try:
            parsed = json.loads(document.get("content", ""))
        except (TypeError, json.JSONDecodeError):
            return json.dumps({"status": "document_content_invalid"})
        if not isinstance(parsed, dict) or not isinstance(parsed.get("blocks"), list):
            return json.dumps({"status": "document_content_invalid"})

        blocks = parsed["blocks"]
        if execution_kind == "document_analysis_command":
            plain_text = _document_plain_text(blocks)
            words = re.findall(r"\b[\wÀ-ỹ]+\b", plain_text, flags=re.UNICODE)
            if effect == "word_count":
                analysis = {
                    "words": len(words),
                    "characters": len(plain_text),
                    "characters_without_spaces": len(re.sub(r"\s", "", plain_text)),
                    "blocks": len(blocks),
                }
            elif effect == "proofread_document":
                issues = []
                for match in re.finditer(r"\s+[,.!?;:]", plain_text):
                    issues.append(
                        {"type": "space_before_punctuation", "offset": match.start()}
                    )
                for match in re.finditer(
                    r"\b([\wÀ-ỹ]+)\s+\1\b", plain_text, flags=re.I | re.UNICODE
                ):
                    issues.append(
                        {
                            "type": "repeated_word",
                            "offset": match.start(),
                            "text": match.group(0),
                        }
                    )
                for match in re.finditer(r" {2,}", plain_text):
                    issues.append(
                        {"type": "repeated_space", "offset": match.start()}
                    )
                analysis = {
                    "language": parameters["language"],
                    "issue_count": len(issues),
                    "issues": issues[:200],
                }
            else:
                images_missing_alt = []
                raw_blocks = []
                empty_blocks = []
                heading_levels = []
                for index, block in enumerate(blocks):
                    if not isinstance(block, dict):
                        continue
                    block_type = block.get("type")
                    data = block.get("data") if isinstance(block.get("data"), dict) else {}
                    if block_type in {"image", "simpleImage", "imageCrop", "imageWithLink"} and not str(
                        data.get("alt", data.get("caption", ""))
                    ).strip():
                        images_missing_alt.append(index)
                    if block_type in {"raw", "html"}:
                        raw_blocks.append(index)
                    if not _plain_editor_text(data).strip() and block_type not in {
                        "delimiter",
                        "pageBreak",
                        "table",
                        "image",
                    }:
                        empty_blocks.append(index)
                    if block_type == "header":
                        heading_levels.append((index, int(data.get("level", 2))))
                heading_jumps = [
                    current[0]
                    for previous, current in zip(heading_levels, heading_levels[1:])
                    if current[1] > previous[1] + 1
                ]
                if effect == "accessibility_check":
                    analysis = {
                        "issue_count": len(images_missing_alt) + len(heading_jumps),
                        "images_missing_alt": images_missing_alt,
                        "heading_level_jumps": heading_jumps,
                    }
                else:
                    analysis = {
                        "blocks": len(blocks),
                        "images_missing_alt": images_missing_alt,
                        "raw_blocks": raw_blocks,
                        "empty_blocks": empty_blocks,
                        "external_links": len(
                            re.findall(r'href=["\']https?://', json.dumps(parsed))
                        ),
                    }
            return json.dumps(
                {
                    "status": "success",
                    "document_id": document_id,
                    "feature_id": feature_id,
                    "mode": mode,
                    "execution_kind": execution_kind,
                    "analysis": analysis,
                },
                ensure_ascii=False,
            )
        if execution_kind == "persistent_document_command":
            state = parsed.get("documentCommandState")
            if not isinstance(state, dict):
                state = {"schemaVersion": 1, "commands": {}}
            commands = state.get("commands")
            if not isinstance(commands, dict):
                commands = {}
            commands[feature_id] = {
                "mode": mode,
                "enabled": enabled,
                "appliedAt": int(time.time() * 1000),
                "parameters": parameters,
            }
            state["schemaVersion"] = 1
            state["commands"] = commands
            parsed["documentCommandState"] = state
        elif effect == "insert_break":
            index = parameters["index"]
            insert_at = len(blocks) if index == -1 else min(index, len(blocks))
            blocks.insert(
                insert_at,
                {
                    "id": uuid.uuid4().hex[:12],
                    "type": "pageBreak",
                    "data": {"kind": parameters["kind"]},
                },
            )
        elif effect == "insert_block":
            blocks.append(
                {
                    "id": uuid.uuid4().hex[:12],
                    "type": parameters["block_type"],
                    "data": parameters["data"],
                }
            )
        elif effect == "insert_media":
            blocks.append(
                {
                    "id": uuid.uuid4().hex[:12],
                    "type": parameters["block_type"],
                    "data": {"title": mode, "effect": parameters["effect"], "url": ""},
                }
            )
        elif effect == "table_autofit":
            index = parameters["block_index"]
            if index >= len(blocks) or blocks[index].get("type") != "table":
                return json.dumps({"status": "command_target_not_table"})
            blocks[index].setdefault("data", {})["autoFit"] = True
        elif effect in {"table_to_text", "text_to_table", "insert_table_row"}:
            block_index = parameters["block_index"]
            if block_index >= len(blocks):
                return json.dumps({"status": "command_target_not_found"})
            target = blocks[block_index]
            if not isinstance(target, dict) or not isinstance(target.get("data"), dict):
                return json.dumps({"status": "command_target_invalid"})
            if effect == "table_to_text":
                content = target["data"].get("content")
                if target.get("type") != "table" or not isinstance(content, list):
                    return json.dumps({"status": "command_target_not_table"})
                rows = []
                for row in content[:1000]:
                    if not isinstance(row, list):
                        return json.dumps({"status": "command_target_invalid"})
                    rows.append(
                        parameters["separator"].join(
                            html.escape(str(cell or "")) for cell in row[:100]
                        )
                    )
                blocks[block_index] = {
                    "id": target.get("id") or uuid.uuid4().hex[:12],
                    "type": "paragraph",
                    "data": {"text": "<br>".join(rows)},
                }
            elif effect == "text_to_table":
                if target.get("type") not in {"paragraph", "header"}:
                    return json.dumps({"status": "command_target_not_text"})
                raw_text = str(target["data"].get("text", ""))
                plain_text = html.unescape(
                    re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", "\n", raw_text, flags=re.I))
                )
                rows = [
                    row.split(parameters["column_separator"])[:100]
                    for row in plain_text.splitlines()[:1000]
                    if row
                ] or [[plain_text]]
                blocks[block_index] = {
                    "id": target.get("id") or uuid.uuid4().hex[:12],
                    "type": "table",
                    "data": {"content": rows, "withHeadings": False},
                }
            else:
                content = target["data"].get("content")
                if target.get("type") != "table" or not isinstance(content, list):
                    return json.dumps({"status": "command_target_not_table"})
                if len(content) >= 1000:
                    return json.dumps({"status": "command_target_too_large"})
                if any(not isinstance(row, list) for row in content):
                    return json.dumps({"status": "command_target_invalid"})
                column_count = max([len(row) for row in content] or [1])
                row_index = min(parameters["row_index"], len(content))
                insert_at = min(
                    len(content),
                    row_index + (1 if parameters["position"] == "below" else 0),
                )
                content.insert(insert_at, [""] * max(1, column_count))
        elif effect in {"format_block", "align_block"}:
            block_index = parameters["block_index"]
            if block_index >= len(blocks):
                return json.dumps({"status": "command_target_not_found"})
            target = blocks[block_index]
            if (
                not isinstance(target, dict)
                or target.get("type") not in {"paragraph", "header", "quote"}
                or not isinstance(target.get("data"), dict)
            ):
                return json.dumps({"status": "command_target_not_text"})
            if effect == "align_block":
                target["data"]["alignment"] = parameters["alignment"]
            else:
                text_field = "text" if "text" in target["data"] else "content"
                raw_text = str(target["data"].get(text_field, ""))
                style = parameters["style"]
                if style == "uppercase":
                    updated_text = _uppercase_editor_html(raw_text)
                elif style == "clear":
                    updated_text = _clear_editor_html(raw_text)
                elif style == "bold":
                    updated_text = f"<b>{raw_text}</b>"
                elif style == "italic":
                    updated_text = f"<i>{raw_text}</i>"
                elif style == "underline":
                    updated_text = f"<u>{raw_text}</u>"
                elif style == "highlight":
                    class_name = "DocLibHighlightColor"
                    updated_text = f'<span class="{class_name}">{raw_text}</span>'
                else:
                    return json.dumps({"status": "command_parameters_invalid"})
                target["data"][text_field] = updated_text
        elif effect in {"image_alt_text", "table_gridlines"}:
            block_index = parameters["block_index"]
            if block_index >= len(blocks):
                return json.dumps({"status": "command_target_not_found"})
            target = blocks[block_index]
            if not isinstance(target, dict) or not isinstance(target.get("data"), dict):
                return json.dumps({"status": "command_target_invalid"})
            if effect == "image_alt_text":
                if target.get("type") not in {
                    "image",
                    "simpleImage",
                    "imageCrop",
                    "imageWithLink",
                }:
                    return json.dumps({"status": "command_target_not_image"})
                target["data"]["alt"] = parameters["text"]
            else:
                if target.get("type") != "table":
                    return json.dumps({"status": "command_target_not_table"})
                target["data"]["gridlines"] = parameters["visible"]
        new_content = json.dumps(parsed, ensure_ascii=False)

        update_payload = {"content": new_content, "content_format": "doclib"}
        if document.get("updated_at"):
            update_payload["expected_version"] = document["updated_at"]
        update_response = await make_api_request(
            "PUT",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}/noi-dung",
            headers=headers,
            json=update_payload,
            timeout=30.0,
        )
        if update_response.status_code not in {200, 201}:
            return json.dumps(
                {
                    "status": "document_update_failed",
                    "upstream_status": update_response.status_code,
                }
            )
        from src.tools.editing import _broadcast_update
        collaboration_synced = True
        try:
            await _broadcast_update(document_id, new_content)
        except Exception:
            collaboration_synced = False
            logger.exception("EditorJS command persisted but collaboration broadcast failed")
        return json.dumps(
            {
                "status": "success",
                "document_id": document_id,
                "feature_id": feature_id,
                "mode": mode,
                "execution_kind": execution_kind,
                "enabled": enabled,
                "parameters": parameters,
                "collaboration_synced": collaboration_synced,
            },
            ensure_ascii=False,
        )
    except Exception:
        logger.exception("EditorJS command application failed")
        return json.dumps({"status": "document_command_service_unavailable"})


@tool
async def get_my_documents(config: RunnableConfig) -> str:
    """
    <module_purpose>
    List all personal documents owned or published by the current user.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks to see their documents, what they have written, or their library.
    CRITICAL: Returns an empty-library message if no documents exist. Requires authentication.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/ca-nhan",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            return json.dumps(
                {"status": "success", "documents": data},
                ensure_ascii=False,
            )
        return json.dumps({"status": "document_list_retrieval_failed"})
    except Exception:
        logger.exception("Failed to load document list from MongoDB")
        return json.dumps({"status": "document_service_unavailable"})

@tool
async def get_trash_documents(config: RunnableConfig) -> str:
    """
    <module_purpose>
    View deleted documents currently in the trash bin.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks about deleted files, trash bin, or recovering a deleted document.
    CRITICAL: Requires authentication. Only shows files deleted by this user.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    if not check_system_access(token):
        return json.dumps({"status": "insufficient_permissions"})

    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/thung-rac",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            return json.dumps(
                {"status": "success", "documents": data},
                ensure_ascii=False,
            )
        return json.dumps({"status": "trash_document_list_retrieval_failed"})
    except Exception:
        logger.exception("Failed to load deleted items list")
        return json.dumps({"status": "document_service_unavailable"})

@tool
async def delete_document(
    document_id: Annotated[str, Field(description="Exact identifier of the document to move to trash")], config: RunnableConfig
) -> str:
    """
    <module_purpose>
    Delete a document by ID, moving it to the trash bin.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user explicitly requests to delete, remove, or trash a specific document.
    CRITICAL: Requires the exact document ID.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})

    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "DELETE",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            try:
                from src.clients.rag import rag_client
                await rag_client.delete_document(
                    document_id,
                    settings.PLATFORM_SYSTEM_ID,
                    True,
                )
                logger.info("Document index cleanup completed")
            except Exception:
                logger.exception("Failed to clean up document index")
            return json.dumps({"status": "success", "document_id": document_id})
        return json.dumps({"status": "document_deletion_failed"})
    except Exception:
        logger.exception("Document deletion failed due to system error")
        return json.dumps({"status": "document_service_unavailable"})

@tool
async def restore_document(
    document_id: Annotated[str, Field(description="Exact identifier of the deleted document to restore")], config: RunnableConfig
) -> str:
    """
    <module_purpose>
    Restore a document from the trash bin by its ID.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks to recover, undelete, or restore a previously deleted document.
    CRITICAL: Requires the exact document ID of a deleted document.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})

    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}/khoi-phuc",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            return json.dumps({"status": "success", "document_id": document_id})
        return json.dumps({"status": "document_restoration_failed"})
    except Exception:
        logger.exception("Document restoration from trash failed")
        return json.dumps({"status": "document_service_unavailable"})

@tool
async def get_document_analytics(
    document_id: Annotated[str, Field(description="Exact identifier of the document whose analytics are requested")], config: RunnableConfig
) -> str:
    """
    <module_purpose>
    View detailed analytics including read count and drop-off rate for a document.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks how well their document is performing, how many reads it has, or its drop-off rate.
    CRITICAL: Requires the exact document ID.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    if not check_system_access(token):
        return json.dumps({"status": "insufficient_permissions"})

    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/tai-lieu/{document_id}/phan-tich/bo-do",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            readers = data.get("readers_started", 0)
            rate = data.get("dropoff_rate", 0)
            return json.dumps(
                {
                    "status": "success",
                    "readers_started": readers,
                    "dropoff_rate": rate,
                }
            )
        return json.dumps({"status": "document_analytics_retrieval_failed"})
    except Exception:
        logger.exception("Failed to retrieve analytics data")
        return json.dumps({"status": "document_service_unavailable"})

@tool
async def read_document(
    document_id: Annotated[str, Field(description="Exact identifier of the document to read")], config: RunnableConfig
) -> str:
    """
    <module_purpose>
    Read full text content of a document by document ID.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks to read, view, or analyze a specific document by its ID.
    CRITICAL: Requires a valid document_id.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    text = await _get_doc_text(document_id, token)
    if not text:
        return json.dumps({"status": "document_content_unavailable"})
    return text

@tool
async def recommend_documents(
    query: Annotated[str, Field(min_length=1, description="Topic, project need, or search phrase used to rank document recommendations")], config: RunnableConfig
) -> str:
    """
    <module_purpose>
    Search and recommend the top 3 most relevant documents for a project request or query.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks for document recommendations, reference materials, or templates for building a project.
    CRITICAL: Returns a structured summary of the top 3 matching documents including title, link, price, and match description.
    </contract>
    """
    from src.clients.content import ContentClient

    try:
        docs = await ContentClient.search(query)
        if not docs:
            return json.dumps({
                "status": "success",
                "query": query,
                "recommendations": [],
            }, ensure_ascii=False)

        recommendations = []
        for doc in docs:
            doc_id = str(doc.get("id"))
            recommendations.append({
                "id": doc_id,
                "title": doc.get("title") or "",
                "slug": doc.get("slug", ""),
                "summary": doc.get("summary") or doc.get("description") or "",
                "url": f"/tai-lieu/xem-truoc/{doc_id}",
            })

        result_payload = {
            "status": "success",
            "query": query,
            "recommendations": recommendations,
        }
        return (
            '<agentic-payload kind="RECOMMENDED_DOCS_PAYLOAD">'
            f"{json.dumps(result_payload, ensure_ascii=False)}"
            "</agentic-payload>"
        )
    except Exception:
        logger.exception("Failed to execute document recommendation tool")
        return json.dumps({"status": "document_recommendation_failed"})
