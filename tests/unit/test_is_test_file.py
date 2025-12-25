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
        # Snapshot files
        ("__snapshots__/Button.test.tsx.snap", True),
        ("component.snap", True),
        ("src/__snapshots__/Header.test.js.snap", True),
        ("component.spec.snap", True),
        ("component.test.snap", True),
        # Fixtures
        ("__fixtures__/user.json", True),
        ("src/__fixtures__/data.json", True),
        ("fixtures/sample_data.json", True),
        ("tests/fixtures/user.json", True),
        ("user.fixture.ts", True),
        ("data.fixture.js", True),
        # Test config files
        ("jest.config.js", True),
        ("jest.config.ts", True),
        ("vitest.config.ts", True),
        ("vitest.config.js", True),
        ("karma.conf.js", True),
        # Test helpers
        ("setupTests.js", True),
        ("setupTests.ts", True),
        ("testSetup.ts", True),
        ("src/testSetup.ts", True),
        ("test-setup.js", True),
        ("test_setup.py", True),
        ("test-utils/helpers.js", True),
        ("src/test-utils/api.ts", True),
        ("test_helpers/utils.py", True),
        ("test_utils/database.py", True),
        # Storybook
        ("Button.stories.tsx", True),
        ("Header.stories.js", True),
        ("stories/Header.tsx", True),
        ("src/stories/Button.tsx", True),
        # Should NOT be test files
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
