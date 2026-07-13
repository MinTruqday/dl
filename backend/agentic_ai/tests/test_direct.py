import asyncio
import json
from unittest.mock import patch, MagicMock
from src.tools.surgical_editing import (
    read_document_section,
    edit_document_text,
    edit_document_block,
    propose_document_edits
)

dummy_config = {"configurable": {"token": "dummy_token"}}

async def test_read_document_section_json():
    with patch("src.tools.interface._make_api_request") as mock_api_request:
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
        print("test_read_document_section_json passed")

async def test_edit_document_text():
    with patch("src.tools.interface._make_api_request") as mock_api_request:
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
        
        call_args = mock_api_request.call_args_list[1]
        assert call_args[0][0] == "PUT"
        assert call_args[1]["json"]["content"] == "Hello Claude. This is a test."
        print("test_edit_document_text passed")

async def main():
    await test_read_document_section_json()
    await test_edit_document_text()
    print("All tests passed.")

if __name__ == "__main__":
    asyncio.run(main())
