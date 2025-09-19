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

if __name__ == "__main__":
    test_fix()
    test_warnings_fix()
