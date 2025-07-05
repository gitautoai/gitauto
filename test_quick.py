#!/usr/bin/env python3
import sys
sys.path.append('.')

from services.coverages.parse_lcov_coverage import parse_lcov_coverage

# Test the exact malformed content from the failing test
lcov_content = """SF:src/malformed.py
FN:invalid_line
FNDA:not_a_number,func
BRDA:invalid_branch_data
DA:not_a_line,1
FN:10,20,30,too_many_parts
FNF:1
FNH:1
DA:10,1
LF:1
LH:1
end_of_record
"""

print("Testing malformed lines...")
try:
    result = parse_lcov_coverage(lcov_content)
    print(f"Malformed content result: {len(result)} reports")
    for i, report in enumerate(result):
        print(f"Report {i}: {report['level']} - {report['full_path']}")
    
    # Test the specific assertion from the failing test
    if len(result) == 3:
        print("✅ Test would PASS: len(result) == 3")
    else:
        print(f"❌ Test would FAIL: len(result) == {len(result)}, expected 3")
        
except Exception as e:
    print(f"❌ Exception occurred: {e}")
    print("Test would FAIL due to exception")

# Test empty content to make sure we didn't break anything
print("\nTesting empty content...")
try:
    result = parse_lcov_coverage("")
    print(f"Empty content result: {len(result)} reports")
    if len(result) == 1:
        print("✅ Empty content test would PASS")
    else:
        print(f"❌ Empty content test would FAIL: expected 1, got {len(result)}")
except Exception as e:
    print(f"❌ Exception occurred with empty content: {e}")