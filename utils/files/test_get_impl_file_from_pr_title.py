from utils.files.get_impl_file_from_pr_title import get_impl_file_from_pr_title


def test_add_unit_tests_prefix():
    title = "Schedule: Add unit and integration tests to services/github/client.py"
    assert get_impl_file_from_pr_title(title) == "services/github/client.py"


def test_achieve_coverage_prefix():
    title = "Schedule: Achieve 100% test coverage for utils/helpers.py"
    assert get_impl_file_from_pr_title(title) == "utils/helpers.py"


def test_non_matching_title():
    title = "Fix bug in authentication"
    assert get_impl_file_from_pr_title(title) is None


def test_empty_title():
    assert get_impl_file_from_pr_title("") is None


def test_file_at_root():
    title = "Schedule: Add unit and integration tests to client.py"
    assert get_impl_file_from_pr_title(title) == "client.py"


def test_no_file_extension():
    title = "Fix the Makefile"
    assert get_impl_file_from_pr_title(title) is None


def test_backtick_wrapped_path():
    title = "Schedule: Add unit and integration tests to `services/github/client.py`"
    assert get_impl_file_from_pr_title(title) == "services/github/client.py"


def test_backtick_with_categories():
    title = "Schedule: Strengthen tests for `src/utils/foo.ts` (adversarial, security)"
    assert get_impl_file_from_pr_title(title) == "src/utils/foo.ts"
