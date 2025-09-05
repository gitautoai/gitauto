#!/usr/bin/env python3

from utils.files.is_test_file import is_test_file

# Test the specific failing case
test_cases = [
    "cypress/integration/login.js",
    "e2e/login.spec.ts", 
    "playwright/tests/login.spec.ts",
    "spec/models/user_spec.rb",
    "testing/utils.py"
]

for case in test_cases:
    print(f"is_test_file('{case}') = {is_test_file(case)}")