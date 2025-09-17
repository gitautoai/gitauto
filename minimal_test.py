# Test the current implementation
import sys
sys.path.append('.')

from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test None input
result = remove_pytest_sections(None)
print("None test:", result, type(result))

# Test empty string
result = remove_pytest_sections("")
print("Empty test:", result, type(result))

# Test simple case
simple_log = "Some content\n=== test session starts ===\ntest content\n=== FAILURES ===\nfailure content"
result = remove_pytest_sections(simple_log)
print("Simple test result:")
print(repr(result))
