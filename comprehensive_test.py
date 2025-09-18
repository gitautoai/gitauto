import sys
sys.path.append('.')

from utils.logs.remove_pytest_sections import remove_pytest_sections

def test_warnings_summary_only():
    log = """Initial content
=========================== warnings summary ============================
/path/to/file.py:10: DeprecationWarning: deprecated function
  deprecated_function()

Final content"""

    expected = """Initial content

Final content"""

    result = remove_pytest_sections(log)
    print('Test 1 - Warnings summary only:')
    print('Match:', result == expected)
    if result != expected:
        print('Expected:', repr(expected))
        print('Actual:', repr(result))
    print()

def test_session_starts_only():
    log = """Initial content
=========================== test session starts ============================
platform info
test results
Final content"""

    expected = """Initial content

Final content"""

    result = remove_pytest_sections(log)
    print('Test 2 - Session starts only:')
    print('Match:', result == expected)
    if result != expected:
        print('Expected:', repr(expected))
        print('Actual:', repr(result))
    print()

def test_with_failures():
    log = """Initial content
=========================== warnings summary ============================
warning content
=================================== FAILURES ===================================
failure content"""

    expected = """Initial content

=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    print('Test 3 - With failures (should work):')
    print('Match:', result == expected)
    if result != expected:
        print('Expected:', repr(expected))
        print('Actual:', repr(result))
    print()

if __name__ == "__main__":
    test_warnings_summary_only()
    test_session_starts_only()
    test_with_failures()
