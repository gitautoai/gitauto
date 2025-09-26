#!/usr/bin/env python3

from config import UTF8
from utils.logs.remove_pytest_sections import remove_pytest_sections


def test_remove_pytest_sections():
    # Read the original log
    with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
        original_log = f.read()

    # Read the expected output
    with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
        expected_output = f.read()

    # Process the log
    result = remove_pytest_sections(original_log)

    # Compare
    print("Original length:", len(original_log))
    print("Expected length:", len(expected_output))
    print("Result length:", len(result))
    print()

    if result == expected_output:
        print("✅ Test PASSED!")
    else:
        print("❌ Test FAILED!")
        print("\n--- EXPECTED ---")
        print(repr(expected_output[:500]))
        print("\n--- ACTUAL ---")
        print(repr(result[:500]))

        # Find first difference
        for i, (a, b) in enumerate(zip(expected_output, result)):
            if a != b:
                print(f"\nFirst difference at position {i}:")
                print(f"Expected: {repr(a)}")
                print(f"Actual: {repr(b)}")
                print(f"Context: {repr(expected_output[max(0, i-20):i+20])}")
                break

if __name__ == "__main__":
    test_remove_pytest_sections()
