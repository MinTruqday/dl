import os
import json
import pytest
from src.tools.search import glob_search, grep_search

def test_glob_search_basic():
    result = glob_search.invoke({"pattern": "**/*.py", "path": "src"})
    assert isinstance(result, str)
    files = json.loads(result)
    assert len(files) > 0
    assert any("interface.py" in f for f in files)
    
def test_grep_search_basic():
    result = grep_search.invoke({
        "pattern": "glob_search",
        "path": "src",
        "output_mode": "content",
        "show_line_numbers": True
    })
    data = json.loads(result)
    assert "result" in data
    text = data["result"]
    assert "search.py" in text or "interface.py" in text
    assert "glob_search" in text

def test_grep_search_count_mode():
    result = grep_search.invoke({
        "pattern": "def ",
        "path": "src/tools/search.py",
        "output_mode": "count"
    })
    data = json.loads(result)
    assert "result" in data
    assert int(data["result"].strip()) >= 2

def test_grep_search_case_insensitive():
    result = grep_search.invoke({
        "pattern": "GLOB_search",
        "path": "src/tools/search.py",
        "output_mode": "content",
        "case_insensitive": True
    })
    data = json.loads(result)
    text = data["result"]
    assert "def glob_search" in text

if __name__ == "__main__":
    pytest.main(["-v", __file__])
