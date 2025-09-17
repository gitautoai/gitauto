from utils.logs.clean_logs import clean_logs
from config import UTF8

def test_clean_logs():
    with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
        original_log = f.read()

    with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
        expected_output = f.read()

    result = clean_logs(original_log)

    # Check specific problematic content
    problematic_lines = [
        "handle_coverage_report(",
        "Enable tracemalloc",
        "Coverage LCOV written to file",
        "-- Docs: https://docs.pytest.org/"
    ]

    for line in problematic_lines:
        if line in result:
            print(f"ERROR: '{line}' is still in the result")
        else:
            print(f"OK: '{line}' was removed")

    print(f"Result length: {len(result)}")
    print(f"Expected length: {len(expected_output)}")
    print(f"Match: {result == expected_output}")

test_clean_logs()
