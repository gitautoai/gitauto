from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test with a simple case
log = """Run python -m pytest
============================= test session starts ==============================
platform linux -- Python 3.12.11, pytest-8.3.3, pluggy-1.5.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 2900 items

services/test.py .......                    [  0%]

=================================== FAILURES ===================================
Test failure content"""

expected = """Run python -m pytest

=================================== FAILURES ===================================
Test failure content"""

result = remove_pytest_sections(log)
print("Result:")
print(repr(result))
print("\nExpected:")
print(repr(expected))
print("\nMatch:", result == expected)
