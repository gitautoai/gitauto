#!/usr/bin/env python3

from utils.logs.remove_pytest_sections import remove_pytest_sections

def test_simple():
    log = """Initial content
============================= test session starts ==============================
platform linux -- Python 3.12.11, pytest-8.3.3, pluggy-1.5.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 2900 items

services/anthropic/test_evaluate_condition.py .......                    [  0%]
services/anthropic/test_exceptions.py ................                   [  0%]

=================================== FAILURES ===================================
failure content"""

    expected = """Initial content

=================================== FAILURES ===================================
failure content"""

    result = remove_pytest_sections(log)
    print("Expected:")
    print(repr(expected))
    print("\nActual:")
    print(repr(result))
    print(f"\nMatch: {result == expected}")

if __name__ == "__main__":
    test_simple()
