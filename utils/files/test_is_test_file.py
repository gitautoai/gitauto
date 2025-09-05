from utils.files.is_test_file import is_test_file


def test_direct_test_file_patterns():
    # Test .test. pattern
    assert is_test_file("Button.test.tsx") is True
    assert is_test_file("utils.test.js") is True
    assert is_test_file("api.test.ts") is True
    
    # Test .spec. pattern
    assert is_test_file("Button.spec.tsx") is True
    assert is_test_file("api.spec.js") is True
    assert is_test_file("user.spec.ts") is True
    
    # Test test. pattern
    assert is_test_file("ButtonTest.java") is True
    assert is_test_file("UserTest.cs") is True
    
    # Test tests. pattern
    assert is_test_file("ButtonTests.java") is True
    assert is_test_file("UserTests.cs") is True
    
    # Test _test. pattern
    assert is_test_file("button_test.py") is True
    assert is_test_file("user_test.go") is True
    
    # Test _spec. pattern
    assert is_test_file("button_spec.rb") is True
    assert is_test_file("user_spec.rb") is True


def test_test_file_prefixes():
    # Test ^test_ pattern
    assert is_test_file("test_button.py") is True
    assert is_test_file("test_utils.py") is True
    
    # Test /test_ pattern
    assert is_test_file("services/anthropic/test_client.py") is True
    assert is_test_file("src/components/test_button.js") is True
    
    # Test ^spec_ pattern
    assert is_test_file("spec_button.rb") is True
    assert is_test_file("spec_helper.rb") is True
    
    # Test /spec_ pattern
    assert is_test_file("services/anthropic/spec_client.py") is True
    assert is_test_file("src/models/spec_user.rb") is True


def test_test_directories():
    # Test __tests__ directory
    assert is_test_file("src/__tests__/Button.tsx") is True
    assert is_test_file("components/__tests__/Modal.js") is True
    
    # Test tests directory (plural)
    assert is_test_file("src/tests/Button.tsx") is True
    assert is_test_file("tests/constants.py") is True
    
    # Test test directory (singular)
    assert is_test_file("src/test/Button.java") is True
    assert is_test_file("test/utils.py") is True
    
    # Test e2e directory
    assert is_test_file("e2e/login.spec.ts") is True
    assert is_test_file("tests/e2e/checkout.js") is True
    
    # Test cypress directory
    assert is_test_file("cypress/integration/login.js") is True
    assert is_test_file("src/cypress/e2e/user.spec.js") is True
    
    # Test playwright directory
    assert is_test_file("playwright/tests/login.spec.ts") is True
    assert is_test_file("tests/playwright/checkout.spec.js") is True
    
    # Test spec directory
    assert is_test_file("spec/models/user_spec.rb") is True
    assert is_test_file("src/spec/controllers/api_spec.rb") is True
    
    # Test testing directory
    assert is_test_file("testing/utils.py") is True
    assert is_test_file("src/testing/helpers.js") is True


def test_mock_files():
    # Test __mocks__ directory
    assert is_test_file("src/__mocks__/api.js") is True
    assert is_test_file("components/__mocks__/Button.tsx") is True
    
    # Test .mock. pattern
    assert is_test_file("api.mock.ts") is True
    assert is_test_file("database.mock.js") is True
    
    # Test mock. pattern
    assert is_test_file("ApiMock.java") is True
    assert is_test_file("DatabaseMock.cs") is True
    
    # Test mocks. pattern
    assert is_test_file("ApiMocks.java") is True
    assert is_test_file("DatabaseMocks.cs") is True


def test_common_test_file_names():
    # Test ^test. pattern
    assert is_test_file("test.js") is True
    assert is_test_file("test.py") is True
    
    # Test ^spec. pattern
    assert is_test_file("spec.rb") is True
    assert is_test_file("spec.js") is True


def test_ci_cd_files():
    # Test .github directory
    assert is_test_file(".github/scripts/deploy.sh") is True
    assert is_test_file(".github/workflows/ci.yml") is True
    assert is_test_file(".github/actions/setup/action.yml") is True


def test_case_insensitive_matching():
    # Test uppercase variations
    assert is_test_file("BUTTON.TEST.TSX") is True
    assert is_test_file("API.SPEC.JS") is True
    assert is_test_file("TEST_UTILS.PY") is True
    assert is_test_file("SRC/TESTS/BUTTON.JS") is True
    assert is_test_file("CYPRESS/INTEGRATION/LOGIN.JS") is True
    
    # Test mixed case variations
    assert is_test_file("Button.Test.tsx") is True
    assert is_test_file("Api.Spec.js") is True
    assert is_test_file("Test_Utils.py") is True
    assert is_test_file("Src/Tests/Button.js") is True


def test_non_test_files():
    # Regular source files
    assert is_test_file("Button.tsx") is False
    assert is_test_file("api.js") is False
    assert is_test_file("utils.py") is False
    assert is_test_file("User.java") is False
    assert is_test_file("Database.cs") is False
    
    # Files with test-like names but not matching patterns
    assert is_test_file("testing_utils.py") is False  # Should be test_utils.py or testing/utils.py
    assert is_test_file("spec_helper_utils.py") is False  # Should be spec_helper.py
    assert is_test_file("button_testing.js") is False  # Should be button_test.js
    
    # Configuration files
    assert is_test_file("package.json") is False
    assert is_test_file("tsconfig.json") is False
    assert is_test_file("webpack.config.js") is False
    
    # Documentation files
    assert is_test_file("README.md") is False
    assert is_test_file("CHANGELOG.md") is False
    
    # Regular directories without test patterns
    assert is_test_file("src/components/Button.tsx") is False
    assert is_test_file("lib/utils/helper.js") is False


def test_edge_cases():
    # Empty string
    assert is_test_file("") is False
    
    # None input (should be handled by decorator)
    assert is_test_file(None) is False
    
    # Non-string inputs (should be handled by decorator)
    assert is_test_file(123) is False
    assert is_test_file([]) is False
    assert is_test_file({}) is False
    assert is_test_file(True) is False
    
    # Whitespace only
    assert is_test_file("   ") is False
    assert is_test_file("\t\n") is False


def test_complex_paths():
    # Nested test directories
    assert is_test_file("src/components/__tests__/ui/Button.test.tsx") is True
    assert is_test_file("backend/services/auth/tests/unit/user.spec.py") is True
    assert is_test_file("frontend/src/pages/__tests__/integration/login.test.js") is True
    
    # Multiple test patterns in path
    assert is_test_file("tests/unit/test_api.spec.py") is True
    assert is_test_file("spec/integration/user_spec.test.rb") is True
    
    # Long paths with test patterns
    assert is_test_file("very/long/path/to/test/directory/with/many/levels/test_file.py") is True
    assert is_test_file("project/src/main/java/com/example/service/UserServiceTest.java") is True


def test_boundary_cases():
    # Files that start or end with test patterns but aren't test files
    assert is_test_file("testfile.py") is False  # Should be test_file.py or test.py
    assert is_test_file("filetest.py") is False  # Should be file_test.py
    
    # Files with test patterns in the middle but not matching exact patterns
    assert is_test_file("my_test_file.py") is False  # Should be test_my_file.py or my_test.py
    assert is_test_file("user_spec_helper.py") is False  # Should be user_spec.py
    
    # Valid edge cases that should match
    assert is_test_file("a.test.b") is True  # Minimal .test. pattern
    assert is_test_file("x/test_y") is True  # Minimal /test_ pattern
    assert is_test_file("test/z") is True  # Minimal test/ pattern
