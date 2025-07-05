#!/usr/bin/env python3
import sys
sys.path.append('.')

from services.coverages.parse_lcov_coverage import parse_lcov_coverage

# Test malformed content
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
result = parse_lcov_coverage(lcov_content)
print(f"Malformed content result: {len(result)} reports")
for i, report in enumerate(result):
    print(f"Report {i}: {report['level']} - {report['full_path']}")