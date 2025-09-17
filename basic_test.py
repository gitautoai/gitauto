#!/usr/bin/env python3
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Import the function
try:
    from utils.logs.remove_pytest_sections import remove_pytest_sections
    print("✓ Successfully imported remove_pytest_sections")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test 1: Very simple case
print("\nTest 1: Simple case")
simple_input = """Before
=== test session starts ===
Remove this
=== FAILURES ===
Keep this"""

expected_simple = """Before

=== FAILURES ===
Keep this"""

result = remove_pytest_sections(simple_input)
print(f"Input: {repr(simple_input)}")
print(f"Expected: {repr(expected_simple)}")
print(f"Result: {repr(result)}")
print(f"Match: {result == expected_simple}")

# Test 2: Check the exact pattern from the payload
print("\nTest 2: Exact pattern from payload")
payload_pattern = """Run python -m pytest
============================= test session starts ==============================
platform linux -- Python 3.12.11, pytest-8.3.3, pluggy-1.5.0
=================================== FAILURES ===================================
Test failure"""

expected_payload = """Run python -m pytest

=================================== FAILURES ===================================
Test failure"""

result2 = remove_pytest_sections(payload_pattern)
print(f"Input: {repr(payload_pattern)}")
print(f"Expected: {repr(expected_payload)}")
print(f"Result: {repr(result2)}")
print(f"Match: {result2 == expected_payload}")

# Test 3: Check if the pattern matching works
print("\nTest 3: Pattern matching")
test_line = "============================= test session starts =============================="
print(f"Test line: {repr(test_line)}")
print(f"Contains '===': {'===' in test_line}")
print(f"Contains 'test session starts': {'test session starts' in test_line}")
print(f"Both conditions: {'===' in test_line and 'test session starts' in test_line}")

# Test 4: Step through the logic manually
print("\nTest 4: Manual step-through")
test_input = """Line 1
============================= test session starts ==============================
Line to remove
=================================== FAILURES ===================================
Line to keep"""

lines = test_input.split("\n")
filtered_lines = []
skip = False
content_removed = False

for i, line in enumerate(lines):
    print(f"Processing line {i}: {repr(line)}")

    # Start skipping at test session header
    if "===" in line and "test session starts" in line:
        print("  -> Starting to skip (test session starts)")
        skip = True
        content_removed = True
        continue

    # Stop skipping and keep failures section
    if "===" in line and "FAILURES" in line:
        print("  -> Stop skipping (FAILURES)")
        skip = False
        # Add blank line before FAILURES if we just removed content and last line isn't blank
        if content_removed and filtered_lines and filtered_lines[-1] != "":
            filtered_lines.append("")
            print("  -> Added blank line")
        filtered_lines.append(line)
        continue

    # Keep line if not skipping
    if not skip:
        print(f"  -> Keeping line: {repr(line)}")
        filtered_lines.append(line)
    else:
        print(f"  -> Skipping line: {repr(line)}")
        content_removed = True

print(f"\nFiltered lines: {filtered_lines}")
manual_result = "\n".join(filtered_lines)
print(f"Manual result: {repr(manual_result)}")
