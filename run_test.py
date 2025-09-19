#!/usr/bin/env python3

import subprocess
import sys

# Run the specific failing test
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "utils/logs/test_clean_logs.py::test_clean_logs_with_pytest_output",
    "-v"
], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
