from typing import cast
from unittest.mock import MagicMock, patch

from services.github.types.github_types import CheckSuiteCompletedPayload
from services.webhook.successful_check_suite_handler import (
    handle_successful_check_suite,
)


def test_handle_successful_check_suite_with_pr():
    payload = {
        "check_suite": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "pull_requests": [
                {
                    "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
                    "id": 2131041354,
                    "number": 123,
                }
            ],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
            },
        },
    }

    with patch(
        "services.webhook.successful_check_suite_handler.supabase"
    ) as mock_supabase:
        # Setup mock chain for select
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = MagicMock(data=[{"id": 100}])

        # Setup mock chain for update
        mock_update = MagicMock()
        mock_update_eq = MagicMock()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_update_eq

        # Execute
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))

        # Verify select was called
        mock_table.select.assert_called_once_with("id")
        mock_select.eq.assert_called_once_with("repo_id", 871345449)
        mock_eq1.eq.assert_called_once_with("pr_number", 123)
        mock_eq2.eq.assert_called_once_with("owner_id", 4620828)

        # Verify update was called
        mock_table.update.assert_called_once_with({"is_test_passed": True})
        mock_update.eq.assert_called_once_with("id", 100)
        mock_update_eq.execute.assert_called_once()


def test_handle_successful_check_suite_without_pr():
    payload = {
        "check_suite": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "pull_requests": [],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
            },
        },
    }

    with patch(
        "services.webhook.successful_check_suite_handler.supabase"
    ) as mock_supabase:
        # Execute
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))

        # Verify no database call was made
        mock_supabase.table.assert_not_called()


def test_handle_successful_check_suite_no_usage_record_found():
    payload = {
        "check_suite": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "pull_requests": [
                {
                    "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
                    "id": 2131041354,
                    "number": 123,
                }
            ],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
            },
        },
    }

    with patch(
        "services.webhook.successful_check_suite_handler.supabase"
    ) as mock_supabase:
        # Setup mock to return empty data
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = MagicMock(data=[])

        # Execute
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))

        # Verify select was called but update was not
        mock_table.select.assert_called_once()
        mock_table.update.assert_not_called()


def test_handle_successful_check_suite_with_exception():
    payload = {
        "check_suite": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "pull_requests": [
                {
                    "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
                    "id": 2131041354,
                    "number": 123,
                }
            ],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
            },
        },
    }

    with patch(
        "services.webhook.successful_check_suite_handler.supabase"
    ) as mock_supabase:
        # Setup mock to raise exception
        mock_supabase.table.side_effect = Exception("Database error")

        # Execute - should not raise due to handle_exceptions decorator
        result = handle_successful_check_suite(
            cast(CheckSuiteCompletedPayload, payload)
        )

        # Verify it returns None (default_return_value)
        assert result is None


@patch("services.webhook.successful_check_suite_handler.check_commit_has_skip_ci")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_auto_merge_success(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_files,
    mock_merge_pr,
    mock_check_skip_ci,
):
    payload = {
        "check_suite": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "head_sha": "abc123",
            "head_branch": "feature-branch",
            "pull_requests": [
                {
                    "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
                    "id": 2131041354,
                    "number": 123,
                    "title": "Test PR",
                    "body": "Test PR body",
                    "user": {"login": "test-user", "id": 12345},
                    "head": {"ref": "feature-branch", "sha": "abc123"},
                    "base": {"ref": "main", "sha": "def456"},
                    "mergeable": True,
                    "mergeable_state": "clean",
                }
            ],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
                "type": "Organization",
            },
            "clone_url": "https://github.com/test-owner/test-repo.git",
            "fork": False,
        },
        "installation": {"id": 12345},
        "sender": {"id": 12345, "login": "test-sender"},
    }

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "squash",
        "auto_merge_only_test_files": False,
    }
    mock_get_token.return_value = "test-token"
    mock_check_skip_ci.return_value = False
    mock_get_files.return_value = [
        {"filename": "test_something.py", "status": "modified"}
    ]
    mock_is_test_file.return_value = True

    with patch(
        "services.webhook.successful_check_suite_handler.supabase"
    ) as mock_supabase:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = MagicMock(data=[{"id": 100}])

        mock_update = MagicMock()
        mock_update_eq = MagicMock()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_update_eq

        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))

        mock_merge_pr.assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            token="test-token",
            merge_method="squash",
        )


@patch("services.webhook.successful_check_suite_handler.check_commit_has_skip_ci")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_auto_merge_disabled(
    mock_get_repo_features,
    mock_get_token,
    mock_get_files,
    mock_merge_pr,
    mock_check_skip_ci,
):
    payload = {
        "check_suite": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "head_sha": "abc123",
            "head_branch": "feature-branch",
            "pull_requests": [
                {
                    "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
                    "id": 2131041354,
                    "number": 123,
                }
            ],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
            },
        },
        "installation": {"id": 12345},
    }

    mock_get_repo_features.return_value = {"auto_merge": False}

    with patch(
        "services.webhook.successful_check_suite_handler.supabase"
    ) as mock_supabase:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = MagicMock(data=[{"id": 100}])

        mock_update = MagicMock()
        mock_update_eq = MagicMock()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_update_eq

        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))

        mock_merge_pr.assert_not_called()


@patch("services.webhook.successful_check_suite_handler.check_commit_has_skip_ci")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_auto_merge_multiple_test_files_changed(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_files,
    mock_merge_pr,
    mock_check_skip_ci,
):
    payload = {
        "check_suite": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "head_sha": "abc123",
            "head_branch": "feature-branch",
            "pull_requests": [
                {
                    "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
                    "id": 2131041354,
                    "number": 123,
                    "title": "Test PR",
                    "body": "Test PR body",
                    "user": {"login": "test-user", "id": 12345},
                    "head": {"ref": "feature-branch", "sha": "abc123"},
                    "base": {"ref": "main", "sha": "def456"},
                    "mergeable": True,
                    "mergeable_state": "clean",
                }
            ],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
                "type": "Organization",
            },
            "clone_url": "https://github.com/test-owner/test-repo.git",
            "fork": False,
        },
        "installation": {"id": 12345},
        "sender": {"id": 12345, "login": "test-sender"},
    }

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": True,
    }
    mock_get_token.return_value = "test-token"
    mock_check_skip_ci.return_value = False
    mock_get_files.return_value = [
        {"filename": "test_something.py", "status": "modified"},
        {"filename": "test_another.py", "status": "modified"},
    ]
    mock_is_test_file.return_value = True

    with patch(
        "services.webhook.successful_check_suite_handler.supabase"
    ) as mock_supabase:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = MagicMock(data=[{"id": 100}])

        mock_update = MagicMock()
        mock_update_eq = MagicMock()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_update_eq

        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))

        mock_merge_pr.assert_called_once()


@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_auto_merge_mixed_test_and_non_test_files(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_files,
    mock_merge_pr,
):
    payload = {
        "check_suite": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "pull_requests": [
                {
                    "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
                    "id": 2131041354,
                    "number": 123,
                }
            ],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
            },
        },
        "installation": {"id": 12345},
    }

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": True,
    }
    mock_get_token.return_value = "test-token"
    mock_get_files.return_value = [
        {"filename": "test_something.py", "status": "modified"},
        {"filename": "src/main.py", "status": "modified"},
    ]

    def is_test_side_effect(filename):
        return filename == "test_something.py"

    mock_is_test_file.side_effect = is_test_side_effect

    with patch(
        "services.webhook.successful_check_suite_handler.supabase"
    ) as mock_supabase:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = MagicMock(data=[{"id": 100}])

        mock_update = MagicMock()
        mock_update_eq = MagicMock()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_update_eq

        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))

        mock_merge_pr.assert_not_called()


@patch("services.webhook.successful_check_suite_handler.check_commit_has_skip_ci")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_auto_merge_with_non_test_files_allowed(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_files,
    mock_merge_pr,
    mock_check_skip_ci,
):
    payload = {
        "check_suite": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "head_sha": "abc123",
            "head_branch": "feature-branch",
            "pull_requests": [
                {
                    "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
                    "id": 2131041354,
                    "number": 123,
                    "title": "Test PR",
                    "body": "Test PR body",
                    "user": {"login": "test-user", "id": 12345},
                    "head": {"ref": "feature-branch", "sha": "abc123"},
                    "base": {"ref": "main", "sha": "def456"},
                    "mergeable": True,
                    "mergeable_state": "clean",
                }
            ],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
                "type": "Organization",
            },
            "clone_url": "https://github.com/test-owner/test-repo.git",
            "fork": False,
        },
        "installation": {"id": 12345},
        "sender": {"id": 12345, "login": "test-sender"},
    }

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": False,
    }
    mock_get_token.return_value = "test-token"
    mock_check_skip_ci.return_value = False
    mock_get_files.return_value = [
        {"filename": "src/main.py", "status": "modified"},
        {"filename": "src/utils.py", "status": "modified"},
    ]
    mock_is_test_file.return_value = False

    with patch(
        "services.webhook.successful_check_suite_handler.supabase"
    ) as mock_supabase:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = MagicMock(data=[{"id": 100}])

        mock_update = MagicMock()
        mock_update_eq = MagicMock()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_update_eq

        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))

        mock_merge_pr.assert_called_once()


@patch("services.webhook.successful_check_suite_handler.create_empty_commit")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.check_commit_has_skip_ci")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_auto_merge_blocked_skip_ci(
    mock_get_repo_features,
    mock_get_token,
    mock_check_skip_ci,
    mock_create_comment,
    mock_create_empty_commit,
):
    payload = {
        "check_suite": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "head_sha": "abc123",
            "head_branch": "gitauto/issue-456",
            "pull_requests": [
                {
                    "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
                    "id": 2131041354,
                    "number": 123,
                }
            ],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
                "type": "Organization",
            },
            "clone_url": "https://github.com/test-owner/test-repo.git",
            "fork": False,
        },
        "installation": {"id": 12345},
        "sender": {"id": 12345, "login": "test-sender"},
    }

    mock_get_repo_features.return_value = {"auto_merge": True}
    mock_get_token.return_value = "test-token"
    mock_check_skip_ci.return_value = True

    with patch(
        "services.webhook.successful_check_suite_handler.supabase"
    ) as mock_supabase:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = MagicMock(data=[{"id": 100}])

        mock_update = MagicMock()
        mock_update_eq = MagicMock()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_update_eq

        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))

        mock_check_skip_ci.assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            commit_sha="abc123",
            token="test-token",
        )
        mock_create_comment.assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            token="test-token",
            issue_number=123,
            body="Auto-merge blocked: last commit has [skip ci], triggering tests instead...",
        )
        mock_create_empty_commit.assert_called_once()
