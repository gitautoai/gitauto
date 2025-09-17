from utils.logs.clean_logs import clean_logs
from config import UTF8

def debug_clean_logs():
    with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
        original_log = f.read()

    with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
        expected_output = f.read()

    result = clean_logs(original_log)

    print("=== RESULT ===")
    print(repr(result[-500:]))  # Last 500 chars
    print("\n=== EXPECTED ===")
    print(repr(expected_output[-500:]))  # Last 500 chars
    print(f"\nResult length: {len(result)}")
    print(f"Expected length: {len(expected_output)}")

debug_clean_logs()
