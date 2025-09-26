from config import UTF8
from utils.logs.remove_pytest_sections import remove_pytest_sections

def test_debug():
    with open(
        "payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8
    ) as f:
        original_log = f.read()

    with open(
        "payloads/github/workflow_runs/test_failure_log_cleaned.txt", "r", encoding=UTF8
    ) as f:
        expected_output = f.read()

    result = remove_pytest_sections(original_log)

    print("Expected length:", len(expected_output))
    print("Result length:", len(result))
    print("Match:", result == expected_output)

    # Find first difference
    for i, (a, b) in enumerate(zip(result, expected_output)):
        if a != b:
            print(f"First difference at position {i}: got '{a}' expected '{b}'")
            print(f"Context: '{result[max(0, i-20):i+20]}'")
            break

    if len(result) != len(expected_output):
        print(f"Length difference: result={len(result)}, expected={len(expected_output)}")
        if len(result) > len(expected_output):
            print(f"Extra content in result: '{result[len(expected_output):]}'")
        else:
            print(f"Missing content in result: '{expected_output[len(result):]}'")

if __name__ == "__main__":
    test_debug()
