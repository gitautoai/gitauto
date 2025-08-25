#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.getcwd())

from utils.files.should_skip_ruby import should_skip_ruby

def test_case(name, content, expected):
    result = should_skip_ruby(content)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    print(f"{status}: {name}")
    if result != expected:
        print(f"  Expected: {expected}, Got: {result}")
        print(f"  Content: {repr(content)}")
    return result == expected

tests_passed = 0
total_tests = 0

# Test 1: The original failing case
total_tests += 1
content1 = """API_BASE_URL = 'https://api.example.com'
API_VERSION = 'v1'
FULL_API_URL = "#{API_BASE_URL}/#{API_VERSION}"
CONFIG_HASH = {
  timeout: 30,
  retries: 3
}"""
if test_case("Complex constant expressions", content1, True):
    tests_passed += 1

# Test 2: Inline comments (existing test that should still pass)
total_tests += 1
content2 = """MAX_RETRIES = 3 # Maximum retry attempts
API_URL = 'https://api.example.com' # Base API URL
DEBUG_MODE = true # Enable debug logging"""
if test_case("Inline comments with constants", content2, True):
    tests_passed += 1

# Test 3: Should not skip - has method call
total_tests += 1
content3 = """CONFIG_HASH = {
  timeout: 30,
  retries: 3
}
puts "Hello" """
if test_case("Multi-line hash with method call", content3, False):
    tests_passed += 1

# Test 4: Single line hash (should still work)
total_tests += 1
content4 = """DEFAULT_CONFIG = { debug: true }"""
if test_case("Single line hash", content4, True):
    tests_passed += 1

print(f"\n📊 Results: {tests_passed}/{total_tests} tests passed")

if tests_passed == total_tests:
    print("🎉 All tests passed!")
    sys.exit(0)
else:
    print("💥 Some tests failed!")
    sys.exit(1)
