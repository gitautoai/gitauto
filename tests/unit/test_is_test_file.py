import pytest

from utils.files.is_test_file import is_test_file


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("Button.test.tsx", True),
        ("utils.spec.js", True),
        ("test_file.py", True),
        ("tests/Component.js", True),
        ("src/__tests__/Component.tsx", True),
        ("services/anthropic/test_client.py", True),
        ("spec_helper.rb", True),
        ("cypress/integration/login.js", True),
        ("e2e/login.spec.ts", True),
        ("ApiMock.java", True),
        ("ApiMocks.java", True),
        (".github/workflows/ci.yml", True),
        ("README.md", False),
        ("main.py", False),
        ("utils/file.py", False),
        ("Button.jsx", False),
        ("folder/button", False),
    ],
)
def test_is_test_file_with_various_filenames(filename, expected):
    assert is_test_file(filename) == expected


def test_is_test_file_non_string_input():
    # Non-string inputs should safely return False
    assert is_test_file(None) is False
    assert is_test_file(123) is False
    assert is_test_file([]) is False


def test_is_test_file_case_insensitivity():
    # The function should use case-insensitive matching
    # Even if the file name is uppercase, it should detect test patterns
    assert is_test_file("TEST_file.py") is True
    assert is_test_file("UTILS.SPEC.JS") is True
