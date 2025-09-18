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
