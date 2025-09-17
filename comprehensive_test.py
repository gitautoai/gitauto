from utils.logs.clean_logs import clean_logs
from config import UTF8

def test_clean_logs():
    with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
        original_log = f.read()

    with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
        expected_output = f.read()

    result = clean_logs(original_log)

    # Find the first difference
    for i, (r, e) in enumerate(zip(result, expected_output)):
        if r != e:
            print(f"First difference at position {i}: got {repr(r)}, expected {repr(e)}")
            print(f"Context: {repr(result[max(0, i-50):i+50])}")
            break

    print(f"Result length: {len(result)}, Expected length: {len(expected_output)}")
    print(f"Match: {result == expected_output}")

test_clean_logs()
