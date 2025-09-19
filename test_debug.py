import sys
sys.path.append('.')
from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test the failing case
log = """Before content
=========================== test session starts ============================
platform linux
collected items
test results
After content"""

expected = """Before content
After content"""

result = remove_pytest_sections(log)
print('Result:')
print(repr(result))
print('\nExpected:')
print(repr(expected))
print('\nMatch:', result == expected)

print('\nResult lines:')
for i, line in enumerate(result.split('\n')):
    print(f"{i}: {repr(line)}")
