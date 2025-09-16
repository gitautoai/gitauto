#!/usr/bin/env python3
import subprocess
import sys

# Run the specific failing test
result = subprocess.run([
    sys.executable, "-m", "pytest", "-xvs", "utils/files/test_should_skip_rust.py::test_const_with_array_access_pattern_in_string"
], capture_output=True, text=True)
