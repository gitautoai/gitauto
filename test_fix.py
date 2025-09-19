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

if __name__ == "__main__":
    test_fix()
