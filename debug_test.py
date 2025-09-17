from config import UTF8
from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test with the actual payload
with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
    original_log = f.read()

with open("payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8) as f:
    expected_output = f.read()

result = remove_pytest_sections(original_log)

print("Match:", result == expected_output)
print("Result length:", len(result))
print("Expected length:", len(expected_output))

if result != expected_output:
    result_lines = result.split('\n')
    expected_lines = expected_output.split('\n')

    print(f"Result has {len(result_lines)} lines")
    print(f"Expected has {len(expected_lines)} lines")

    # Find first difference
    for i, (r_line, e_line) in enumerate(zip(result_lines, expected_lines)):
        if r_line != e_line:
            print(f"\nFirst difference at line {i+1}:")
            print(f"Result:   {repr(r_line)}")
            print(f"Expected: {repr(e_line)}")
            break

    # Show some context around the difference
    if i < len(result_lines):
        print(f"\nContext (lines {max(1, i-2)} to {min(len(result_lines), i+3)}):")
        for j in range(max(0, i-2), min(len(result_lines), i+3)):
            marker = ">>> " if j == i else "    "
            print(f"{marker}Line {j+1}: {repr(result_lines[j])}")

        print(f"\nExpected context:")
        for j in range(max(0, i-2), min(len(expected_lines), i+3)):
            marker = ">>> " if j == i else "    "
            print(f"{marker}Line {j+1}: {repr(expected_lines[j])}")
