#!/usr/bin/env python3
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from config import UTF8
from utils.logs.clean_logs import clean_logs

# Read the files
with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
    original_log = f.read()

with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
    expected_output = f.read()

# Run clean_logs
result = clean_logs(original_log)

print(f"Original length: {len(original_log)}")
print(f"Expected length: {len(expected_output)}")
print(f"Result length: {len(result)}")
print(f"Match: {result == expected_output}")

if result != expected_output:
    # Find first difference
    for i, (a, b) in enumerate(zip(result, expected_output)):
        if a != b:
            print(f"\nFirst difference at character {i}:")
            print(f"Result char: {repr(a)}")
            print(f"Expected char: {repr(b)}")

            # Show context
            start = max(0, i - 50)
            end = min(len(result), i + 50)
            print(f"\nResult context ({start}-{end}):")
            print(repr(result[start:end]))

            end_exp = min(len(expected_output), i + 50)
            print(f"\nExpected context ({start}-{end_exp}):")
            print(repr(expected_output[start:end_exp]))
            break

    if len(result) != len(expected_output):
        print(f"\nLength difference: result has {len(result)} chars, expected has {len(expected_output)} chars")
