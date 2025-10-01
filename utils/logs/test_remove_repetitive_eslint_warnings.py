from utils.logs.remove_repetitive_eslint_warnings import \
    remove_repetitive_eslint_warnings


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


def test_result_with_trailing_newline_input_without():
    # Test line 71-72: input doesn't end with newline but result does
    # This is a contrived scenario to cover the edge case
    log = """/path/to/file.js
  1:1  error  Some error

"""
    # Remove the trailing newline from input
    log = log.rstrip("\n")

    result = remove_repetitive_eslint_warnings(log)
    # Result should not have trailing newline to match input
    assert not result.endswith("\n")
    assert "/path/to/file.js" in result
    assert "1:1  error  Some error" in result


def test_result_with_trailing_newline_but_input_without():
    # Test line 71-72: input without trailing newline but result has one
    # This happens when we add blank lines during processing
    log = """/path/to/file1.js
  1:1  error  Unexpected token
✖ 1 problem (1 error, 0 warnings)"""

    # The function adds a blank line before ✖, so result_lines becomes:
    # ["/path/to/file1.js", "  1:1  error  Unexpected token", "", "✖ 1 problem..."]
    # After join, this creates a trailing newline scenario that needs to be stripped
    expected = """/path/to/file1.js
  1:1  error  Unexpected token

✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected
    assert not result.endswith("\n")



def test_result_with_trailing_newline_when_input_has_none():
    # Test line 71-72: input without trailing newline but result has one
    # This happens when the last line in result_lines is empty
    log = """/path/to/file1.js
  1:1  error  Unexpected token

✖ 1 problem (1 error, 0 warnings)"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token

✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected
    assert not result.endswith("\n")


def test_multiple_empty_lines():
    # Test with multiple empty lines in the input
    log = """/path/to/file1.js
  1:1  error  Unexpected token


✖ 1 problem (1 error, 0 warnings)"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token


✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_empty_lines_between_files():
    # Test with empty lines between file entries
    log = """/path/to/file1.js
  1:1  error  Unexpected token

/path/to/file2.js
  2:1  error  Another error

✖ 2 problems (2 errors, 0 warnings)"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token
/path/to/file2.js
  2:1  error  Another error

✖ 2 problems (2 errors, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_file_with_no_errors_or_warnings():
    # Test file path with no errors or warnings following it
    log = """/path/to/file1.js

✖ 0 problems (0 errors, 0 warnings)"""

    expected = """
✖ 0 problems (0 errors, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_summary_without_blank_line_before():
    # Test that blank line is added before summary when needed
    log = """/path/to/file1.js
  1:1  error  Unexpected token
✖ 1 problem (1 error, 0 warnings)"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token

✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_summary_with_file_path_before():
    # Test that blank line is NOT added when previous line is a file path
    log = """/path/to/file1.js
✖ 1 problem (1 error, 0 warnings)"""

    expected = """/path/to/file1.js
✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_summary_with_empty_line_before():
    # Test that blank line is NOT added when previous line is already empty
    log = """/path/to/file1.js
  1:1  error  Unexpected token

✖ 1 problem (1 error, 0 warnings)"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token

✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_jsx_file_extension():
    # Test that .tsx files are recognized
    log = """/path/to/component.tsx
  1:1  error  Type error

✖ 1 problem (1 error, 0 warnings)"""

    expected = """/path/to/component.tsx
  1:1  error  Type error

✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_file_path_not_starting_with_slash():
    # Test that relative paths (not starting with /) are not treated as file paths
    log = """path/to/file.js
  1:1  error  Some error"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_whitespace_in_error_lines():
    # Test that error lines with various whitespace are handled correctly
    log = """/path/to/file1.js
    10:5  error  Unexpected token
  2:1  error  Another error

✖ 2 problems (2 errors, 0 warnings)"""

    expected = """/path/to/file1.js
    10:5  error  Unexpected token
  2:1  error  Another error



def test_file_with_only_warnings():
    # Test that files with only warnings are filtered out
    log = """/path/to/file1.js
  1:1  warning  Missing semicolon
  2:1  warning  'var' is deprecated

✖ 2 problems (0 errors, 2 warnings)"""

    expected = """✖ 2 problems (0 errors, 2 warnings)"""

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
    # Test that file paths with colons are not treated as file paths
    log = """/path/to/file.js:10:5
  1:1  error  Some error"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_non_js_file_extension():
    # Test that non-JS/TS files are not treated as file paths
    log = """/path/to/file.py
  1:1  error  Some error"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_multiple_files_with_mixed_content():
    # Test multiple files with errors, warnings, and empty lines
    log = """/path/to/file1.js
  1:1  warning  Warning 1
  2:1  error  Error 1
  3:1  warning  Warning 2

/path/to/file2.ts
  4:1  error  Error 2
  5:1  error  Error 3

/path/to/file3.tsx
  6:1  warning  Warning 3

✖ 6 problems (3 errors, 3 warnings)"""

    expected = """/path/to/file1.js
  2:1  error  Error 1
/path/to/file2.ts
  4:1  error  Error 2
  5:1  error  Error 3

✖ 6 problems (3 errors, 3 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_trailing_newline_edge_case():
    # Test edge case: input without trailing newline, result processing
    log = """/path/to/file1.js
  1:1  error  Unexpected token"""

    result = remove_repetitive_eslint_warnings(log)
    # Result should not end with newline since input doesn't
    assert not result.endswith("\n")
    assert result == log


def test_double_trailing_newline():
    # Test input with double trailing newline
    log = """/path/to/file1.js
  1:1  error  Unexpected token

"""

