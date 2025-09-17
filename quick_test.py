from utils.logs.clean_logs import clean_logs
from config import UTF8

# Quick test to see if the problematic content is removed
with open("payloads/github/workflow_runs/test_failure_log.txt", "r", encoding=UTF8) as f:
    original_log = f.read()

result = clean_logs(original_log)

# Check if problematic content is removed
problematic_content = [
    "handle_coverage_report(",
    "Enable tracemalloc",
    "Coverage LCOV written to file"
]

for content in problematic_content:
    if content in result:
        print(f"FAIL: '{content}' is still present")
    else:
        print(f"PASS: '{content}' was removed")

print(f"\nOriginal length: {len(original_log)}")
print(f"Result length: {len(result)}")
