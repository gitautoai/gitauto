#!/usr/bin/env python3
import subprocess
import sys
import os

# Run the clean_logs test that uses remove_pytest_sections
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "utils/logs/test_clean_logs.py::test_clean_logs_with_pytest_output",
    "-v"
], cwd=os.getcwd())

print(f"Return code: {result.returncode}")
if result.returncode == 0:
    print("✓ Clean logs test passed!")
