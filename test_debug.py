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

# Let's also test the logic for each line in the pytest section
print('\nTesting each line:')
test_lines = ['platform linux', 'collected items', 'test results', 'After content']
for line in test_lines:
    stripped_line = line.strip()
    is_pytest_output = (
        stripped_line.startswith(('platform ', 'cachedir:', 'rootdir:', 'plugins:', 'asyncio:', 'collecting')) or
        'collected' in stripped_line.lower() or
        '::' in stripped_line or
        any(pattern in stripped_line for pattern in ['PASSED', 'FAILED', 'SKIPPED', 'ERROR', '%]', 'warnings']) or
        stripped_line.lower().startswith(('test ', 'tests '))
    )
    print(f"'{line}' -> is_pytest_output: {is_pytest_output}")
