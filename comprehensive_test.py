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
if test_case("Complex constant expressions (original failing case)", content1, True):
    tests_passed += 1

# Test 2: Inline comments
total_tests += 1
content2 = """MAX_RETRIES = 3 # Maximum retry attempts
API_URL = 'https://api.example.com' # Base API URL"""
if test_case("Inline comments", content2, True):
    tests_passed += 1

# Test 3: Single line hash
total_tests += 1
content3 = """DEFAULT_CONFIG = { debug: true }"""
if test_case("Single line hash", content3, True):
    tests_passed += 1

# Test 4: Should not skip - has method call
total_tests += 1
content4 = """CONFIG_HASH = {
  timeout: 30
}
puts "Hello" """
if test_case("Multi-line hash with method call (should not skip)", content4, False):
    tests_passed += 1

# Test 5: Only comments
total_tests += 1
content5 = """# This is a comment
# Another comment"""
if test_case("Only comments", content5, True):
    tests_passed += 1

# Test 6: Requires and constants
total_tests += 1
content6 = """require 'json'
MAX_RETRIES = 3
autoload :Parser, 'parser'"""
if test_case("Mixed requires, constants, and autoload", content6, True):
    tests_passed += 1

# Test 7: String with hash symbol but not interpolation
total_tests += 1
content7 = """API_KEY = 'secret#key'"""
if test_case("String with hash symbol", content7, True):
    tests_passed += 1

print(f"\n📊 Results: {tests_passed}/{total_tests} tests passed")

if tests_passed == total_tests:
    print("🎉 All tests passed! The fix should work.")
else:
    print("💥 Some tests failed. Need to investigate further.")
