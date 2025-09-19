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
    looks_like_regular_content = (
        # Must not contain pytest-specific keywords
        not any(keyword in stripped_line.lower() for keyword in [
            'platform', 'cachedir', 'rootdir', 'plugins', 'asyncio', 'collecting', 'collected',
            'test', 'pytest', 'passed', 'failed', 'skipped', 'error', 'warning', 'coverage'
        ]) and
        # Must not contain test patterns
        '::' not in stripped_line and
        '%]' not in stripped_line and
        # Should be a simple phrase (not too complex)
        len(stripped_line.split()) <= 4 and
        # Should not start with common pytest prefixes
        not stripped_line.startswith(('  ', '\t'))
    )
    print(f"'{line}' -> looks_like_regular_content: {looks_like_regular_content}")
