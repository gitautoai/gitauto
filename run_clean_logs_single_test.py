#!/usr/bin/env python3
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Import and run the clean_logs test
from utils.logs.test_clean_logs import test_clean_logs_with_pytest_output

try:
    test_clean_logs_with_pytest_output()
    print("✓ test_clean_logs_with_pytest_output passed")
except AssertionError as e:
    print("✗ test_clean_logs_with_pytest_output failed:")
    print(f"  {e}")
except Exception as e:
    print("✗ test_clean_logs_with_pytest_output error:")
    print(f"  {e}")
