from utils.text.issue_template import get_issue_title_for_pr_merged, get_issue_body_for_pr_merged


def test_get_issue_title_for_pr_merged_positive_number():
    result = get_issue_title_for_pr_merged(123)
    assert result == "Add unit tests for files changed in PR #123"


def test_get_issue_title_for_pr_merged_zero():
    result = get_issue_title_for_pr_merged(0)
    assert result == "Add unit tests for files changed in PR #0"


def test_get_issue_title_for_pr_merged_negative_number():
    result = get_issue_title_for_pr_merged(-1)
    assert result == "Add unit tests for files changed in PR #-1"


def test_get_issue_title_for_pr_merged_large_number():
    result = get_issue_title_for_pr_merged(999999)
    assert result == "Add unit tests for files changed in PR #999999"


def test_get_issue_body_for_pr_merged_single_file():
    pr_number = 123
    file_list = ["src/main.py"]
    result = get_issue_body_for_pr_merged(pr_number, file_list)
    
    expected = """The following files were changed in PR #123 that might need test coverage:

- src/main.py

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
    assert result == expected


def test_get_issue_body_for_pr_merged_multiple_files():
    pr_number = 456
    file_list = ["src/main.py", "utils/helper.py", "tests/test_main.py"]
    result = get_issue_body_for_pr_merged(pr_number, file_list)
    
    assert "PR #456" in result
    assert "- src/main.py" in result
    assert "- utils/helper.py" in result
    assert "- tests/test_main.py" in result


def test_get_issue_body_for_pr_merged_empty_file_list():
    pr_number = 789
    file_list = []
    result = get_issue_body_for_pr_merged(pr_number, file_list)
    
    assert "PR #789" in result
    assert "## Action Required" in result


def test_get_issue_body_for_pr_merged_zero_pr_number():
    pr_number = 0
    file_list = ["file.py"]
    result = get_issue_body_for_pr_merged(pr_number, file_list)
    
    assert "PR #0" in result
    assert "- file.py" in result


def test_get_issue_body_for_pr_merged_special_characters_in_filename():
    pr_number = 100
    file_list = ["src/file-with-dashes.py", "utils/file_with_underscores.py", "tests/file.with.dots.py"]
    result = get_issue_body_for_pr_merged(pr_number, file_list)
    
    assert "- src/file-with-dashes.py" in result
    assert "- utils/file_with_underscores.py" in result
    assert "- tests/file.with.dots.py" in result
