#!/usr/bin/env python3
import subprocess
import sys
import os

# Run all remove_pytest_sections tests
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "utils/logs/test_remove_pytest_sections.py",
    "-v", "--tb=short"
], capture_output=True, text=True, cwd=os.getcwd())

print("STDOUT:")
print(result.stdout)
print(f"Return code: {result.returncode}")
