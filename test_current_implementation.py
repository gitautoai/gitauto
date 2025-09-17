#!/usr/bin/env python3
import os
import subprocess
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("Testing current implementation...")

# Test 1: Run the remove_pytest_sections tests
print("\n1. Running remove_pytest_sections tests:")
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "utils/logs/test_remove_pytest_sections.py",
    "-v", "--tb=short"
], capture_output=True, text=True, cwd=os.getcwd())

print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)
print(f"Return code: {result.returncode}")

# Test 2: Run the clean_logs test
print("\n2. Running clean_logs test:")
result2 = subprocess.run([
    sys.executable, "-m", "pytest",
    "utils/logs/test_clean_logs.py::test_clean_logs_with_pytest_output",
    "-v", "--tb=short"
], capture_output=True, text=True, cwd=os.getcwd())

print("STDOUT:")
print(result2.stdout)
if result2.stderr:
    print("STDERR:")
    print(result2.stderr)
print(f"Return code: {result2.returncode}")

# Test 3: Manual test of the function
print("\n3. Manual test:")
try:
    from utils.logs.remove_pytest_sections import remove_pytest_sections

    # Test None
    result = remove_pytest_sections(None)
    print(f"None test: {result} (type: {type(result)}) - Pass: {result is None}")

    # Test empty
    result = remove_pytest_sections("")
    print(f"Empty test: {repr(result)} (type: {type(result)}) - Pass: {result == ''}")

    # Test basic functionality
    log = """Run python -m pytest
=========================== test session starts ============================
platform linux -- Python 3.11.4, pytest-7.4.0, pluggy-1.2.0
test content
=================================== FAILURES ===================================
failure content"""

    expected = """Run python -m pytest

=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    print(f"Basic test - Pass: {result == expected}")
    if result != expected:
        print(f"  Result: {repr(result)}")
        print(f"  Expected: {repr(expected)}")

except Exception as e:
    print(f"Manual test failed: {e}")
