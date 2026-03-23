import re

from utils.error.handle_exceptions import handle_exceptions
from utils.logs.remove_ansi_escape_codes import remove_ansi_escape_codes

# Jest/Vitest: "FAIL src/a.test.ts (8.086 s)" or "FAIL integration testing/a.test.ts"
JEST_FAIL_PATTERN = re.compile(
    r"^\s*FAIL\s+(.+?)(?:\s+\(\d+[\d.]*\s*s\))?$", re.MULTILINE
)

# Pytest: "FAILED tests/test_logic.py::test_name - error message"
PYTEST_FAIL_PATTERN = re.compile(r"^FAILED\s+(\S+\.py)::", re.MULTILINE)

# PHPUnit: file path on its own line after "There was N failure:" block, e.g. "/home/app/tests/fooTest.php:84"
PHPUNIT_FAIL_PATTERN = re.compile(r"^(\S+\.php):\d+$", re.MULTILINE)

# File extensions for test files across frameworks
TEST_FILE_PATTERN = re.compile(r"\.(test|spec)\.(ts|tsx|js|jsx|mjs|cjs)$")


@handle_exceptions(default_return_value=set(), raise_on_error=False)
def extract_failing_test_files(error_log: str):
    cleaned = remove_ansi_escape_codes(error_log)
    files: set[str] = set()

    # Jest/Vitest: extract test file paths from "FAIL <path>" lines
    for match in JEST_FAIL_PATTERN.finditer(cleaned):
        raw = match.group(1).strip()
        # Raw match may contain a workspace prefix (e.g. "integration", "core") before the actual file path
        for part in raw.split():
            if TEST_FILE_PATTERN.search(part):
                files.add(part)

    # Pytest: extract test file paths from "FAILED <path>::<test_name>" lines
    for match in PYTEST_FAIL_PATTERN.finditer(cleaned):
        files.add(match.group(1))

    # PHPUnit: extract file paths ending with .php:<line_number>
    for match in PHPUNIT_FAIL_PATTERN.finditer(cleaned):
        path = match.group(1)
        # Only include paths that look like test files (contain "test" or "Test")
        if "test" in path.lower():
            files.add(path)

    return files
