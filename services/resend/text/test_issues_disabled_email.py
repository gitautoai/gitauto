from unittest.mock import patch

import pytest

from services.resend.text.issues_disabled_email import get_issues_disabled_email_text


def test_get_issues_disabled_email_text_basic():
    subject, text = get_issues_disabled_email_text("John", "owner", "repo")

    assert subject == "Enable Issues to use GitAuto"
    assert "Hi John," in text
    assert "GitHub Issues are disabled" in text
    assert "https://github.com/owner/repo/settings" in text
    assert "Re-enable" in text
    assert "Wes\nGitAuto" in text


def test_get_issues_disabled_email_text_with_full_name():
    subject, text = get_issues_disabled_email_text("John Doe", "myorg", "myrepo")

    assert subject == "Enable Issues to use GitAuto"
    assert "Hi John Doe," in text
    assert "myorg/myrepo" in text
    assert "https://github.com/myorg/myrepo/settings" in text


def test_get_issues_disabled_email_text_with_special_characters():
    subject, text = get_issues_disabled_email_text(
        "José María", "org-name", "repo_name"
    )

    assert subject == "Enable Issues to use GitAuto"
    assert "Hi José María," in text
    assert "org-name/repo_name" in text
    assert "https://github.com/org-name/repo_name/settings" in text


def test_get_issues_disabled_email_text_with_empty_string():
    subject, text = get_issues_disabled_email_text("", "owner", "repo")

    assert subject == "Enable Issues to use GitAuto"
    assert "Hi ," in text
    assert "owner/repo" in text


def test_get_issues_disabled_email_text_with_none():
    subject, text = get_issues_disabled_email_text(None, "owner", "repo")

    assert subject == "Enable Issues to use GitAuto"
    assert "Hi None," in text
    assert "owner/repo" in text


def test_get_issues_disabled_email_text_includes_instructions():
    _, text = get_issues_disabled_email_text("Alice", "owner", "repo")

    assert "https://github.com/owner/repo/settings" in text
    assert "Re-enable" in text
    assert "schedule" in text


def test_get_issues_disabled_email_text_includes_settings_url():
    _, text = get_issues_disabled_email_text("Bob", "owner", "repo")

    assert "gitauto.ai/settings/triggers" in text


def test_get_issues_disabled_email_text_includes_email_signature():
    with patch(
        "services.resend.text.issues_disabled_email.EMAIL_SIGNATURE",
        "Custom Signature",
    ):
        _, text = get_issues_disabled_email_text("Bob", "owner", "repo")

        assert "Custom Signature" in text
        assert text.endswith("Custom Signature")


def test_get_issues_disabled_email_text_return_type():
    result = get_issues_disabled_email_text("Test User", "owner", "repo")

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)
    assert isinstance(result[1], str)


@pytest.mark.parametrize(
    "user_name,owner,repo,expected_greeting,expected_repo",
    [
        ("Alice", "owner1", "repo1", "Hi Alice,", "owner1/repo1"),
        ("Bob Smith", "myorg", "myrepo", "Hi Bob Smith,", "myorg/myrepo"),
        ("李小明", "chinese-org", "test-repo", "Hi 李小明,", "chinese-org/test-repo"),
        ("O'Connor", "org", "app", "Hi O'Connor,", "org/app"),
        (
            "user@example.com",
            "company",
            "project",
            "Hi user@example.com,",
            "company/project",
        ),
        ("123", "num-org", "num-repo", "Hi 123,", "num-org/num-repo"),
        (
            "user-name_test",
            "test-org",
            "test_repo",
            "Hi user-name_test,",
            "test-org/test_repo",
        ),
    ],
)
def test_get_issues_disabled_email_text_parametrized(
    user_name, owner, repo, expected_greeting, expected_repo
):
    subject, text = get_issues_disabled_email_text(user_name, owner, repo)

    assert subject == "Enable Issues to use GitAuto"
    assert expected_greeting in text
    assert expected_repo in text
    assert f"https://github.com/{owner}/{repo}/settings" in text
