from typing import cast

from services.github.types.github_types import BaseArgs
from utils.files.is_target_test_file import is_target_test_file


def test_is_target_test_file_with_add_unit_tests():
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "issue_title": "Schedule: Add unit tests to services/webhook/schedule_handler.py",
        },
    )

    assert is_target_test_file("services/webhook/test_schedule_handler.py", base_args)
    assert not is_target_test_file("services/webhook/test_issue_handler.py", base_args)
    assert not is_target_test_file("services/webhook/schedule_handler.py", base_args)


def test_is_target_test_file_with_increase_coverage():
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "issue_title": "Schedule: Increase test coverage for utils/files/is_test_file.py",
        },
    )

    assert is_target_test_file("utils/files/test_is_test_file.py", base_args)
    assert is_target_test_file("tests/unit/test_is_test_file.py", base_args)
    assert not is_target_test_file("utils/files/test_is_code_file.py", base_args)
    assert not is_target_test_file("utils/files/is_test_file.py", base_args)


def test_is_target_test_file_with_non_test_file():
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "issue_title": "Schedule: Add unit tests to services/chat_with_agent.py",
        },
    )

    assert not is_target_test_file("services/chat_with_agent.py", base_args)


def test_is_target_test_file_with_no_issue_title():
    base_args = cast(BaseArgs, {"owner": "test", "repo": "test"})

    assert is_target_test_file("services/test_chat_with_agent.py", base_args)


def test_is_target_test_file_with_non_schedule_title():
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "issue_title": "Fix bug in payment processing",
        },
    )

    assert is_target_test_file("services/test_payment.py", base_args)
