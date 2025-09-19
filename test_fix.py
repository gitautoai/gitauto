from utils.logs.remove_pytest_sections import remove_pytest_sections


def test_fix():
    log = """Before content
=========================== test session starts ============================
platform linux
collected items
test results
After content"""

    expected = """Before content
After content"""

    result = remove_pytest_sections(log)
    print(f"Expected: {repr(expected)}")
    print(f"Got: {repr(result)}")
    print(f"Match: {result == expected}")

def test_warnings_fix():
    log = """Before content
=========================== warnings summary ============================
warning 1
warning 2
After content"""

    expected = """Before content
After content"""

    result = remove_pytest_sections(log)
    print(f"Warnings test - Expected: {repr(expected)}")
    print(f"Warnings test - Got: {repr(result)}")
    print(f"Warnings test - Match: {result == expected}")

def test_debug():
    # Test the specific lines
    print("Testing 'warning 1':")
    print(f"  Contains 'warning': {'warning' in 'warning 1'.lower()}")
    print(f"  Starts with space: {'warning 1'.startswith((' ', '\t'))}")

    print("Testing 'After content':")
    pytest_keywords = ['platform', 'collected', 'items', 'PASSED', 'FAILED', 'ERROR', 'SKIPPED',
                      'warning', 'test_', '.py', '::', '[', '%]', 'cachedir', 'rootdir', 'plugins', 'results']
    print(f"  Contains pytest keywords: {any(kw in 'After content'.lower() for kw in pytest_keywords)}")
    print(f"  Starts with space: {'After content'.startswith((' ', '\t'))}")

if __name__ == "__main__":
    test_fix()
    test_warnings_fix()
    test_debug()
