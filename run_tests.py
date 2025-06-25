#!/usr/bin/env python3
"""
Simple test runner to verify the new unit tests work correctly.
"""

import subprocess
import sys

def run_tests():
    """Run the new unit tests for the files changed in PR #1038."""
    test_files = [
        "tests/services/test_chat_with_agent.py",
        "tests/services/webhook/test_check_run_handler.py", 
        "tests/services/webhook/test_issue_handler.py",
        "tests/services/webhook/test_push_handler.py",
        "tests/services/webhook/test_review_run_handler.py"
    ]
    
    for test_file in test_files:
        print(f"\n{'='*60}")
        print(f"Running tests in {test_file}")
        print('='*60)
        subprocess.run([sys.executable, "-m", "pytest", test_file, "-v"], check=False)

if __name__ == "__main__":
    run_tests()
