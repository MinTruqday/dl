import json
import httpx
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from loguru import logger

from src.core.infrastructure.configuration import settings

async def _broadcast_update(document_id: str, new_content: str):
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post(
                f"{settings.WEBSOCKET_URL}/ws/internal/broadcast",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                json={
                    "document_id": document_id,
                    "message": {
                        "type": "DOCUMENT_UPDATED",
                        "content": new_content,
                    },
                },
            )
            response.raise_for_status()
    except Exception:
        logger.exception("Failed to broadcast document update")


@tool
async def read_document_section(
    document_id: str,
    start_index: int = 0,
    limit: int = 50,
    config: RunnableConfig = None
) -> str:
    """
    <module_purpose>
    Read a specific section of a document by its ID to avoid overwhelming context.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when working with large documents and you only need to read a specific portion (by block index for EditorJS, or line numbers for LaTeX).
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token: return "Authentication token is missing or invalid"
    headers = {"Authorization": token}
    from src.tools.http_client import make_api_request, INTERNAL_API_URL
    try:
        res = await make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200: return "Document detailed information extraction failed"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Error loading document {e}")

    format = doc_data.get("content_format", "doclib")
    content = doc_data.get("content", "")
    
    if format == "doclib":
        try:
            parsed = json.loads(content)
            blocks = parsed.get("blocks", [])
            sliced_blocks = blocks[start_index:start_index + limit]
            return f"Document section retrieved successfully with blocks {start_index} to {start_index + len(sliced_blocks) - 1} out of {len(blocks)}\n" + json.dumps(sliced_blocks, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, TypeError):
            return "Document format is JSON but content parsing failed"
    elif format == "doclibx":
        lines = content.splitlines()
        sliced_lines = lines[start_index:start_index + limit]
        res_str = f"Showing lines {start_index} to {start_index + len(sliced_lines) - 1} out of {len(lines)}:\n"
        for i, line in enumerate(sliced_lines):
            res_str += f"{start_index + i}: {line}\n"
        return res_str
    else:
        return f"Document format {format} is unknown or unsupported"

@tool
async def edit_document_text(
    document_id: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
    config: RunnableConfig = None
) -> str:
    """
    <module_purpose>
    Surgically replace exact text in a document without rewriting the entire structure.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this to fix typos, change specific words, or rewrite small portions of text precisely.
    - old_string must exactly match a sequence of characters in the document.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token: return "Authentication token is missing or invalid"
    headers = {"Authorization": token}
    from src.tools.http_client import make_api_request, INTERNAL_API_URL
    try:
        res = await make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200: return "Document detailed information extraction failed"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Error loading document {e}")

    format = doc_data.get("content_format", "doclib")
    content = doc_data.get("content", "")
    
    if old_string not in content:
        import difflib
        lines = content.splitlines()
        best_match = None
        highest_ratio = 0.0
        
        for i in range(len(lines)):
            ratio = difflib.SequenceMatcher(None, old_string, lines[i]).ratio()
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = lines[i]
                
        if highest_ratio > 0.8 and best_match:
            logger.info(f"Fuzzy match used. Ratio: {highest_ratio}")
            content = content.replace(best_match, new_string, 1) if not replace_all else content.replace(best_match, new_string)
            new_content = content
        else:
            return f"Exact old_string not found and no close fuzzy match (highest ratio: {highest_ratio})"
    else:
        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            new_content = content.replace(old_string, new_string, 1)
        
    content_payload = {"content": new_content, "content_format": format}
    try:
        res_content = await make_api_request(
            "PUT", f"{INTERNAL_API_URL}/tai-lieu/{document_id}/noi-dung", headers=headers, json=content_payload
        )
        if res_content.status_code not in [200, 201]: return f"Document content update failed with API status code {res_content.status_code}"
        await _broadcast_update(document_id, new_content)
    except Exception as e:
        raise Exception(f"Error during content update {e}")
        
    return "Document text replaced successfully"

@tool
async def edit_document_block(
    document_id: str,
    block_index: int = -1,
    action: str = "replace",
    new_block_json: str = None,
    block_id: str = None,
    config: RunnableConfig = None
) -> str:
    """
    <module_purpose>
    Surgically insert, replace, or delete a specific block in an EditorJS document.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this for EditorJS documents ONLY (format='json').
    - action must be 'insert' (inserts before index), 'replace' (replaces block at index), or 'delete' (removes block at index).
    - new_block_json is required for 'insert' and 'replace' and must be a valid JSON string for a single EditorJS block.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token: return "Authentication token is missing or invalid"
    headers = {"Authorization": token}
    from src.tools.http_client import make_api_request, INTERNAL_API_URL
    try:
        res = await make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200: return "Document detailed information extraction failed"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Error loading document {e}")

    format = doc_data.get("content_format", "doclib")
    content = doc_data.get("content", "")
    
    if format not in ["json", "doclib"]:
        return "Tool applicability restricted to JSON EditorJS documents"
        
    try:
        parsed = json.loads(content)
        blocks = parsed.get("blocks", [])
    except (json.JSONDecodeError, TypeError):
        return "Document content validation failed as JSON"
        
    if action in ["insert", "replace"]:
        try:
            new_block = json.loads(new_block_json)
        except (json.JSONDecodeError, TypeError):
            return "Provided new_block_json is not a valid JSON string"
            
    if block_id:
        target_index = next((i for i, b in enumerate(blocks) if b.get("id") == block_id), -1)
        if target_index != -1:
            block_index = target_index
        else:
            return f"Block ID {block_id} not found"

    if action == "delete":
        if 0 <= block_index < len(blocks):
            blocks.pop(block_index)
        else:
            return "Target block_index is out of bounds"
    elif action == "replace":
        if 0 <= block_index < len(blocks):
            if "id" not in new_block and "id" in blocks[block_index]:
                new_block["id"] = blocks[block_index]["id"]
            blocks[block_index] = new_block
        else:
            return "Target block_index is out of bounds"
    elif action == "insert":
        if 0 <= block_index <= len(blocks):
            blocks.insert(block_index, new_block)
        else:
            return "Target block_index is out of bounds"
    else:
        return "Requested action is unknown and not supported"
        
    parsed["blocks"] = blocks
    new_content = json.dumps(parsed)
    
    content_payload = {"content": new_content, "content_format": format}
    try:
        res_content = await make_api_request(
            "PUT", f"{INTERNAL_API_URL}/tai-lieu/{document_id}/noi-dung", headers=headers, json=content_payload
        )
        if res_content.status_code not in [200, 201]: return f"Document content update failed with API status code {res_content.status_code}"
        await _broadcast_update(document_id, new_content)
    except Exception as e:
        raise Exception(f"Error during content update {e}")
        
    return f"Document block {action} operation completed successfully"

@tool
async def propose_document_edits(
    document_id: str,
    proposed_text: str,
    config: RunnableConfig = None
) -> str:
    """
    <module_purpose>
    Propose substantive edits (rewording, additions) for the user to review before applying directly.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this for substantive meaning changes (legal text, specific wording) where Track Changes / suggestions are preferred over direct edits.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token: return "Authentication token is missing or invalid"
    headers = {"Authorization": token}
    from src.tools.http_client import make_api_request, INTERNAL_API_URL
    try:
        res = await make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200: return "Document detailed information extraction failed"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Error loading document {e}")

    format = doc_data.get("content_format", "doclib")
    content = doc_data.get("content", "")
    
    if format == "doclib":
        try:
            parsed = json.loads(content)
            blocks = parsed.get("blocks", [])
            blocks.append({
                "type": "paragraph",
                "data": {"text": f"<mark class=\"cdx-marker\">PROPOSED EDIT:</mark> {proposed_text}"}
            })
            parsed["blocks"] = blocks
            new_content = json.dumps(parsed)
        except (json.JSONDecodeError, TypeError):
            return "Document parsing failed during proposal generation"
    elif format == "doclibx":
        new_content = content + f"\n\n% PROPOSED EDIT:\n% {proposed_text}\n"
    else:
        new_content = content + f"\n\n[PROPOSED EDIT]: {proposed_text}"
        
    content_payload = {"content": new_content, "content_format": format}
    try:
        res_content = await make_api_request(
            "PUT", f"{INTERNAL_API_URL}/tai-lieu/{document_id}/noi-dung", headers=headers, json=content_payload
        )
        if res_content.status_code not in [200, 201]: return f"Document content update failed with API status code {res_content.status_code}"
        await _broadcast_update(document_id, new_content)
    except Exception as e:
        raise Exception(f"Error during content update {e}")
        
    return "Proposed edits added to document successfully"
