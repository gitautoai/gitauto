import pytest
from unittest.mock import patch, MagicMock

from utils.files.is_test_file import is_test_file


def test_is_test_file_with_non_string_input():
    """Test that is_test_file returns False for non-string inputs."""
    assert is_test_file(None) is False
    assert is_test_file(123) is False
    assert is_test_file([]) is False
    assert is_test_file({}) is False


def test_is_test_file_with_empty_string():
    """Test that is_test_file returns False for empty string."""
    assert is_test_file("") is False


@pytest.mark.parametrize("filename", [
    # Direct test file patterns
    "Button.test.tsx",
    "utils.test.js",
    "Button.spec.tsx",
    "api.spec.js",
    "ButtonTest.java",
    "UserTest.cs",
    "ButtonTests.java",
    "UserTests.cs",
    "button_test.py",
    "user_test.go",
    "button_spec.rb",
    "user_spec.rb",
    "test_button.py",
    "test_utils.py",
    "services/anthropic/test_client.py",
    "spec_button.rb",
    "spec_helper.rb",
    "services/anthropic/spec_client.py",
    
    # Test directories
    "src/__tests__/Button.tsx",
    "src/tests/Button.tsx",
    "src/test/Button.java",
    "tests/constants.py",
    "test/utils.py",
    "e2e/login.spec.ts",
    "cypress/integration/login.js",
    "playwright/tests/login.spec.ts",
    "spec/models/user_spec.rb",
    "testing/utils.py",
    
    # Mock files
    "src/__mocks__/api.js",
    "api.mock.ts",
    "database.mock.js",
    "ApiMock.java",
    "DatabaseMock.cs",
    "ApiMocks.java",
    "DatabaseMocks.cs",
    
    # Common test file names
    "test.js",
    "test.py",
    "spec.rb",
    "spec.js",
    
    # CI/CD and infrastructure
    ".github/workflows/pytest.yml",
    ".github/scripts/test-script.js",
])
def test_is_test_file_with_test_files(filename):
    """Test that is_test_file returns True for various test file patterns."""
    assert is_test_file(filename) is True


@pytest.mark.parametrize("filename", [
    # Regular source files
    "Button.tsx",
    "utils.js",
    "api.py",
    "User.java",
    "index.html",
    "styles.css",
    "README.md",
    "package.json",
    "requirements.txt",
    "Dockerfile",
    "main.py",
    "app.js",
    "server.py",
    "client.go",
    "database.sql",
    "config.yml",
    "utils/files/is_code_file.py",
    "src/components/Button.tsx",
    "lib/helpers/format.js",
])
def test_is_test_file_with_non_test_files(filename):
    """Test that is_test_file returns False for non-test files."""
    assert is_test_file(filename) is False


def test_is_test_file_case_insensitivity():
    """Test that is_test_file is case-insensitive."""
    assert is_test_file("TEST_file.py") is True
    assert is_test_file("Test.js") is True
    assert is_test_file("button.TEST.tsx") is True
    assert is_test_file("button.SPEC.js") is True
    assert is_test_file("TESTS/constants.py") is True
    assert is_test_file("src/TEST/utils.py") is True
    assert is_test_file(".GITHUB/workflows/deploy.yml") is True


def test_is_test_file_with_mixed_case_patterns():
    """Test that is_test_file works with mixed case patterns."""
    assert is_test_file("Test_Button.py") is True
    assert is_test_file("button_Test.py") is True
    assert is_test_file("Button.Spec.tsx") is True
    assert is_test_file("src/Tests/component.js") is True


def test_is_test_file_with_exception_handling():
    """Test that handle_exceptions decorator works correctly."""
    with patch("re.search", side_effect=Exception("Test exception")):
        assert is_test_file("test_file.py") is False


def test_is_test_file_with_regex_error():
    """Test that is_test_file handles regex errors gracefully."""
    with patch("re.search", side_effect=ValueError("Invalid regex pattern")):
        assert is_test_file("test_file.py") is False


def test_is_test_file_with_attribute_error():
    """Test that is_test_file handles attribute errors gracefully."""
    mock_filename = MagicMock()
    mock_filename.lower.side_effect = AttributeError("No lower method")
    assert is_test_file(mock_filename) is False




def test_is_test_file_with_unicode_characters():
    """Test that is_test_file handles unicode characters correctly."""
    assert is_test_file("tést_file.py") is True
    assert is_test_file("file_tést.py") is True
    assert is_test_file("src/tést/utils.py") is True


def test_is_test_file_with_special_characters():
    """Test that is_test_file handles special characters correctly."""
    assert is_test_file("test-file.py") is True
    assert is_test_file("file-test.py") is True
    assert is_test_file("src/test-utils/component.js") is True


def test_is_test_file_with_long_paths():
    """Test that is_test_file works with long file paths."""
    long_path = "very/long/path/with/many/directories/that/could/potentially/cause/issues/with/regex/test_file.py"
    assert is_test_file(long_path) is True
