import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TestNamingPattern:
    name: str
    detect: re.Pattern[str]  # Matches full file path to identify test files
    stem_strip: re.Pattern[str]  # Strips test affix from Path.stem to recover impl stem
    description: str  # Template for detect_test_naming_convention


SKIP_DIRS = frozenset(
    {
        ".git",
        "__pycache__",
        "node_modules",
        "venv",
        ".venv",
        "dist",
        "build",
        ".next",
        ".nuxt",
        "vendor",
        "coverage",
    }
)

# Order matters: more specific first.
TEST_NAMING_PATTERNS: list[TestNamingPattern] = [
    # Jest/Vitest: Button.spec.tsx, Quote.spec.ts
    TestNamingPattern(
        name="dot_spec",
        detect=re.compile(r"\.spec\."),
        stem_strip=re.compile(r"(?i:\.spec$)"),
        description="Use .spec. naming (e.g., {example})",
    ),
    # Jest/Vitest: Button.test.tsx, index.test.ts
    TestNamingPattern(
        name="dot_test",
        detect=re.compile(r"\.test\."),
        stem_strip=re.compile(r"(?i:\.test$)"),
        description="Use .test. naming (e.g., {example})",
    ),
    # pytest: test_client.py, test_utils.py
    TestNamingPattern(
        name="test_prefix",
        detect=re.compile(r"(^|/)test_"),
        stem_strip=re.compile(r"(?i:^test_)"),
        description="Use test_ prefix naming (e.g., {example})",
    ),
    # Go: handler_test.go
    TestNamingPattern(
        name="underscore_test",
        detect=re.compile(r"_test\."),
        stem_strip=re.compile(r"(?i:_test$)"),
        description="Use _test suffix naming (e.g., {example})",
    ),
    # RSpec: user_spec.rb
    TestNamingPattern(
        name="underscore_spec",
        detect=re.compile(r"_spec\."),
        stem_strip=re.compile(r"(?i:_spec$)"),
        description="Use _spec suffix naming (e.g., {example})",
    ),
    # PHPUnit/JUnit: SafetypatServiceTest.php, ServiceTest.java
    TestNamingPattern(
        name="Test_suffix",
        detect=re.compile(r"(?<!vi)tests?\."),
        stem_strip=re.compile(r"(?<=[a-z])Test$"),
        description="Use Test suffix naming (e.g., {example})",
    ),
    # Ruby: spec_helper.rb
    TestNamingPattern(
        name="spec_prefix",
        detect=re.compile(r"(^|/)spec_"),
        stem_strip=re.compile(r"(?i:^spec_)"),
        description="Use spec_ prefix naming (e.g., {example})",
    ),
]

# Test directory patterns (path-based, not filename-based)
TEST_DIR_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(^|/)__tests__/"),
    re.compile(r"(^|/)tests?/"),
    re.compile(r"(^|/)e2e/"),
    re.compile(r"(^|/)cypress/"),
    re.compile(r"(^|/)playwright/"),
    re.compile(r"(^|/)spec/"),
    re.compile(r"(^|/)testing/"),
]

# Test support file patterns (mocks, fixtures, snapshots, helpers, storybook, CI)
TEST_SUPPORT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(^|/)__mocks__/"),
    re.compile(r"\.mock\."),
    re.compile(r"mocks?\."),
    re.compile(r"(^|/)__snapshots__/"),
    re.compile(r"\.snap$"),
    re.compile(r"(^|/)__fixtures__/"),
    re.compile(r"(^|/)fixtures/"),
    re.compile(r"\.fixture\."),
    re.compile(r"(^|/)test[-_]utils?/"),
    re.compile(r"(^|/)test[-_]helpers?/"),
    re.compile(r"(^|/)setuptests\."),
    re.compile(r"(^|/)testsetup\."),
    re.compile(r"(^|/)test[-_]setup\."),
    re.compile(r"\.stories\."),
    re.compile(r"(^|/)stories/"),
    re.compile(r"^test\."),
    re.compile(r"^spec\."),
    re.compile(r"^\.github/"),
]

# All test-related directory names (child subdirs, mirror prefixes, support dirs)
TEST_DIR_NAMES = {
    "__tests__",  # Jest/Vitest convention
    "tests",  # Python, PHP, general
    "test",  # Java/Maven, Go
    "spec",  # RSpec (Ruby), Jasmine
    "specs",  # Jasmine/Mocha plural convention
    "e2e",  # End-to-end tests
    "unit",  # PHPUnit/Laravel Unit tests
    "feature",  # PHPUnit/Laravel Feature tests
    "integration",  # Integration test category
    "cypress",  # Cypress E2E
    "playwright",  # Playwright E2E
    "testing",  # Python, general
    "__mocks__",  # Jest manual mocks
    "__snapshots__",  # Jest/Vitest snapshots
    "__fixtures__",  # Test fixtures
    "fixtures",  # Test fixtures (Django, Rails)
    "test-utils",  # Test utilities (kebab-case)
    "test_utils",  # Test utilities (snake_case)
    "test-helpers",  # Test helpers (kebab-case)
    "test_helper",  # Test helpers (snake_case, Rails)
    "stories",  # Storybook visual tests
}

# Qualifiers like .integration, .unit, .e2e that appear between impl stem and .test/.spec
TEST_QUALIFIER_STRIP = re.compile(
    r"(?i)\.(integration|unit|e2e|functional|acceptance)$"
)

# Top-level directories that indicate a "separate test directory" convention
TOP_LEVEL_TEST_DIRS = frozenset({"test", "tests", "spec", "specs", "t"})

CRACO_CONFIG_FILES = [
    "craco.config.js",
    "craco.config.ts",
]

JEST_CONFIG_FILES = [
    "jest.config.js",
    "jest.config.ts",
    "jest.config.mjs",
    "jest.config.cjs",
]

VITEST_CONFIG_FILES = [
    "vitest.config.ts",
    "vitest.config.js",
    "vitest.config.mts",
    "vitest.config.mjs",
]


JS_TS_FILE_EXTENSIONS = (".js", ".jsx", ".ts", ".tsx")

PHP_TEST_FILE_EXTENSIONS = ("Test.php",)

# Python test files use prefix (test_foo.py), not suffix
PYTHON_TEST_FILE_PREFIX = "test_"

TS_TEST_FILE_EXTENSIONS = (
    ".test.ts",
    ".test.tsx",
    ".spec.ts",
    ".spec.tsx",
)

JS_TEST_FILE_EXTENSIONS = (
    ".test.js",
    ".test.jsx",
    ".spec.js",
    ".spec.jsx",
) + TS_TEST_FILE_EXTENSIONS
