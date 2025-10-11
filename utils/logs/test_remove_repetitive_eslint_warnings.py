
from utils.logs.remove_repetitive_eslint_warnings import (
    remove_repetitive_eslint_warnings,
)

def test_edge_case_trailing_newline_strip():
    # Edge case: file with only warnings gets removed, leaving only summary
    # If summary line triggers blank line addition, result might end with newline
    log = "/path/file.js\n  1:1  warning  Warning\n✖ 1 problem"
    result = remove_repetitive_eslint_warnings(log)
    # Input doesn't end with newline, result shouldn't either
    assert not result.endswith("\n")


def test_edge_case_trailing_newline_with_footer():
    # Edge case: file with only warnings followed by non-file content with trailing newline
    # This tests the scenario where result might end with newline but input doesn't
    log = "/path/file.js\n  1:1  warning  Warning\nFooter line"
    result = remove_repetitive_eslint_warnings(log)
    # Input doesn't end with newline, result shouldn't either
    assert not result.endswith("\n")
from utils.logs.remove_repetitive_eslint_warnings import \
    remove_repetitive_eslint_warnings


def test_remove_repetitive_eslint_warnings():
    log = """/path/to/file1.js
  1:1  error  Unexpected token
  2:1  warning  'var' is deprecated

/path/to/file2.js
  1:1  warning  Missing semicolon
  2:1  warning  'var' is deprecated

✖ 4 problems (1 error, 3 warnings)"""

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
    result = remove_repetitive_eslint_warnings("")
    assert result == ""


def test_none_error_log():
    result = remove_repetitive_eslint_warnings(None)
    assert result is None


def test_file_with_only_warnings():
    log = """/path/to/file1.ts
  1:1  warning  Missing semicolon
  2:1  warning  'var' is deprecated

✖ 2 problems (0 errors, 2 warnings)"""

    expected = """✖ 2 problems (0 errors, 2 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_trailing_newline_handling():
    log = """/path/to/file1.js
  1:1  error  Unexpected token"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected
    assert not result.endswith("\n")


def test_multiple_files_with_mixed_errors_and_warnings():
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
    log = """/path/to/file1.js
  1:1  error  Unexpected token
error Command failed with exit code 1."""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token
error Command failed with exit code 1."""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_file_path_with_colon():
    log = """src/file1.js:1:1: error: Unexpected token
src/file2.js:2:1: warning: Missing semicolon"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_non_js_ts_file():
    log = """/path/to/file.py
  1:1  error  Some error"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_input_with_trailing_newline():
    log = """/path/to/file1.js
  1:1  error  Unexpected token
"""

    result = remove_repetitive_eslint_warnings(log)
    assert result.endswith("\n")


def test_trailing_newline_mismatch():
    # Test line 71-72: This tests the case where input doesn't end with newline
    # but result does (after join). This happens when result_lines ends with ""
    # We create a scenario with a non-file line followed by empty line
    # The key is to have the split produce an empty string at the end
    # while conceptually the input shouldn't end with newline

    # Case 1: Input with trailing newline after summary
    log_with_newline = "/path/file.js\n  1:1  error  Error\n✖ 1 problem\n"
    result1 = remove_repetitive_eslint_warnings(log_with_newline)
    assert result1.endswith("\n")

    # Case 2: Input without trailing newline
    log_without_newline = "/path/file.js\n  1:1  error  Error\n✖ 1 problem"
    result2 = remove_repetitive_eslint_warnings(log_without_newline)
    assert not result2.endswith("\n")

    # Case 3: Non-file content with trailing empty line
    # This creates a scenario where result_lines could end with ""
    log3 = "Header\nFooter\n"
    result3 = remove_repetitive_eslint_warnings(log3)
    assert result3.endswith("\n")

    # Case 4: Non-file content without trailing newline
    log4 = "Header\nFooter"
    result4 = remove_repetitive_eslint_warnings(log4)
    assert not result4.endswith("\n")


def test_empty_lines_in_output():
    # Test with empty lines between content
    log = "/path/file.js\n  1:1  error  Error\n\n✖ 1 problem"
    result = remove_repetitive_eslint_warnings(log)
    # Should preserve the structure
    assert "/path/file.js" in result
    assert "  1:1  error  Error" in result
    assert "✖ 1 problem" in result


def test_multiple_empty_lines():
    # Test with multiple consecutive empty lines
    log = "Line1\n\n\nLine2"
    result = remove_repetitive_eslint_warnings(log)
    # Should preserve all empty lines
    assert result == log


def test_only_summary_line():
    # Test with only a summary line
    log = "✖ 5 problems (2 errors, 3 warnings)"
    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_file_with_errors_and_trailing_content():
    # Test file processing with content after errors
    log = "/path/file.js\n  1:1  error  Error\n  2:1  error  Another error\n✖ 2 problems"
    result = remove_repetitive_eslint_warnings(log)
    assert "/path/file.js" in result
    assert "  1:1  error  Error" in result
    assert "  2:1  error  Another error" in result
    assert "✖ 2 problems" in result


def test_result_ends_with_newline_but_input_does_not():
    # Test line 71-72: This is a very specific edge case
    # We need result to end with \n but input to not end with \n
    # This can happen when processing adds empty lines

    # Create a case with a summary line that gets a blank line before it
    # and then an empty line after it
    # Input ends with "\n\n" which creates two empty strings in split
    # But we'll test the trimming logic
    log = "Some header\n✖ 1 problem\n"
    result = remove_repetitive_eslint_warnings(log)
    expected = "Some header\n\n✖ 1 problem\n"
    # Input ends with \n, result should too
    assert result.endswith("\n")
    # The function adds a blank line before summary lines
    assert result == expected
