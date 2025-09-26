from utils.logs.remove_pytest_sections import remove_pytest_sections
from config import UTF8

# Read the original log
with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
    original_log = f.read()

# Read the expected output
with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
    expected_output = f.read()

# Process the log
result = remove_pytest_sections(original_log)

print("Length comparison:")
print(f"Original: {len(original_log)}")
print(f"Result: {len(result)}")
print(f"Expected: {len(expected_output)}")
print(f"Match: {result == expected_output}")
print("Done!")
