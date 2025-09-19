from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test the failing case
log1 = """Before content
=========================== test session starts ============================
platform linux
collected items
test results
After content"""

expected1 = """Before content
After content"""

result1 = remove_pytest_sections(log1)
print("Test 1 (session starts):")
print(f"Expected: {repr(expected1)}")
print(f"Got: {repr(result1)}")
print(f"Match: {result1 == expected1}")
print()

# Test a case that should have blank lines
log2 = """Content before
=========================== test session starts ============================
session content to remove
=================================== FAILURES ===================================
failure content"""

expected2 = """Content before

=================================== FAILURES ===================================
failure content"""

result2 = remove_pytest_sections(log2)
print("Test 2 (with FAILURES):")
print(f"Expected: {repr(expected2)}")
print(f"Got: {repr(result2)}")
print(f"Match: {result2 == expected2}")
