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

print("Testing the failing case...")
result = should_skip_ruby(content)
print(f"Result: {result}")
print(f"Expected: True")

if result is True:
    print("✅ SUCCESS: The fix works!")
else:
    print("❌ FAILED: The fix didn't work")

# Test inline comments case too
content2 = """MAX_RETRIES = 3 # Maximum retry attempts"""
result2 = should_skip_ruby(content2)
print(f"\nInline comments test: {result2} (expected: True)")
