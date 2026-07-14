import json
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from loguru import logger
import requests

def _broadcast_update(document_id: str, new_content: str):
    try:
        requests.post(
            "http://websocket:8000/ws/broadcast",
            json={
                "document_id": document_id,
                "message": {
                    "type": "DOCUMENT_UPDATED",
                    "content": new_content
                }
            },
            timeout=2.0
        )
    except Exception as e:
        logger.error(f"Failed to broadcast update: {e}")


@tool
async def read_document_section(
    document_id: str,
    start_index: int = 0,
    limit: int = 50,
    config: RunnableConfig = None
) -> str:
    """
    <tool_definition>
    
    Read a specific section of a document by its ID to avoid overwhelming context.
    
    WHEN TO USE THIS TOOL:
    - Use this when working with large documents and you only need to read a specific portion (by block index for EditorJS, or line numbers for LaTeX).
    
    </tool_definition>
    """
    token = config.get("configurable", {}).get("token")
    if not token: return "Authentication token is missing or invalid"
    headers = {"Authorization": token}
    from src.tools.interface import _make_api_request, INTERNAL_API_URL
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200: return "Document detailed information extraction failed"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Error loading document {e}")

    format = doc_data.get("content_format", "json")
    content = doc_data.get("content", "")
    
    if format == "json":
        try:
            parsed = json.loads(content)
            blocks = parsed.get("blocks", [])
            sliced_blocks = blocks[start_index:start_index + limit]
            return f"Document section retrieved successfully with blocks {start_index} to {start_index + len(sliced_blocks) - 1} out of {len(blocks)}\n" + json.dumps(sliced_blocks, ensure_ascii=False, indent=2)
        except:
            return "Document format is JSON but content parsing failed"
    elif format == "latex":
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
    <tool_definition>
    
    Surgically replace exact text in a document without rewriting the entire structure.
    
    WHEN TO USE THIS TOOL:
    - Use this to fix typos, change specific words, or rewrite small portions of text precisely.
    - old_string must exactly match a sequence of characters in the document.
    
    </tool_definition>
    """
    token = config.get("configurable", {}).get("token")
    if not token: return "Authentication token is missing or invalid"
    headers = {"Authorization": token}
    from src.tools.interface import _make_api_request, INTERNAL_API_URL
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200: return "Document detailed information extraction failed"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Error loading document {e}")

    format = doc_data.get("content_format", "json")
    content = doc_data.get("content", "")
    
    if old_string not in content:
        return "Exact old_string not found in document content due to mismatch"
        
    if replace_all:
        new_content = content.replace(old_string, new_string)
    else:
        new_content = content.replace(old_string, new_string, 1)
        
    content_payload = {"content": new_content, "content_format": format}
    try:
        res_content = await _make_api_request(
            "PUT", f"{INTERNAL_API_URL}/tai-lieu/{document_id}/noi-dung", headers=headers, json=content_payload
        )
        if res_content.status_code not in [200, 201]: return f"Document content update failed with API status code {res_content.status_code}"
        _broadcast_update(document_id, new_content)
    except Exception as e:
        raise Exception(f"Error during content update {e}")
        
    return "Document text replaced successfully"

@tool
async def edit_document_block(
    document_id: str,
    block_index: int,
    action: str,
    new_block_json: str = None,
    config: RunnableConfig = None
) -> str:
    """
    <tool_definition>
    
    Surgically insert, replace, or delete a specific block in an EditorJS document.
    
    WHEN TO USE THIS TOOL:
    - Use this for EditorJS documents ONLY (format='json').
    - action must be 'insert' (inserts before index), 'replace' (replaces block at index), or 'delete' (removes block at index).
    - new_block_json is required for 'insert' and 'replace' and must be a valid JSON string for a single EditorJS block (e.g. '{"type":"paragraph","data":{"text":"..."}}').
    
    </tool_definition>
    """
    token = config.get("configurable", {}).get("token")
    if not token: return "Authentication token is missing or invalid"
    headers = {"Authorization": token}
    from src.tools.interface import _make_api_request, INTERNAL_API_URL
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200: return "Document detailed information extraction failed"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Error loading document {e}")

    format = doc_data.get("content_format", "json")
    content = doc_data.get("content", "")
    
    if format != "json":
        return "Tool applicability restricted to JSON EditorJS documents"
        
    try:
        parsed = json.loads(content)
        blocks = parsed.get("blocks", [])
    except:
        return "Document content validation failed as JSON"
        
    if action in ["insert", "replace"]:
        try:
            new_block = json.loads(new_block_json)
        except:
            return "Provided new_block_json is not a valid JSON string"
            
    if action == "delete":
        if 0 <= block_index < len(blocks):
            blocks.pop(block_index)
        else:
            return "Target block_index is out of bounds"
    elif action == "replace":
        if 0 <= block_index < len(blocks):
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
        res_content = await _make_api_request(
            "PUT", f"{INTERNAL_API_URL}/tai-lieu/{document_id}/noi-dung", headers=headers, json=content_payload
        )
        if res_content.status_code not in [200, 201]: return f"Document content update failed with API status code {res_content.status_code}"
        _broadcast_update(document_id, new_content)
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
    <tool_definition>
    
    Propose substantive edits (rewording, additions) for the user to review before applying directly.
    
    WHEN TO USE THIS TOOL:
    - Use this for substantive meaning changes (legal text, specific wording) where Track Changes / suggestions are preferred over direct edits.
    
    </tool_definition>
    """
    token = config.get("configurable", {}).get("token")
    if not token: return "Authentication token is missing or invalid"
    headers = {"Authorization": token}
    from src.tools.interface import _make_api_request, INTERNAL_API_URL
    try:
        res = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200: return "Document detailed information extraction failed"
        doc_data = res.json().get("data", {})
    except Exception as e:
        raise Exception(f"Error loading document {e}")

    format = doc_data.get("content_format", "json")
    content = doc_data.get("content", "")
    
    if format == "json":
        try:
            parsed = json.loads(content)
            blocks = parsed.get("blocks", [])
            blocks.append({
                "type": "paragraph",
                "data": {"text": f"<mark class=\"cdx-marker\">PROPOSED EDIT:</mark> {proposed_text}"}
            })
            parsed["blocks"] = blocks
            new_content = json.dumps(parsed)
        except:
            return "Document parsing failed during proposal generation"
    elif format == "latex":
        new_content = content + f"\n\n% PROPOSED EDIT:\n% {proposed_text}\n"
    else:
        new_content = content + f"\n\n[PROPOSED EDIT]: {proposed_text}"
        
    content_payload = {"content": new_content, "content_format": format}
    try:
        res_content = await _make_api_request(
            "PUT", f"{INTERNAL_API_URL}/tai-lieu/{document_id}/noi-dung", headers=headers, json=content_payload
        )
        if res_content.status_code not in [200, 201]: return f"Document content update failed with API status code {res_content.status_code}"
        _broadcast_update(document_id, new_content)
    except Exception as e:
        raise Exception(f"Error during content update {e}")
        
    return "Proposed edits added to document successfully"
