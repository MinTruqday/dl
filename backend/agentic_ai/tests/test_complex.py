import asyncio
from unittest.mock import patch, MagicMock
import json

dummy_config = {"configurable": {"token": "dummy_token"}}

async def test_complex_editorjs_text_replace():
    print("Running test_complex_editorjs_text_replace...")
    complex_json = {
        "time": 1690000000000,
        "blocks": [
            { "type": "header", "data": { "text": "This is a complex header", "level": 2 } },
            { "type": "image", "data": { "file": { "url": "http://img.com/a.jpg" }, "caption": "A nice image" } },
            { "type": "table", "data": { "content": [["K1", "V1"], ["K2", "V2"]] } },
            { "type": "code", "data": { "code": "def test(): pass" } }
        ],
        "version": "2.27.0"
    }
    
    with patch("src.tools.interface._make_api_request") as mock_api_request:
        mock_resp_get = MagicMock()
        mock_resp_get.status_code = 200
        mock_resp_get.json.return_value = {
            "data": {
                "content_format": "json",
                "content": json.dumps(complex_json)
            }
        }
        
        mock_resp_put = MagicMock()
        mock_resp_put.status_code = 200
        
        # We also need to mock requests.post in surgical_editing._broadcast_update
        with patch("src.tools.surgical_editing.requests.post") as mock_post:
            mock_api_request.side_effect = [mock_resp_get, mock_resp_put]
            
            from src.tools.surgical_editing import edit_document_text
            res = await edit_document_text.ainvoke({
                "document_id": "doc123",
                "old_string": "K1",
                "new_string": "Key1",
                "replace_all": False
            }, config=dummy_config)
            
            assert "successfully" in res
            
            put_call = mock_api_request.call_args_list[1]
            payload = put_call.kwargs["json"]
            assert "Key1" in payload["content"]
            assert "K1" not in payload["content"]
            
            mock_post.assert_called_once()
            print("test_complex_editorjs_text_replace passed!")


async def test_complex_editorjs_block_replace():
    print("Running test_complex_editorjs_block_replace...")
    complex_json = {
        "time": 1690000000000,
        "blocks": [
            { "type": "header", "data": { "text": "Header", "level": 2 } },
            { "type": "image", "data": { "file": { "url": "http://img.com/a.jpg" }, "caption": "A nice image" } }
        ],
        "version": "2.27.0"
    }
    
    with patch("src.tools.interface._make_api_request") as mock_api_request:
        mock_resp_get = MagicMock()
        mock_resp_get.status_code = 200
        mock_resp_get.json.return_value = {
            "data": {
                "content_format": "json",
                "content": json.dumps(complex_json)
            }
        }
        
        mock_resp_put = MagicMock()
        mock_resp_put.status_code = 200
        
        with patch("src.tools.surgical_editing.requests.post") as mock_post:
            mock_api_request.side_effect = [mock_resp_get, mock_resp_put]
            
            from src.tools.surgical_editing import edit_document_block
            new_block = json.dumps({ "type": "list", "data": { "style": "unordered", "items": ["Item 1", "Item 2"] } })
            res = await edit_document_block.ainvoke({
                "document_id": "doc123",
                "block_index": 1,
                "action": "replace",
                "new_block_json": new_block
            }, config=dummy_config)
            
            assert "successful" in res
            
            put_call = mock_api_request.call_args_list[1]
            payload = put_call.kwargs["json"]
            updated_content = json.loads(payload["content"])
            assert updated_content["blocks"][1]["type"] == "list"
            assert updated_content["blocks"][1]["data"]["items"][0] == "Item 1"
            
            mock_post.assert_called_once()
            print("test_complex_editorjs_block_replace passed!")

async def test_complex_latex_text_replace():
    print("Running test_complex_latex_text_replace...")
    latex_content = "\\begin{tabular}{|c|c|}\n\\hline\nA & B \\\\\n\\hline\n\\end{tabular}"
    
    with patch("src.tools.interface._make_api_request") as mock_api_request:
        mock_resp_get = MagicMock()
        mock_resp_get.status_code = 200
        mock_resp_get.json.return_value = {
            "data": {
                "content_format": "latex",
                "content": latex_content
            }
        }
        
        mock_resp_put = MagicMock()
        mock_resp_put.status_code = 200
        
        with patch("src.tools.surgical_editing.requests.post") as mock_post:
            mock_api_request.side_effect = [mock_resp_get, mock_resp_put]
            
            from src.tools.surgical_editing import edit_document_text
            res = await edit_document_text.ainvoke({
                "document_id": "doc123",
                "old_string": "A & B \\\\",
                "new_string": "C & D \\\\",
                "replace_all": False
            }, config=dummy_config)
            
            assert "successfully" in res
            
            put_call = mock_api_request.call_args_list[1]
            payload = put_call.kwargs["json"]
            assert "C & D \\\\" in payload["content"]
            assert "A & B \\\\" not in payload["content"]
            
            mock_post.assert_called_once()
            print("test_complex_latex_text_replace passed!")


async def main():
    await test_complex_editorjs_text_replace()
    await test_complex_editorjs_block_replace()
    await test_complex_latex_text_replace()
    print("All tests passed.")

if __name__ == "__main__":
    asyncio.run(main())
