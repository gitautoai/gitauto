#!/usr/bin/env python3
import subprocess
import sys

# Run all tests for the should_skip_rust module
result = subprocess.run([
    sys.executable, "-m", "pytest", "-xvs", "utils/files/test_should_skip_rust.py"
], capture_output=True, text=True)
