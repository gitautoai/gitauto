#!/usr/bin/env python3
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from config import UTF8
from utils.logs.deduplicate_logs import deduplicate_logs
from utils.logs.remove_ansi_escape_codes import remove_ansi_escape_codes
from utils.logs.remove_pytest_sections import remove_pytest_sections
from utils.logs.remove_repetitive_eslint_warnings import \
    remove_repetitive_eslint_warnings

# Read the test files
with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
    original_log = f.read()

with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
    expected_output = f.read()

print("Step-by-step debugging of clean_logs function:")
print(f"Original length: {len(original_log)}")

# Step 1: remove_pytest_sections
step1 = remove_pytest_sections(original_log)
print(f"After remove_pytest_sections: {len(step1)}")
print(f"Matches expected: {step1 == expected_output}")

if step1 != expected_output:
    print("Step 1 doesn't match expected output!")
    # Find first difference
    for i, (a, b) in enumerate(zip(step1, expected_output)):
        if a != b:
            print(f"First difference at character {i}: got {repr(a)}, expected {repr(b)}")
            # Show context
            start = max(0, i - 20)
            end = min(len(step1), i + 20)
            print(f"Context: {repr(step1[start:end])}")
            break

    if len(step1) != len(expected_output):
        print(f"Length difference: step1={len(step1)}, expected={len(expected_output)}")

# Step 2: remove_repetitive_eslint_warnings
step2 = remove_repetitive_eslint_warnings(step1)
print(f"After remove_repetitive_eslint_warnings: {len(step2)}")

# Step 3: remove_ansi_escape_codes
step3 = remove_ansi_escape_codes(step2)
print(f"After remove_ansi_escape_codes: {len(step3)}")

# Step 4: deduplicate_logs
step4 = deduplicate_logs(step3)
print(f"After deduplicate_logs: {len(step4)}")

print(f"Final result matches expected: {step4 == expected_output}")

# Let's also test just the remove_pytest_sections function with a smaller sample
print("\n" + "="*50)
print("Testing remove_pytest_sections with first 50 lines:")

lines = original_log.split('\n')
sample = '\n'.join(lines[:50])
print(f"Sample length: {len(sample)}")

sample_result = remove_pytest_sections(sample)
print(f"Sample result length: {len(sample_result)}")
print("Sample result:")
for i, line in enumerate(sample_result.split('\n')):
    print(f"{i+1:2d}: {repr(line)}")
