import asyncio
import os
import sys

sys.path.insert(0, "/app")

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
