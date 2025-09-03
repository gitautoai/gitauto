#!/usr/bin/env python3
import subprocess
import sys

# Run all tests in the get_circleci_workflow_id module
result = subprocess.run([
    sys.executable, "-m", "pytest", 
    "services/github/check_suites/test_get_circleci_workflow_id.py", 
    "-v"
], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")