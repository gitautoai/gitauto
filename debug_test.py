from utils.logs.remove_pytest_sections import remove_pytest_sections

log = """Run python -m pytest

=== test session starts ===
platform linux -- Python 3.12.11, pytest-8.3.3, pluggy-1.5.0
rootdir: /home/runner/work/gitauto/gitauto
plugins: asyncio-0.24.0, cov-6.0.0
asyncio: mode=Mode.STRICT, default_fixture_loop_scope=None
collected 3624 items

=================================== FAILURES ===================================
_______________________________ test_fail ________________________________

    def test_fail():
>       assert False
E       AssertionError

test_example.py:2: AssertionError

=========================== short test summary info ============================
FAILED test_example.py::test_fail - AssertionError"""

expected = """Run python -m pytest

=================================== FAILURES ===================================
_______________________________ test_fail ________________________________

    def test_fail():
>       assert False
E       AssertionError

test_example.py:2: AssertionError

=========================== short test summary info ============================
FAILED test_example.py::test_fail - AssertionError"""

result = remove_pytest_sections(log)
print("RESULT:")
print(repr(result))
print("\nEXPECTED:")
print(repr(expected))
print("\nMATCH:", result == expected)
