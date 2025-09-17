#!/usr/bin/env python3
import subprocess
import sys
import os

# Run the specific failing test
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "utils/logs/test_remove_pytest_sections.py::test_remove_pytest_sections_only_test_session_starts",
    "-v"
], cwd=os.getcwd())

print(f"Return code: {result.returncode}")
if result.returncode == 0:
    print("✓ Test passed!")
