#!/usr/bin/env python3
"""
Simple test runner to verify the should_test_file tests work correctly.
This file can be deleted after verification.
"""

import subprocess
import sys

def run_tests():
    """Run the tests for should_test_file.py"""
    try:
        # Run pytest on the specific test file
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "utils/files/test_should_test_file.py", 
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)