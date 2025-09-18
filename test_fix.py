import sys
sys.path.append('.')

from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test the specific failing case
log = """Initial content
=========================== warnings summary ============================
/path/to/file.py:10: DeprecationWarning: deprecated function
  deprecated_function()

Final content"""

expected = """Initial content

Final content"""

result = remove_pytest_sections(log)
print('Input:')
print(repr(log))
print()
print('Expected:')
print(repr(expected))
print()
print('Actual:')
print(repr(result))
print()
print('Match:', result == expected)
