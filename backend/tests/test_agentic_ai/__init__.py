"""
Pytest configuration for agentic_ai test suite.
Prevents MagicMock settings from leaking into module-level imports.
"""
import sys
import os
import pytest

# Ensure agentic_ai src is on path
_ai_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../agentic_ai"))
if _ai_src not in sys.path:
    sys.path.insert(0, _ai_src)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration (require running Docker services)")
    config.addinivalue_line("markers", "unit: marks tests as pure unit tests (no external dependencies)")
