import json
import pytest
import datetime
from unittest.mock import patch, MagicMock

from src.tools.surgical_editing import (
    read_document_section,
    edit_document_text,
    edit_document_block,
    propose_document_edits
)

dummy_config = {"configurable": {"token": "dummy_token"}}

@pytest.fixture
def mock_api_request():
    with patch("src.tools.surgical_editing._make_api_request") as mock_req:
        yield mock_req

@pytest.mark.asyncio
async def test_read_document_section_json(mock_api_request):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": {
            "content_format": "json",
            "content": json.dumps({"blocks": [{"type": "paragraph", "data": {"text": f"Block {i}"}} for i in range(10)]})
        }
    }
    mock_api_request.return_value = mock_resp

    result = await read_document_section.ainvoke({"document_id": "doc1", "start_index": 2, "limit": 2}, config=dummy_config)
    assert "Showing blocks 2 to 3" in result
    assert "Block 2" in result
    assert "Block 3" in result

@pytest.mark.asyncio
async def test_edit_document_text(mock_api_request):
    mock_resp_get = MagicMock()
    mock_resp_get.status_code = 200
    mock_resp_get.json.return_value = {
        "data": {
            "content_format": "latex",
            "content": "Hello World. This is a test."
        }
    }
    
    mock_resp_put = MagicMock()
    mock_resp_put.status_code = 200
    
    mock_api_request.side_effect = [mock_resp_get, mock_resp_put]

    result = await edit_document_text.ainvoke({
        "document_id": "doc1",
        "old_string": "World",
        "new_string": "Claude"
    }, config=dummy_config)
    
    assert "successfully" in result
    
    # Check the payload sent to PUT
    call_args = mock_api_request.call_args_list[1]
    assert call_args[0][0] == "PUT"
    assert call_args[1]["json"]["content"] == "Hello Claude. This is a test."

@pytest.mark.asyncio
async def test_edit_document_block_insert(mock_api_request):
    mock_resp_get = MagicMock()
    mock_resp_get.status_code = 200
    mock_resp_get.json.return_value = {
        "data": {
            "content_format": "json",
            "content": json.dumps({"blocks": [{"type": "paragraph", "data": {"text": "Block 0"}}]})
        }
    }
    
    mock_resp_put = MagicMock()
    mock_resp_put.status_code = 200
    
    mock_api_request.side_effect = [mock_resp_get, mock_resp_put]

    new_block = json.dumps({"type": "paragraph", "data": {"text": "Inserted"}})
    
    result = await edit_document_block.ainvoke({
        "document_id": "doc1",
        "block_index": 0,
        "action": "insert",
        "new_block_json": new_block
    }, config=dummy_config)
    
    call_args = mock_api_request.call_args_list[1]
    sent_content = json.loads(call_args[1]["json"]["content"])
    assert len(sent_content["blocks"]) == 2
    assert sent_content["blocks"][0]["data"]["text"] == "Inserted"

@pytest.mark.asyncio
async def test_propose_document_edits(mock_api_request):
    mock_resp_get = MagicMock()
    mock_resp_get.status_code = 200
    mock_resp_get.json.return_value = {
        "data": {
            "content_format": "latex",
            "content": "Original text."
        }
    }
    
    mock_resp_put = MagicMock()
    mock_resp_put.status_code = 200
    
    mock_api_request.side_effect = [mock_resp_get, mock_resp_put]

    result = await propose_document_edits.ainvoke({
        "document_id": "doc1",
        "proposed_text": "Consider changing this to something else."
    }, config=dummy_config)
    
    call_args = mock_api_request.call_args_list[1]
    sent_content = call_args[1]["json"]["content"]
    assert "PROPOSED EDIT:" in sent_content
    assert "Consider changing this to something else." in sent_content
