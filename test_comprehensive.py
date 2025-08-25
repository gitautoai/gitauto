import sys
sys.path.append('.')
from utils.files.should_skip_ruby import should_skip_ruby

def test_case(name, content, expected):
    result = should_skip_ruby(content)
    status = "PASS" if result == expected else "FAIL"
    print(f"{status}: {name} - Expected: {expected}, Got: {result}")
    return result == expected

# Test cases
all_passed = True

# The failing case
content1 = """API_BASE_URL = 'https://api.example.com'
API_VERSION = 'v1'
FULL_API_URL = "#{API_BASE_URL}/#{API_VERSION}"
CONFIG_HASH = {
  timeout: 30,
  retries: 3
}"""
all_passed &= test_case("Complex constant expressions", content1, True)

# Single line hash (should still work)
content2 = """DEFAULT_CONFIG = { debug: true }"""
all_passed &= test_case("Single line hash", content2, True)

# Inline comments (should still work)
content3 = """MAX_RETRIES = 3 # Maximum retry attempts
API_URL = 'https://api.example.com' # Base API URL"""
all_passed &= test_case("Inline comments", content3, True)

# Mixed with requires (should still work)
content4 = """require 'json'
CONFIG_HASH = {
  timeout: 30,
  retries: 3
}"""
all_passed &= test_case("Mixed requires and multi-line hash", content4, True)

# Should not skip - has method call
content5 = """CONFIG_HASH = {
  timeout: 30,
  retries: 3
}
puts "Hello" """
all_passed &= test_case("Multi-line hash with method call", content5, False)

print(f"\nAll tests passed: {all_passed}")
