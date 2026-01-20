from utils.files.get_impl_file_from_issue_title import get_impl_file_from_issue_title


def test_add_unit_tests_prefix():
    title = "Schedule: Add unit tests to services/github/client.py"
    assert get_impl_file_from_issue_title(title) == "services/github/client.py"


def test_uncovered_code_prefix():
    title = "Schedule: Add tests for uncovered code in utils/helpers.py"
    assert get_impl_file_from_issue_title(title) == "utils/helpers.py"


def test_non_matching_title():
    title = "Fix bug in authentication"
    assert get_impl_file_from_issue_title(title) is None


def test_empty_title():
    assert get_impl_file_from_issue_title("") is None


def test_file_at_root():
    title = "Schedule: Add unit tests to client.py"
    assert get_impl_file_from_issue_title(title) == "client.py"


def test_no_file_extension():
    title = "Fix the Makefile"
    assert get_impl_file_from_issue_title(title) is None
