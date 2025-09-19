#!/usr/bin/env python3
import sys
sys.path.append('.')
from utils.logs.remove_pytest_sections import remove_pytest_sections

def test_failing_case():
    """Test the case that was failing"""
    log = """Before content
=========================== test session starts ============================
platform linux
collected items
test results
After content"""

    expected = """Before content
After content"""

    result = remove_pytest_sections(log)
    print("Test: test_remove_pytest_sections_only_test_session_starts")
    print("Expected:", repr(expected))
    print("Got:     ", repr(result))
    print("PASS" if result == expected else "FAIL")
    return result == expected

if __name__ == "__main__":
    success = test_failing_case()
    if success:
        print("\n✅ Fix verified!")
    else:
        print("\n❌ Fix failed!")
    sys.exit(0 if success else 1)
