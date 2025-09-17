from config import UTF8
from utils.logs.clean_logs import clean_logs

# Test the actual failing case
with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
    original_log = f.read()

with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
    expected_output = f.read()

result = clean_logs(original_log)

print("Match:", result == expected_output)
if result != expected_output:
    print("First difference at character:", next((i for i, (a, b) in enumerate(zip(result, expected_output)) if a != b), len(min(result, expected_output))))
    print("Result length:", len(result))
    print("Expected length:", len(expected_output))

    # Show first few lines of difference
    result_lines = result.split('\n')
    expected_lines = expected_output.split('\n')

    for i, (r_line, e_line) in enumerate(zip(result_lines, expected_lines)):
        if r_line != e_line:
            print(f"Line {i+1} differs:")
            print(f"Result:   {repr(r_line)}")
            print(f"Expected: {repr(e_line)}")
            break
