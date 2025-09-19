import sys
sys.path.append('/home/runner/work/gitauto/gitauto')

from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test the failing case
log = """Initial content
=========================== warnings summary ============================
/path/to/file.py:10: DeprecationWarning: deprecated function
  deprecated_function()

/path/to/file.py:20: UserWarning: user warning
  warnings.warn("user warning")

=================================== FAILURES ===================================
Test failure content here"""

result = remove_pytest_sections(log)
print("RESULT:")
print(repr(result))

expected = """Initial content

=================================== FAILURES ===================================
Test failure content here"""

print("\nEXPECTED:")
print(repr(expected))

print(f"\nMATCH: {result == expected}")
