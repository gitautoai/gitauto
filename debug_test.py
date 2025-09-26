from config import UTF8
from utils.logs.clean_logs import clean_logs

def debug_clean_logs():
    with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
        original_log = f.read()

    with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
        expected_output = f.read()

    result = clean_logs(original_log)

    print("=== RESULT ===")
    print(repr(result[:1000]))
    print("\n=== EXPECTED ===")
    print(repr(expected_output[:1000]))
    print(f"\nEqual: {result == expected_output}")

if __name__ == "__main__":
    debug_clean_logs()
