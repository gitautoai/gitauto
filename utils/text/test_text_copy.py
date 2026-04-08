from utils.text.build_pr_completion_comment import build_pr_completion_comment
from utils.text.text_copy import (
    git_command,
    UPDATE_COMMENT_FOR_422,
    UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE,
)
from config import EMAIL_LINK, PRODUCT_ID
from constants.urls import DASHBOARD_TRIGGERS_URL
from constants.messages import COMPLETED_PR


def test_git_command():
    branch_name = "feature/test-branch"
    result = git_command(branch_name)

    expected = (
        f"\n\n## Test these changes locally\n\n"
        f"```\n"
        f"git fetch origin\n"
        f"git checkout {branch_name}\n"
        f"git pull origin {branch_name}\n"
        f"```"
    )

    assert result == expected


def test_build_pr_completion_comment_bot_creator_bot_sender():
    pr_creator = "sentry-io[bot]"
    sender_name = "gitauto-ai[bot]"
    result = build_pr_completion_comment(pr_creator, sender_name, trigger="dashboard")

    expected = f"{COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_build_pr_completion_comment_bot_creator_product_sender():
    pr_creator = "sentry-io[bot]"
    sender_name = f"user-{PRODUCT_ID}"
    result = build_pr_completion_comment(pr_creator, sender_name, trigger="dashboard")

    expected = f"{COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_build_pr_completion_comment_bot_creator_human_sender():
    pr_creator = "sentry-io[bot]"
    sender_name = "human-user"
    result = build_pr_completion_comment(pr_creator, sender_name, trigger="dashboard")

    expected = f"@{sender_name} {COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_build_pr_completion_comment_same_creator_and_sender():
    pr_creator = "test-user"
    sender_name = "test-user"
    result = build_pr_completion_comment(pr_creator, sender_name, trigger="dashboard")

    expected = f"@{pr_creator} {COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_build_pr_completion_comment_product_in_sender():
    pr_creator = "test-user"
    sender_name = f"user-{PRODUCT_ID}"
    result = build_pr_completion_comment(pr_creator, sender_name, trigger="dashboard")

    expected = f"@{pr_creator} {COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_build_pr_completion_comment_different_creator_and_sender():
    pr_creator = "test-user1"
    sender_name = "test-user2"
    result = build_pr_completion_comment(pr_creator, sender_name, trigger="dashboard")

    expected = f"@{pr_creator} @{sender_name} {COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_build_pr_completion_comment_automation_true():
    pr_creator = "test-user"
    sender_name = "test-user"
    result = build_pr_completion_comment(pr_creator, sender_name, trigger="schedule")

    expected = f"@{pr_creator} {COMPLETED_PR}\n\nI autonomously open pull requests on a schedule. You can manage your schedule [here]({DASHBOARD_TRIGGERS_URL}). Should you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_git_command_with_special_characters():
    branch_name = "feature/fix-bug-#123"
    result = git_command(branch_name)

    expected = (
        f"\n\n## Test these changes locally\n\n"
        f"```\n"
        f"git fetch origin\n"
        f"git checkout {branch_name}\n"
        f"git pull origin {branch_name}\n"
        f"```"
    )

    assert result == expected


def test_git_command_empty_branch_name():
    branch_name = ""
    result = git_command(branch_name)

    expected = (
        f"\n\n## Test these changes locally\n\n"
        f"```\n"
        f"git fetch origin\n"
        f"git checkout {branch_name}\n"
        f"git pull origin {branch_name}\n"
        f"```"
    )

    assert result == expected


def test_update_comment_constants():
    assert EMAIL_LINK in UPDATE_COMMENT_FOR_422
    assert "I'm a bit lost here!" in UPDATE_COMMENT_FOR_422
    assert "feedback or need help?" in UPDATE_COMMENT_FOR_422
    assert EMAIL_LINK in UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE
    assert (
        "No changes were detected" in UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE
    )
    assert "feedback or need help?" in UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE


def test_build_pr_completion_comment_automation_bot_creator_bot_sender():
    pr_creator = "sentry-io[bot]"
    sender_name = "gitauto-ai[bot]"
    result = build_pr_completion_comment(pr_creator, sender_name, trigger="schedule")

    expected = f"{COMPLETED_PR}\n\nI autonomously open pull requests on a schedule. You can manage your schedule [here]({DASHBOARD_TRIGGERS_URL}). Should you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_build_pr_completion_comment_automation_different_users():
    pr_creator = "test-user1"
    sender_name = "test-user2"
    result = build_pr_completion_comment(pr_creator, sender_name, trigger="schedule")

    expected = f"@{pr_creator} @{sender_name} {COMPLETED_PR}\n\nI autonomously open pull requests on a schedule. You can manage your schedule [here]({DASHBOARD_TRIGGERS_URL}). Should you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_build_pr_completion_comment_edge_case_product_id_in_creator():
    pr_creator = f"user-{PRODUCT_ID}-test"
    sender_name = "different-user"
    result = build_pr_completion_comment(pr_creator, sender_name, trigger="dashboard")

    expected = f"@{pr_creator} @{sender_name} {COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_build_pr_completion_comment_empty_names():
    pr_creator = ""
    sender_name = ""
    result = build_pr_completion_comment(pr_creator, sender_name, trigger="dashboard")
    expected = f"@ {COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected
