from config import UTF8
from utils.logs.clean_logs import clean_logs

def test_clean_logs_with_pytest_output():
    try:
        with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
            original_log = f.read()

        with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
            expected_output = f.read()

        result = clean_logs(original_log)
        match = result == expected_output
        print("clean_logs test:", match)

        if not match:
            print("Result length:", len(result))
            print("Expected length:", len(expected_output))
            # Find first difference
            for i, (a, b) in enumerate(zip(result, expected_output)):
                if a != b:
                    print(f"First difference at character {i}: got {repr(a)}, expected {repr(b)}")
                    break
        return match
    except Exception as e:
        print("clean_logs test failed with exception:", e)
        return False

if __name__ == "__main__":
    test_clean_logs_with_pytest_output()
