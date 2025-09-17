#!/usr/bin/env python3
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from config import UTF8

# Read the actual payload file and check the session starts line
with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
    lines = f.readlines()

print("Looking for 'test session starts' line...")
for i, line in enumerate(lines):
    if "test session starts" in line:
        print(f"Found at line {i+1}: {repr(line.rstrip())}")
        print(f"Contains '===': {'===' in line}")
        break
else:
    print("Not found!")

# Also check what comes after
print("\nFirst 20 lines of the file:")
for i, line in enumerate(lines[:20]):
    print(f"{i+1:2d}: {repr(line.rstrip())}")

# Test the function with just the first few lines
from utils.logs.remove_pytest_sections import remove_pytest_sections

test_log = "".join(lines[:15])  # First 15 lines
print(f"\nTesting with first 15 lines:")
print(f"Input length: {len(test_log)}")

result = remove_pytest_sections(test_log)
print(f"Output length: {len(result)}")
print(f"Output:")
for i, line in enumerate(result.split('\n')):
    print(f"{i+1:2d}: {repr(line)}")
