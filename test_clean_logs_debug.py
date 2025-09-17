#!/usr/bin/env python3
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from config import UTF8
from utils.logs.clean_logs import clean_logs

print("Testing clean_logs function...")

try:
    # Read the test files
    with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
        original_log = f.read()

    with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
        expected_output = f.read()

    print(f"Original log length: {len(original_log)}")
    print(f"Expected output length: {len(expected_output)}")

    # Run clean_logs
    result = clean_logs(original_log)
    print(f"Result length: {len(result)}")
    print(f"Match: {result == expected_output}")

    if result != expected_output:
        # Find first difference
        for i, (a, b) in enumerate(zip(result, expected_output)):
            if a != b:
                print(f"\nFirst difference at character {i}:")
                print(f"Result char: {repr(a)}")
                print(f"Expected char: {repr(b)}")

                # Show some context
                start = max(0, i - 30)
                end = min(len(result), i + 30)
                print(f"\nResult context:")
                print(repr(result[start:end]))

                end_exp = min(len(expected_output), i + 30)
                print(f"\nExpected context:")
                print(repr(expected_output[start:end_exp]))
                break

        # Check if it's just a length difference
        if len(result) != len(expected_output):
            print(f"\nLength difference: result={len(result)}, expected={len(expected_output)}")
            if len(result) < len(expected_output):
                print("Result is shorter than expected")
                print(f"Missing content: {repr(expected_output[len(result):])}")
            else:
                print("Result is longer than expected")
                print(f"Extra content: {repr(result[len(expected_output):])}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
