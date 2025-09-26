#!/usr/bin/env python3

from utils.logs.remove_pytest_sections import remove_pytest_sections


def test_basic_functionality():
    """Test basic functionality with a simple case"""
    log = """Initial content
========================= test session starts ==========================
platform linux -- Python 3.12.11, pytest-8.3.3, pluggy-1.5.0
rootdir: /home/runner/work/gitauto/gitauto
plugins: cov-6.0.0, anyio-4.4.0, Faker-24.14.1, asyncio-0.26.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 2900 items

services/anthropic/test_evaluate_condition.py .......                    [  0%]
services/anthropic/test_exceptions.py ................                   [  0%]

=================================== FAILURES ===================================
failure content"""

    expected = """Initial content

=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    print("Expected:")
    print(repr(expected))
    print("\nActual:")
    print(repr(result))
    print("\nMatch:", result == expected)

    return result == expected

def test_real_log():
    """Test with the real log files"""
    from config import UTF8
    from utils.logs.clean_logs import clean_logs

    # Read the original log
    with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
        original_log = f.read()

    # Read the expected output
    with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
        expected_output = f.read()

    # Process the log using clean_logs (which calls remove_pytest_sections)
    result = clean_logs(original_log)

    print(f"Real log test - Match: {result == expected_output}")

    if result != expected_output:
        # Find first difference
        min_len = min(len(expected_output), len(result))
        for i in range(min_len):
            if expected_output[i] != result[i]:
                print(f"First difference at position {i}:")
                print(f"Expected: {repr(expected_output[i])}")
                print(f"Actual: {repr(result[i])}")
                print(f"Expected context: {repr(expected_output[max(0, i-50):i+50])}")
                print(f"Actual context: {repr(result[max(0, i-50):i+50])}")
                break

    return result == expected_output

if __name__ == "__main__":
    print("Testing basic functionality...")
    basic_ok = test_basic_functionality()
    print(f"Basic test: {'✅ PASSED' if basic_ok else '❌ FAILED'}")

    print("\nTesting real log...")
    real_ok = test_real_log()
    print(f"Real log test: {'✅ PASSED' if real_ok else '❌ FAILED'}")

    if basic_ok and real_ok:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")
