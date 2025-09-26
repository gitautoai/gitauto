from config import UTF8
from utils.logs.clean_logs import clean_logs

# Test the clean_logs function with the actual payload
with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
    original_log = f.read()

with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
    expected_output = f.read()

result = clean_logs(original_log)

print(f"Original length: {len(original_log)}")
print(f"Expected length: {len(expected_output)}")
print(f"Result length: {len(result)}")
print(f"Match: {result == expected_output}")

if result != expected_output:
    print("First 1000 chars of result:")
    print(repr(result[:1000]))
