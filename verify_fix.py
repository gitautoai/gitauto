#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.getcwd())

from utils.files.should_skip_ruby import should_skip_ruby

# Test the exact failing case
content = """API_BASE_URL = 'https://api.example.com'
API_VERSION = 'v1'
FULL_API_URL = "#{API_BASE_URL}/#{API_VERSION}"
CONFIG_HASH = {
  timeout: 30,
  retries: 3
}"""

result = should_skip_ruby(content)
print(f"Test result: {result}")
print(f"Expected: True")
print(f"Test passes: {result is True}")

if result is True:
    print("✅ Fix successful!")
else:
    print("❌ Fix failed!")
