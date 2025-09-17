from utils.logs.remove_pytest_sections import remove_pytest_sections
from config import UTF8

def test_just_pytest():
    with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
        original_log = f.read()

    result = remove_pytest_sections(original_log)

    # Check if the problematic lines are still there
    if "handle_coverage_report(" in result:
        print("ERROR: handle_coverage_report( is still in the result")
    if "Enable tracemalloc" in result:
        print("ERROR: Enable tracemalloc is still in the result")
    if "Coverage LCOV written to file" in result:
        print("ERROR: Coverage LCOV written to file is still in the result")

    print("Test completed")

test_just_pytest()
