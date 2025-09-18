from utils.logs.remove_repetitive_eslint_warnings import \
"""Unit tests for remove_repetitive_eslint_warnings module."""


    remove_repetitive_eslint_warnings


def test_empty_input():
    """Test with empty string input."""
    assert remove_repetitive_eslint_warnings("") == ""


def test_none_input():
    """Test with None input."""
    assert remove_repetitive_eslint_warnings(None) is None


def test_file_with_only_errors():
    """Test file that has only errors - should be kept."""
    log = """/path/to/file1.js
  1:1  error  Unexpected token
  2:5  error  Missing semicolon

✖ 2 problems (2 errors, 0 warnings)"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token
  2:5  error  Missing semicolon

✖ 2 problems (2 errors, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_file_with_only_warnings():
    """Test file that has only warnings - should be removed."""
    log = """/path/to/file1.js
  1:1  warning  'var' is deprecated
  2:5  warning  Missing semicolon

✖ 2 problems (0 errors, 2 warnings)"""

    expected = """
✖ 2 problems (0 errors, 2 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_file_with_mixed_errors_and_warnings():
    """Test file with both errors and warnings - should keep only errors."""
    log = """/path/to/file1.js
  1:1  error  Unexpected token
  2:1  warning  'var' is deprecated
  3:5  error  Missing semicolon
  4:1  warning  Unused variable

✖ 4 problems (2 errors, 2 warnings)"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token
  3:5  error  Missing semicolon

✖ 4 problems (2 errors, 2 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_multiple_files_mixed_scenarios():
    """Test multiple files with different error/warning combinations."""
    log = """/path/to/file1.js
  1:1  error  Unexpected token
  2:1  warning  'var' is deprecated

/path/to/file2.js
  1:1  warning  Missing semicolon
  2:1  warning  'var' is deprecated

/path/to/file3.js
  1:1  error  Syntax error
  2:1  error  Type error

✖ 6 problems (3 errors, 3 warnings)"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token
/path/to/file3.js
  1:1  error  Syntax error
  2:1  error  Type error

✖ 6 problems (3 errors, 3 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_different_file_extensions():
    """Test with different supported file extensions (.ts, .js, .tsx)."""
    log = """/path/to/file1.ts
  1:1  error  Type error

/path/to/file2.js
  1:1  warning  Warning only

/path/to/file3.tsx
  1:1  error  JSX error

✖ 3 problems (2 errors, 1 warning)"""

    expected = """/path/to/file1.ts
  1:1  error  Type error
/path/to/file3.tsx
  1:1  error  JSX error

✖ 3 problems (2 errors, 1 warning)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_relative_paths_not_processed():
    """Test that relative paths (not starting with /) are not processed as file paths."""
    log = """src/file1.js:1:1: warning: 'var' is deprecated (no-var)
src/file2.js:1:1: warning: Missing semicolon (semi)
src/file3.js:1:1: warning: Unused variable (no-unused-vars)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_files_with_colons_not_processed():
    """Test that file paths containing colons are not processed as ESLint file paths."""
    log = """/path/to/file1.js:1:1
  1:1  error  Some error

✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_error_command_failed_stops_processing():
    """Test that 'error Command failed' line stops file processing."""
    log = """/path/to/file1.js
  1:1  error  Unexpected token
error Command failed with exit code 1.

/path/to/file2.js
  1:1  error  Another error"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token
error Command failed with exit code 1.

/path/to/file2.js
  1:1  error  Another error"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_blank_line_insertion_before_summary():
    """Test that blank line is added before summary when needed."""
    log = """/path/to/file1.js
  1:1  error  Unexpected token
✖ 1 problem (1 error, 0 warnings)"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token

✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_no_blank_line_when_already_exists():
    """Test that no extra blank line is added when one already exists."""
    log = """/path/to/file1.js
  1:1  error  Unexpected token

✖ 1 problem (1 error, 0 warnings)"""

    expected = """/path/to/file1.js
  1:1  error  Unexpected token

✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_no_blank_line_when_previous_is_file_path():
    """Test that no blank line is added when previous line is a file path."""
    log = """/path/to/file1.js
✖ 1 problem (1 error, 0 warnings)"""

    expected = """/path/to/file1.js
✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_trailing_newline_preservation():
    """Test that trailing newline behavior is preserved."""
    # Input without trailing newline
    log_no_newline = """/path/to/file1.js
  1:1  error  Unexpected token"""

    result_no_newline = remove_repetitive_eslint_warnings(log_no_newline)
    assert not result_no_newline.endswith("\n")

    # Input with trailing newline
    log_with_newline = """/path/to/file1.js
  1:1  error  Unexpected token
"""

    result_with_newline = remove_repetitive_eslint_warnings(log_with_newline)
    assert result_with_newline.endswith("\n")


def test_unsupported_file_extensions():
    """Test that files with unsupported extensions are not processed as ESLint files."""
    log = """/path/to/file1.py
  1:1  error  Some error

/path/to/file2.css
  1:1  warning  Some warning

✖ 2 problems (1 error, 1 warning)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_empty_file_sections():
    """Test files that have no error or warning lines."""
    log = """/path/to/file1.js

/path/to/file2.js
  1:1  error  Actual error

✖ 1 problem (1 error, 0 warnings)"""

    expected = """/path/to/file2.js
  1:1  error  Actual error

✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_whitespace_in_error_lines():
    """Test that error lines with different whitespace patterns are correctly identified."""
    log = """/path/to/file1.js
    1:1  error  Error with more spaces
\t2:1  error  Error with tab
  3:1  error  Error with normal spaces

✖ 3 problems (3 errors, 0 warnings)"""

    expected = """/path/to/file1.js
    1:1  error  Error with more spaces
\t2:1  error  Error with tab
  3:1  error  Error with normal spaces

✖ 3 problems (3 errors, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_complex_real_world_scenario():
    """Test a complex real-world ESLint output scenario."""
    log = """/path/to/src/component1.tsx
  12:5   error    'React' must be in scope when using JSX  react/react-in-jsx-scope
  15:10  warning  'useState' is defined but never used      @typescript-eslint/no-unused-vars
  20:1   error    Missing semicolon                         semi

/path/to/src/component2.js
  5:1   warning  'var' is deprecated                       no-var
  8:15  warning  Missing trailing comma                     comma-dangle

/path/to/src/utils.ts
  3:1   error    Expected indentation of 2 spaces          indent
  10:5  error    'console' is not defined                   no-console
  15:1  warning  Prefer const over let                      prefer-const

✖ 8 problems (4 errors, 4 warnings)
  4 errors and 0 warnings potentially fixable with the --fix option."""

    expected = """/path/to/src/component1.tsx
  12:5   error    'React' must be in scope when using JSX  react/react-in-jsx-scope
  20:1   error    Missing semicolon                         semi
/path/to/src/utils.ts
  3:1   error    Expected indentation of 2 spaces          indent
  10:5  error    'console' is not defined                   no-console

✖ 8 problems (4 errors, 4 warnings)
  4 errors and 0 warnings potentially fixable with the --fix option."""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected
