#!/usr/bin/env python3
import subprocess
import sys

# Run the specific failing test
result = subprocess.run([
    sys.executable, "-m", "pytest", 
    "services/github/check_suites/test_get_circleci_workflow_id.py::test_get_circleci_workflow_ids_http_error_exception", 
    "-v"
], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
