#!/usr/bin/env python3
import subprocess
import sys
import os

# Run all tests in the logs module
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "utils/logs/",
    "-v"
], cwd=os.getcwd())

print(f"Return code: {result.returncode}")
if result.returncode == 0:
    print("✓ All logs module tests passed!")
