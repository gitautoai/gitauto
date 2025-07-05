#!/usr/bin/env python3
import sys
sys.path.append('.')

from services.coverages.parse_lcov_coverage import parse_lcov_coverage

# Test empty content
result = parse_lcov_coverage("")
print(f"Empty content result: {len(result)} reports")
print(f"First result: {result[0] if result else 'None'}")