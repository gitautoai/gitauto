def get_issue_title():
    return "Add unit tests to improve coverage"


def get_issue_body(file_path: str, statement_coverage: float | None = None):
    coverage_info = ""
    if statement_coverage is not None:
        coverage_info = f" (Current statement coverage: {statement_coverage}%)"

    return f"""This file has been identified as needing unit test coverage{coverage_info}:

- {file_path}

## Action Required

Please add comprehensive unit tests for this file to improve test coverage. Focus on:

- Testing main functionality and logic paths
- Edge cases and error handling
- Input validation
- Return value verification

## Benefits of Adding Tests

- Ensure code reliability and correctness
- Prevent regressions during future changes
- Make refactoring safer and easier
- Document expected behavior for other developers
- Improve overall codebase quality

## Test Guidelines

- Write clear, descriptive test names
- Test both happy path and error scenarios
- Keep tests focused and independent
- Use appropriate test data and mocks when needed
- Ensure tests are maintainable and readable

"""
