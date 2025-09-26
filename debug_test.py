#!/usr/bin/env python3

from config import UTF8
from utils.logs.clean_logs import clean_logs


def test_clean_logs_with_pytest_output():
    # Read the original log
    with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
        original_log = f.read()

    # Read the expected output
    with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
        expected_output = f.read()

    # Process the log using clean_logs (which calls remove_pytest_sections)
    result = clean_logs(original_log)

    # Compare
    print("Original length:", len(original_log))
    print("Expected length:", len(expected_output))
    print("Result length:", len(result))
    print()

    if result == expected_output:
        print("✅ Test PASSED!")
        return True
    else:
        print("❌ Test FAILED!")

        # Find first difference
        min_len = min(len(expected_output), len(result))
        for i in range(min_len):
            if expected_output[i] != result[i]:
                print(f"\nFirst difference at position {i}:")
                print(f"Expected: {repr(expected_output[i])}")
                print(f"Actual: {repr(result[i])}")
                print(f"Expected context: {repr(expected_output[max(0, i-30):i+30])}")
                print(f"Actual context: {repr(result[max(0, i-30):i+30])}")
                break

        if len(expected_output) != len(result):
            print(f"\nLength difference: expected {len(expected_output)}, got {len(result)}")
            if len(result) > len(expected_output):
                print(f"Extra content in result: {repr(result[len(expected_output):len(expected_output)+100])}")
            else:
                print(f"Missing content in result: {repr(expected_output[len(result):len(result)+100])}")

        return False

if __name__ == "__main__":
    test_clean_logs_with_pytest_output()
