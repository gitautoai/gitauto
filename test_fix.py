from utils.logs.remove_pytest_sections import remove_pytest_sections
from config import UTF8

# Test with a small sample
test_input = """Run python -m pytest
============================= test session starts ==============================
platform linux -- Python 3.12.11, pytest-8.3.3, pluggy-1.5.0
rootdir: /home/runner/work/gitauto/gitauto
collected 2900 items

services/git/test_git_manager.py ............s..............             [  6%]
services/github/artifacts/test_download_artifact.py ..................   [  6%]
..............                                                           [  8%]
....                                                                     [  9%]

=================================== FAILURES ===================================
Test failure content"""

expected = """Run python -m pytest

=================================== FAILURES ===================================
Test failure content"""

result = remove_pytest_sections(test_input)
print("Input:")
print(repr(test_input))
print("\nResult:")
print(repr(result))
print("\nExpected:")
print(repr(expected))
print("\nMatch:", result == expected)
