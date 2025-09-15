#!/usr/bin/env python3

import os

from remove_repetitive_eslint_warnings import remove_repetitive_eslint_warnings

import pytest
from config import UTF8


def test_empty_input():
    """Test with empty string input."""
    assert remove_repetitive_eslint_warnings("") == ""


def test_none_input():
    """Test with None input."""
    assert remove_repetitive_eslint_warnings(None) is None


def test_no_eslint_files():
    """Test with log that contains no ESLint file paths."""
    log = "Some random log content\nAnother line\nNo ESLint files here"
    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_file_with_only_warnings():
    """Test file with only warnings (should be filtered out)."""
    log = """/path/to/file.ts
  10:5  warning  Missing semicolon  semi
  15:3  warning  Unused variable  no-unused-vars"""

    result = remove_repetitive_eslint_warnings(log)
    # Should be empty since no errors, only warnings
    assert result == ""


def test_file_with_only_errors():
    """Test file with only errors (should be kept)."""
    log = """/path/to/file.ts
  10:5  error  Missing semicolon  semi
  15:3  error  Unused variable  no-unused-vars"""

    expected = """/path/to/file.ts
  10:5  error  Missing semicolon  semi
  15:3  error  Unused variable  no-unused-vars"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_file_with_mixed_warnings_and_errors():
    """Test file with both warnings and errors (only errors should be kept)."""
    log = """/path/to/file.ts
  10:5  warning  Missing semicolon  semi
  15:3  error  Unused variable  no-unused-vars
  20:1  warning  Another warning  some-rule
  25:2  error  Another error  another-rule"""

    expected = """/path/to/file.ts
  15:3  error  Unused variable  no-unused-vars
  25:2  error  Another error  another-rule"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_multiple_files_with_errors():
    """Test multiple files with errors."""
    log = """/path/to/file1.ts
  10:5  error  Error 1  rule1
  15:3  error  Error 2  rule2

/path/to/file2.js
  5:1  error  Error 3  rule3"""

    expected = """/path/to/file1.ts
  10:5  error  Error 1  rule1
  15:3  error  Error 2  rule2
/path/to/file2.js
  5:1  error  Error 3  rule3"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_multiple_files_mixed_content():
    """Test multiple files where some have errors and some don't."""
    log = """/path/to/file1.ts
  10:5  warning  Warning 1  rule1
  15:3  warning  Warning 2  rule2

/path/to/file2.js
  5:1  error  Error 1  rule3
  8:2  warning  Warning 3  rule4

/path/to/file3.tsx
  1:1  warning  Only warnings here  rule5"""

    expected = """/path/to/file2.js
  5:1  error  Error 1  rule3"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_file_path_with_colon_ignored():
    """Test that file paths containing colons are not treated as ESLint files."""
    log = """/path/to/file.ts:10:5
  This should not be treated as a file path
  10:5  error  Some error  rule1"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_non_js_ts_files_ignored():
    """Test that non-JS/TS files are ignored."""
    log = """/path/to/file.py
  10:5  error  Some error  rule1

/path/to/file.txt
  15:3  error  Another error  rule2"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == log


def test_summary_with_x_mark():
    """Test that summary lines with ✖ mark are preserved with proper spacing."""
    log = """/path/to/file.ts
  10:5  error  Error 1  rule1
✖ 1 problem (1 error, 0 warnings)"""

    expected = """/path/to/file.ts
  10:5  error  Error 1  rule1

✖ 1 problem (1 error, 0 warnings)"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_error_command_failed_stops_processing():
    """Test that 'error Command failed' stops file processing."""
    log = """/path/to/file.ts
  10:5  error  Error 1  rule1
error Command failed with exit code 1.
  15:3  error  This should not be processed  rule2"""

    expected = """/path/to/file.ts
  10:5  error  Error 1  rule1
error Command failed with exit code 1.
  15:3  error  This should not be processed  rule2"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_trailing_newline_preservation():
    """Test that trailing newline behavior is preserved."""
    # Input without trailing newline
    log_no_newline = "/path/to/file.ts\n  10:5  error  Error 1  rule1"
    result_no_newline = remove_repetitive_eslint_warnings(log_no_newline)
    assert not result_no_newline.endswith("\n")

    # Input with trailing newline
    log_with_newline = "/path/to/file.ts\n  10:5  error  Error 1  rule1\n"
    result_with_newline = remove_repetitive_eslint_warnings(log_with_newline)
    assert result_with_newline.endswith("\n")


def test_different_file_extensions():
    """Test different supported file extensions."""
    log = """/path/to/file.js
  10:5  error  JS Error  rule1

/path/to/file.ts
  15:3  error  TS Error  rule2

/path/to/file.tsx
  20:1  error  TSX Error  rule3"""

    expected = """/path/to/file.js
  10:5  error  JS Error  rule1
/path/to/file.ts
  15:3  error  TS Error  rule2
/path/to/file.tsx
  20:1  error  TSX Error  rule3"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_whitespace_in_error_lines():
    """Test various whitespace patterns in error lines."""
    log = """/path/to/file.ts
    10:5  error  Error with spaces  rule1
\t15:3  error  Error with tab  rule2
  20:1  error  Error with normal spaces  rule3"""

    expected = """/path/to/file.ts
    10:5  error  Error with spaces  rule1
\t15:3  error  Error with tab  rule2
  20:1  error  Error with normal spaces  rule3"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_complex_real_world_scenario():
    """Test a complex scenario similar to real ESLint output."""
    log = """
/src/components/Header.tsx
  12:5   warning  'React' is defined but never used  @typescript-eslint/no-unused-vars
  25:10  error    Missing return type on function      @typescript-eslint/explicit-function-return-type
  30:15  warning  Prefer const assertion                prefer-const

/src/utils/helpers.js
  5:1   warning  Missing semicolon                     semi
  8:10  warning  Unused variable 'temp'                no-unused-vars

/src/types/index.ts
  15:5  error    Type annotation missing               @typescript-eslint/no-explicit-any
  20:1  error    Export not found                      import/no-unresolved

✖ 7 problems (3 errors, 4 warnings)
  3 errors and 0 warnings potentially fixable with the --fix option.
"""

    expected = """
/src/components/Header.tsx
  25:10  error    Missing return type on function      @typescript-eslint/explicit-function-return-type
/src/types/index.ts
  15:5  error    Type annotation missing               @typescript-eslint/no-explicit-any
  20:1  error    Export not found                      import/no-unresolved

✖ 7 problems (3 errors, 4 warnings)
  3 errors and 0 warnings potentially fixable with the --fix option.
"""

    result = remove_repetitive_eslint_warnings(log)
    assert result == expected


def test_remove_repetitive_eslint_warnings_integration():
    """Integration test using payload files."""
    payload_path = os.path.join(
        os.path.dirname(__file__), "../../payloads/circleci/eslint_build_log.txt"
    )

    # Skip if payload file doesn't exist
    if not os.path.exists(payload_path):
        pytest.skip("Payload file not found")

    with open(payload_path, "r", encoding=UTF8) as f:
        test_log = f.read()

    cleaned_path = os.path.join(
        os.path.dirname(__file__),
        "../../payloads/circleci/eslint_build_log_cleaned.txt",
    )

    # Skip if cleaned file doesn't exist
    if not os.path.exists(cleaned_path):
        pytest.skip("Cleaned payload file not found")

    with open(cleaned_path, "r", encoding=UTF8) as f:
        expected_output = f.read()

    result = remove_repetitive_eslint_warnings(test_log)
    assert result == expected_output


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])
