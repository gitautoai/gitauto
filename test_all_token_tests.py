#!/usr/bin/env python3
import subprocess
import sys

def run_tests():
    """Run all tests in the token module to check for regressions"""
    cmd = [
        sys.executable, "-m", "pytest", 
        "services/github/token/test_get_installation_token.py",
        "-v", "--tb=short"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)

if __name__ == "__main__":
    run_tests()