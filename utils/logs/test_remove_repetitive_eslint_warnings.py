from utils.logs.remove_repetitive_eslint_warnings import (
    remove_repetitive_eslint_warnings,
)


def test_remove_repetitive_eslint_warnings():
    # This function filters ESLint output - keeps files only if they have errors (not just warnings)
    log = """/path/to/file1.js
  1:1  error  Unexpected token
  2:1  warning  'var' is deprecated

/path/to/file2.js
  1:1  warning  Missing semicolon
  2:1  warning  'var' is deprecated

✖ 4 problems (1 error, 3 warnings)"""

    # Only file1.js should remain because it has errors; file2.js has only warnings
    expected = """/path/to/file1.js
  1:1  error  Unexpected token

✖ 4 problems (1 error, 3 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_remove_repetitive_eslint_warnings_no_repetition():
    log = """src/file1.js:1:1: warning: 'var' is deprecated (no-var)
src/file2.js:1:1: warning: Missing semicolon (semi)
src/file3.js:1:1: warning: Unused variable (no-unused-vars)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_empty_error_log():
    # Test line 5-6: empty string input
    result = remove_repetitive_eslint_warnings("")
    assert result == ""


def test_none_error_log():
    # Test line 5-6: None input
    result = remove_repetitive_eslint_warnings(None)
    assert result is None


def test_file_with_only_warnings():
    # Test line 27 branch: file path with only warnings (no errors)
    log = """/path/to/file1.ts
  1:1  warning  Missing semicolon
  2:1  warning  'var' is deprecated

✖ 2 problems (0 errors, 2 warnings)"""

    # File should be excluded since it has no errors
    expected = """✖ 2 problems (0 errors, 2 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_trailing_newline_handling():
    # Test line 69-70: input without trailing newline
    log = """/path/to/file1.js
  1:1  error  Unexpected token"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected
    assert not result.endswith("\n")


def test_multiple_files_with_mixed_errors_and_warnings():
    # Test comprehensive scenario with multiple files
    log = """/path/to/file1.tsx
  1:1  error  Unexpected token
  2:1  warning  Missing semicolon

/path/to/file2.js
  1:1  warning  'var' is deprecated

/path/to/file3.ts
  3:5  error  Type error
  4:1  error  Another error

✖ 6 problems (3 errors, 3 warnings)"""

    expected = """/path/to/file1.tsx
  1:1  error  Unexpected token
/path/to/file3.ts
  3:5  error  Type error
  4:1  error  Another error

✖ 6 problems (3 errors, 3 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_error_command_failed_marker():
    # Test that "error Command failed" stops file processing
    log = """/path/to/file1.js
  1:1  error  Unexpected token
error Command failed with exit code 1."""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token
error Command failed with exit code 1."""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_file_path_with_colon():
    # Test that file paths with colons are not treated as ESLint file paths
    log = """src/file1.js:1:1: error: Unexpected token
src/file2.js:2:1: warning: Missing semicolon"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_non_js_ts_file():
    # Test that non-JS/TS files are not treated as ESLint file paths
    log = """/path/to/file.py
  1:1  error  Some error"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_input_with_trailing_newline():
    # Test that input with trailing newline preserves it
    log = """/path/to/file1.js
  1:1  error  Unexpected token
"""

    result = remove_repetitive_eslint_warnings(log)
    assert result.endswith("\n")
