#!/usr/bin/env python3
import subprocess
import sys

def run_test():
    """Run the specific failing test to check if it's fixed"""
    cmd = [
        sys.executable, "-m", "pytest", 
        "services/github/token/test_get_installation_token.py::test_get_installation_access_token_rate_limit_403",
        "-v", "--tb=short"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)

if __name__ == "__main__":
    run_test()
