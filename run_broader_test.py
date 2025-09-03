#!/usr/bin/env python3
import subprocess
import sys

# Run all tests in the handle_exceptions module to make sure we didn't break anything
result = subprocess.run([
    sys.executable, "-m", "pytest", 
    "utils/error/test_handle_exceptions.py", 
    "-v"
], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")