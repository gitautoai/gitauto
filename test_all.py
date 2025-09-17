#!/usr/bin/env python3
import subprocess
import sys
import os

# Run all remove_pytest_sections tests
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "utils/logs/test_remove_pytest_sections.py",
    "-v"
], cwd=os.getcwd())

print(f"Return code: {result.returncode}")
if result.returncode == 0:
    print("✓ All tests passed!")
