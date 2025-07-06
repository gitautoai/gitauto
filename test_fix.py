#!/usr/bin/env python3
from utils.files.is_test_file import is_test_file

# Test the specific cases that were failing
test_cases = [
    "cypress/integration/login.js",
    "e2e/login.spec.ts", 
    "playwright/tests/login.spec.ts",
    "testing/utils.py",
    # Unicode test cases
    "test-file.py",
    "file-test.py", 
    "src/test-utils/component.js",
    # Unicode test cases
    "tést_file.py",
    "file_tést.py",
    "src/tést/utils.py"
]

for case in test_cases:
    result = is_test_file(case)
    print(f"{case}: {result}")
