import sys
sys.path.append('.')
from utils.files.should_skip_ruby import should_skip_ruby

# Test the failing case
content = """API_BASE_URL = 'https://api.example.com'
API_VERSION = 'v1'
FULL_API_URL = "#{API_BASE_URL}/#{API_VERSION}"
CONFIG_HASH = {
  timeout: 30,
  retries: 3
}"""

result = should_skip_ruby(content)
print(f'Result: {result}, Expected: True, Test passes: {result is True}')