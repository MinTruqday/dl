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
    if not token:
        return json.dumps({"status": "authentication_required"})
    headers = {"Authorization": token}
    from src.tools.http_client import make_api_request, INTERNAL_API_URL
    try:
        res = await make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200:
            return json.dumps({"status": "document_retrieval_failed"})
        doc_data = res.json().get("data", {})
    except Exception:
        logger.exception("Document loading failed")
        return json.dumps({"status": "document_service_unavailable"})

    format = doc_data.get("content_format", "doclib")
    content = doc_data.get("content", "")
    
    if format == "doclib":
        try:
            parsed = json.loads(content)
            blocks = parsed.get("blocks", [])
            sliced_blocks = blocks[start_index:start_index + limit]
            return json.dumps(
                {
                    "status": "success",
                    "start_index": start_index,
                    "end_index": start_index + len(sliced_blocks) - 1,
                    "total_blocks": len(blocks),
                    "blocks": sliced_blocks,
                },
                ensure_ascii=False,
            )
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"status": "document_content_invalid"})
    elif format == "doclibx":
        lines = content.splitlines()
        sliced_lines = lines[start_index:start_index + limit]
        return json.dumps(
            {
                "status": "success",
                "start_index": start_index,
                "end_index": start_index + len(sliced_lines) - 1,
                "total_lines": len(lines),
                "lines": sliced_lines,
            },
            ensure_ascii=False,
        )
    else:
        return json.dumps(
            {"status": "unsupported_document_format", "format": format}
        )

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
    if not token:
        return json.dumps({"status": "authentication_required"})
    headers = {"Authorization": token}
    from src.tools.http_client import make_api_request, INTERNAL_API_URL
    try:
        res = await make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200:
            return json.dumps({"status": "document_retrieval_failed"})
        doc_data = res.json().get("data", {})
    except Exception:
        logger.exception("Document loading failed")
        return json.dumps({"status": "document_service_unavailable"})

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
            return json.dumps(
                {
                    "status": "document_text_not_found",
                    "highest_similarity": highest_ratio,
                }
            )
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
        if res_content.status_code not in [200, 201]:
            return json.dumps(
                {
                    "status": "document_update_failed",
                    "upstream_status": res_content.status_code,
                }
            )
        await _broadcast_update(document_id, new_content)
    except Exception:
        logger.exception("Document content update failed")
        return json.dumps({"status": "document_service_unavailable"})
        
    return json.dumps({"status": "success", "document_id": document_id})

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
    if not token:
        return json.dumps({"status": "authentication_required"})
    headers = {"Authorization": token}
    from src.tools.http_client import make_api_request, INTERNAL_API_URL
    try:
        res = await make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200:
            return json.dumps({"status": "document_retrieval_failed"})
        doc_data = res.json().get("data", {})
    except Exception:
        logger.exception("Document loading failed")
        return json.dumps({"status": "document_service_unavailable"})

    format = doc_data.get("content_format", "doclib")
    content = doc_data.get("content", "")
    
    if format not in ["json", "doclib"]:
        return json.dumps(
            {"status": "unsupported_document_format", "format": format}
        )
        
    try:
        parsed = json.loads(content)
        blocks = parsed.get("blocks", [])
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"status": "document_content_invalid"})
        
    if action in ["insert", "replace"]:
        try:
            new_block = json.loads(new_block_json)
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"status": "new_block_invalid"})
            
    if block_id:
        target_index = next((i for i, b in enumerate(blocks) if b.get("id") == block_id), -1)
        if target_index != -1:
            block_index = target_index
        else:
            return json.dumps(
                {"status": "document_block_not_found", "block_id": block_id}
            )

    if action == "delete":
        if 0 <= block_index < len(blocks):
            blocks.pop(block_index)
        else:
            return json.dumps({"status": "block_index_out_of_bounds"})
    elif action == "replace":
        if 0 <= block_index < len(blocks):
            if "id" not in new_block and "id" in blocks[block_index]:
                new_block["id"] = blocks[block_index]["id"]
            blocks[block_index] = new_block
        else:
            return json.dumps({"status": "block_index_out_of_bounds"})
    elif action == "insert":
        if 0 <= block_index <= len(blocks):
            blocks.insert(block_index, new_block)
        else:
            return json.dumps({"status": "block_index_out_of_bounds"})
    else:
        return json.dumps({"status": "unsupported_block_action", "action": action})
        
    parsed["blocks"] = blocks
    new_content = json.dumps(parsed)
    
    content_payload = {"content": new_content, "content_format": format}
    try:
        res_content = await make_api_request(
            "PUT", f"{INTERNAL_API_URL}/tai-lieu/{document_id}/noi-dung", headers=headers, json=content_payload
        )
        if res_content.status_code not in [200, 201]:
            return json.dumps(
                {
                    "status": "document_update_failed",
                    "upstream_status": res_content.status_code,
                }
            )
        await _broadcast_update(document_id, new_content)
    except Exception:
        logger.exception("Document content update failed")
        return json.dumps({"status": "document_service_unavailable"})
        
    return json.dumps(
        {"status": "success", "document_id": document_id, "action": action}
    )

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
    if not token:
        return json.dumps({"status": "authentication_required"})
    headers = {"Authorization": token}
    from src.tools.http_client import make_api_request, INTERNAL_API_URL
    try:
        res = await make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{document_id}", headers=headers)
        if res.status_code != 200:
            return json.dumps({"status": "document_retrieval_failed"})
        doc_data = res.json().get("data", {})
    except Exception:
        logger.exception("Document loading failed")
        return json.dumps({"status": "document_service_unavailable"})

    format = doc_data.get("content_format", "doclib")
    content = doc_data.get("content", "")
    
    if format == "doclib":
        try:
            parsed = json.loads(content)
            blocks = parsed.get("blocks", [])
            blocks.append({
                "type": "paragraph",
                "data": {"text": f"<mark class=\"cdx-marker\">{proposed_text}</mark>"}
            })
            parsed["blocks"] = blocks
            new_content = json.dumps(parsed)
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"status": "document_content_invalid"})
    elif format == "doclibx":
        new_content = content + f"\n\n\\begin{{quote}}\n{proposed_text}\n\\end{{quote}}\n"
    else:
        new_content = content + f"\n\n{proposed_text}"
        
    content_payload = {"content": new_content, "content_format": format}
    try:
        res_content = await make_api_request(
            "PUT", f"{INTERNAL_API_URL}/tai-lieu/{document_id}/noi-dung", headers=headers, json=content_payload
        )
        if res_content.status_code not in [200, 201]:
            return json.dumps(
                {
                    "status": "document_update_failed",
                    "upstream_status": res_content.status_code,
                }
            )
        await _broadcast_update(document_id, new_content)
    except Exception:
        logger.exception("Document content update failed")
        return json.dumps({"status": "document_service_unavailable"})
        
    return json.dumps({"status": "success", "document_id": document_id})
