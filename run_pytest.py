#!/usr/bin/env python3
import os
import subprocess
import sys

# Run pytest on the remove_pytest_sections tests
print("Running pytest on utils/logs/test_remove_pytest_sections.py...")

result = subprocess.run([
    sys.executable, "-m", "pytest",
    "utils/logs/test_remove_pytest_sections.py",
    "-v", "--tb=line", "--no-header"
], cwd=os.getcwd())

print(f"\nReturn code: {result.returncode}")

# Also run the clean_logs test
print("\n" + "="*60)
print("Running pytest on utils/logs/test_clean_logs.py::test_clean_logs_with_pytest_output...")

result2 = subprocess.run([
    sys.executable, "-m", "pytest",
    "utils/logs/test_clean_logs.py::test_clean_logs_with_pytest_output",
    "-v", "--tb=line", "--no-header"
], cwd=os.getcwd())

print(f"\nReturn code: {result2.returncode}")
