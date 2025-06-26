def get_issue_title_for_pr_merged(pr_number: int):
    return f"Add unit tests for files changed in PR #{pr_number}"


def get_issue_body_for_pr_merged(pr_number: int, file_list: list[str]):
    file_list_str = "\n".join([f"- {file}" for file in file_list])

    return f"""The following files were changed in PR #{pr_number} that might need test coverage:

{file_list_str}

## Action Required

Please add unit tests for these files to improve test coverage. Comprehensive test coverage helps:

- Ensure code reliability
- Prevent regressions
- Make future refactoring easier
- Document expected behavior

Focus on testing important logic paths and edge cases.

## Test Scope Guidelines

- Concentrate on testing only the files modified in this PR
- Tests for dependent files might need updates if function signatures or behaviors changed
- Keep code changes minimal to simplify review and merging
- Adapt your approach based on the specific changes made in the PR

"""
