#!/usr/bin/env python3
"""
Run the agentic_ai unit tests inside the Docker container.
This script is copied into the container and executed there.

Usage:
    docker exec doclib_agentic_ai python /app/run_tests.py

It runs pytest with:
 - asyncio_mode=auto for async tests
 - Full verbosity and colored output
 - Saves results to /tmp/test_results.json
"""
import subprocess
import sys
import os

os.chdir("/app")

cmd = [
    sys.executable, "-m", "pytest",
    "/app/tests/",
    "-v",
    "--tb=short",
    "--asyncio-mode=auto",
    "--no-header",
    "-q",
    "--json-report",
    "--json-report-file=/tmp/test_results.json",
]

result = subprocess.run(cmd, capture_output=False)
sys.exit(result.returncode)
