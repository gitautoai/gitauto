#!/usr/bin/env python3
"""Temporary test runner to verify our tests work."""

import subprocess
import sys

def run_tests():
    """Run the search_remote_file_contents tests."""
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "services/github/search/test_search_remote_file_contents.py", 
            "-v"
        ], capture_output=True, text=True, cwd=".")
        
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
