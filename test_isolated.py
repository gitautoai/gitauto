from utils.logs.clean_logs import clean_logs
from utils.logs.remove_pytest_sections import remove_pytest_sections

# Read the actual test files
with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding="utf-8") as f:
    original_log = f.read()

with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding="utf-8") as f:
    expected_output = f.read()

print("TESTING remove_pytest_sections directly:")
result_pytest_only = remove_pytest_sections(original_log)
print(f"Length - Original: {len(original_log)}, After pytest removal: {len(result_pytest_only)}")

print("\nTESTING clean_logs (full pipeline):")
result_full = clean_logs(original_log)
print(f"Length - After full pipeline: {len(result_full)}")
print(f"Expected length: {len(expected_output)}")

print(f"\nFull pipeline matches expected: {result_full == expected_output}")
print(f"Pytest-only matches expected: {result_pytest_only == expected_output}")

# Check if the test session section is being removed
test_session_line = "============================= test session starts =============================="
if test_session_line in original_log:
    print(f"\nOriginal contains test session line: True")
    print(f"Pytest-only result contains test session line: {test_session_line in result_pytest_only}")
    print(f"Full pipeline result contains test session line: {test_session_line in result_full}")
    print(f"Expected contains test session line: {test_session_line in expected_output}")
else:
    print(f"\nOriginal does not contain exact test session line")
    # Check for variations
    for line in original_log.split('\n'):
        if 'test session starts' in line:
            print(f"Found test session line: {repr(line)}")
            print(f"Pytest-only result contains this line: {line in result_pytest_only}")
            print(f"Full pipeline result contains this line: {line in result_full}")
            print(f"Expected contains this line: {line in expected_output}")
            break

# Check for specific problematic lines
problematic_lines = [
    "asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function",
    "collected 2900 items"
]

for line in problematic_lines:
    print(f"\nLine: {repr(line)}")
    print(f"Original contains: {line in original_log}")
    print(f"Pytest-only result contains: {line in result_pytest_only}")
    print(f"Full pipeline result contains: {line in result_full}")
    print(f"Expected contains: {line in expected_output}")
