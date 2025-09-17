#!/usr/bin/env python3
"""Run the specific failing test"""

import subprocess
import sys

# Run the specific test that was failing
result = subprocess.run([sys.executable, "-m", "pytest", "services/github/utils/test_deconstruct_github_payload.py::test_deconstruct_github_payload_success", "-v"], capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
