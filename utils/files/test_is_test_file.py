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
        ("__tests__/Component.tsx", True),  # __tests__ at root
        ("services/claude/test_client.py", True),
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
        # Config files are NOT test files (use is_config_file for these)
        ("jest.config.js", False),
        ("jest.config.ts", False),
        ("vitest.config.ts", False),
        ("vitest.config.js", False),
        ("karma.conf.js", False),
        ("webpack.config.js", False),
        ("webpack.config.ts", False),
        ("rollup.config.js", False),
        ("rollup.config.mjs", False),
        ("vite.config.js", False),
        ("vite.config.ts", False),
        ("babel.config.js", False),
        ("babel.config.json", False),
        ("next.config.js", False),
        ("next.config.mjs", False),
        ("nuxt.config.js", False),
        ("nuxt.config.ts", False),
        ("tailwind.config.js", False),
        ("postcss.config.js", False),
        ("eslint.config.js", False),
        ("eslint.config.mjs", False),
        (".eslintrc", False),
        (".eslintrc.js", False),
        (".eslintrc.json", False),
        (".prettierrc", False),
        (".prettierrc.js", False),
        (".prettierrc.json", False),
        ("prettier.config.js", False),
        ("tsconfig.json", False),
        ("tsconfig.build.json", False),
        ("tsconfig.app.json", False),
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
        # Test directory patterns
        ("test/services/stripe/webhook.test.ts", True),
        ("test/setup.ts", True),
        ("test/teardown.ts", True),
        ("test/fixture/mock_answers.ts", True),
        ("test/fixture/mock_config.json", True),
        ("test/mock_data/mock_policies.ts", True),
        ("test/utils/helpers.ts", True),
        ("test/mongodb/instance.ts", True),
        # src/test/ patterns
        ("src/test/setup.ts", True),
        ("src/test/fixture/mock_data.ts", True),
        ("src/test/utils/createTestContext.ts", True),
        # Various .test. patterns
        ("src/context/getSecrets.test.ts", True),
        ("src/models/graphql/__tests__/error.test.ts", True),
        ("src/resolvers/handler.test.ts", True),
        # Snapshot patterns
        ("src/services/__snapshots__/getUserPaymentOption.test.ts.snap", True),
        ("test/utils/__snapshots__/calTotalPayable.test.ts.snap", True),
        # Root-level test directories (the (^|/) pattern bug)
        ("testing/utils/context/getTestSecrets.ts", True),
        ("testing/setup.ts", True),
        ("testing/teardown.ts", True),
        ("src/testing/helpers.ts", True),
        ("e2e/login.spec.ts", True),
        ("e2e/integration/checkout.ts", True),
        ("playwright/tests/login.spec.ts", True),
        ("spec/models/user_spec.rb", True),
        ("__mocks__/api.js", True),
        ("__snapshots__/Button.test.tsx.snap", True),
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
    # Intentionally passing invalid types to test runtime error handling
    assert is_test_file(None) is False  # pyright: ignore[reportArgumentType]
    assert is_test_file(123) is False  # pyright: ignore[reportArgumentType]
    assert is_test_file([]) is False  # pyright: ignore[reportArgumentType]


def test_is_test_file_case_insensitivity():
    # The function should use case-insensitive matching
    # Even if the file name is uppercase, it should detect test patterns
    assert is_test_file("TEST_file.py") is True
    assert is_test_file("UTILS.SPEC.JS") is True
