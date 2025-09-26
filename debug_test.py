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

# Compare line by line
result_lines = result.split('\n')
expected_lines = expected_output.split('\n')

print(f"Result has {len(result_lines)} lines")
print(f"Expected has {len(expected_lines)} lines")

# Find first difference
for i, (result_line, expected_line) in enumerate(zip(result_lines, expected_lines)):
    if result_line != expected_line:
        print(f"First difference at line {i+1}:")
        print(f"Result:   '{result_line}'")
        print(f"Expected: '{expected_line}'")
        break
else:
    print("All lines match!")
