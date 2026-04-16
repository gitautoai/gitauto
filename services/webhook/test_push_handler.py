# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch

from services.github.branches.get_required_status_checks import StatusChecksResult
from services.github.types.webhook.push import PushWebhookPayload
from services.webhook.push_handler import handle_push


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_tag_push_returns_early(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/tags/v1.0.0",
        "commits": [],
    }

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_repository.assert_not_called()
    mock_get_token.assert_not_called()
    mock_get_open_prs.assert_not_called()
    mock_update_pr.assert_not_called()
    mock_logger.info.assert_called()


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.get_default_branch")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_repository_not_found_falls_back_to_default_branch(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_get_default_branch,
    _mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/main",
        "commits": [{"added": ["src/app.py"], "modified": [], "removed": []}],
    }

    mock_get_repository.return_value = None
    mock_get_token.return_value = "test-token"
    mock_get_default_branch.return_value = "main"
    mock_get_open_prs.return_value = [{"number": 1, "title": "PR 1"}]
    mock_update_pr.return_value = ("updated", None)

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_repository.assert_called_once_with(owner_id=123, repo_id=456)
    mock_get_token.assert_called_once_with(installation_id=789)
    mock_get_default_branch.assert_called_once()
    mock_get_open_prs.assert_called_once()
    mock_update_pr.assert_called_once()


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_local_feature_to_remote_feature_not_handled(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/feature-branch",
        "commits": [],
    }

    mock_get_repository.return_value = {"target_branch": "main"}
    mock_get_token.return_value = "test-token"

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_repository.assert_called_once_with(owner_id=123, repo_id=456)
    mock_get_token.assert_called_once_with(installation_id=789)
    mock_get_open_prs.assert_not_called()
    mock_update_pr.assert_not_called()
    mock_logger.info.assert_called()


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_remote_feature_to_remote_staging_not_handled(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/staging",
        "commits": [],
    }

    mock_get_repository.return_value = {"target_branch": "main"}
    mock_get_token.return_value = "test-token"

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_repository.assert_called_once_with(owner_id=123, repo_id=456)
    mock_get_token.assert_called_once_with(installation_id=789)
    mock_get_open_prs.assert_not_called()
    mock_update_pr.assert_not_called()
    mock_logger.info.assert_called()


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_no_open_prs_returns_early(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/main",
        "commits": [],
    }

    mock_get_repository.return_value = {"target_branch": "main"}
    mock_get_token.return_value = "test-token"
    mock_get_open_prs.return_value = []

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_repository.assert_called_once_with(owner_id=123, repo_id=456)
    mock_get_token.assert_called_once_with(installation_id=789)
    mock_get_open_prs.assert_called_once_with(
        owner="test-owner", repo="test-repo", token="test-token"
    )
    mock_update_pr.assert_not_called()
    mock_logger.info.assert_called()


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_local_main_to_remote_main_handled(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/main",
        "commits": [{"added": ["src/app.py"], "modified": [], "removed": []}],
    }

    mock_get_repository.return_value = {"target_branch": "main"}
    mock_get_token.return_value = "test-token"
    mock_get_open_prs.return_value = [
        {"number": 1, "title": "PR 1"},
        {"number": 2, "title": "PR 2"},
    ]
    mock_update_pr.return_value = ("updated", None)

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_repository.assert_called_once_with(owner_id=123, repo_id=456)
    mock_get_token.assert_called_once_with(installation_id=789)
    mock_get_open_prs.assert_called_once_with(
        owner="test-owner", repo="test-repo", token="test-token"
    )
    assert mock_update_pr.call_count == 2
    mock_update_pr.assert_any_call(
        owner="test-owner", repo="test-repo", pr_number=1, token="test-token"
    )
    mock_update_pr.assert_any_call(
        owner="test-owner", repo="test-repo", pr_number=2, token="test-token"
    )
    mock_logger.info.assert_called()


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_remote_feature_to_remote_main_handled(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/main",
        "commits": [{"added": ["src/app.py"], "modified": [], "removed": []}],
    }

    mock_get_repository.return_value = {"target_branch": "main"}
    mock_get_token.return_value = "test-token"
    mock_get_open_prs.return_value = [{"number": 5, "title": "Feature PR"}]
    mock_update_pr.return_value = ("updated", None)

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_repository.assert_called_once_with(owner_id=123, repo_id=456)
    mock_get_token.assert_called_once_with(installation_id=789)
    mock_get_open_prs.assert_called_once_with(
        owner="test-owner", repo="test-repo", token="test-token"
    )
    mock_update_pr.assert_called_once_with(
        owner="test-owner", repo="test-repo", pr_number=5, token="test-token"
    )
    mock_logger.info.assert_called()


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_with_failed_updates(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/main",
        "commits": [{"added": ["src/app.py"], "modified": [], "removed": []}],
    }

    mock_get_repository.return_value = {"target_branch": "main"}
    mock_get_token.return_value = "test-token"
    mock_get_open_prs.return_value = [
        {"number": 1, "title": "PR 1"},
        {"number": 2, "title": "PR 2"},
        {"number": 3, "title": "PR 3"},
    ]
    mock_update_pr.side_effect = [
        ("updated", None),
        ("failed", "HTTP 500: Internal server error"),
        ("updated", None),
    ]

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    assert mock_update_pr.call_count == 3
    # Check the result summary log (last info call)
    result_call = mock_logger.info.call_args_list[-1][0][0]
    assert "- Failed: 1" in result_call
    assert "PR #2: HTTP 500" in result_call


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_with_merge_conflicts(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/main",
        "commits": [{"added": ["src/app.py"], "modified": [], "removed": []}],
    }

    mock_get_repository.return_value = {"target_branch": "main"}
    mock_get_token.return_value = "test-token"
    mock_get_open_prs.return_value = [
        {"number": 1, "title": "PR 1"},
        {"number": 2, "title": "PR 2"},
        {"number": 3, "title": "PR 3"},
    ]
    mock_update_pr.side_effect = [
        ("updated", None),
        ("conflict", None),
        ("up_to_date", None),
    ]

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    assert mock_update_pr.call_count == 3
    # Check the result summary log (last info call)
    result_call = mock_logger.info.call_args_list[-1][0][0]
    assert "- Updated: 1" in result_call
    assert "- Up-to-date: 1" in result_call
    assert "- Conflicts: 1" in result_call
    assert "- Failed: 0" in result_call
    assert "PR #2" in result_call


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_no_gitauto_prs_returns_early(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/main",
        "commits": [],
    }

    mock_get_repository.return_value = {"target_branch": "main"}
    mock_get_token.return_value = "test-token"
    mock_get_open_prs.return_value = []

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_repository.assert_called_once_with(owner_id=123, repo_id=456)
    mock_get_token.assert_called_once_with(installation_id=789)
    mock_get_open_prs.assert_called_once_with(
        owner="test-owner", repo="test-repo", token="test-token"
    )
    mock_update_pr.assert_not_called()
    mock_logger.info.assert_called()


# --- Empty target_branch fallback tests ---


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.get_default_branch")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_empty_target_branch_falls_back_to_default(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_get_default_branch,
    _mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/master",
        "commits": [{"added": ["src/app.py"], "modified": [], "removed": []}],
    }

    mock_get_repository.return_value = {"target_branch": ""}
    mock_get_token.return_value = "test-token"
    mock_get_default_branch.return_value = "master"
    mock_get_open_prs.return_value = [{"number": 10, "title": "PR 10"}]
    mock_update_pr.return_value = ("updated", None)

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_default_branch.assert_called_once()
    mock_get_open_prs.assert_called_once()
    mock_update_pr.assert_called_once_with(
        owner="test-owner", repo="test-repo", pr_number=10, token="test-token"
    )


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.get_default_branch")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_empty_target_branch_default_branch_not_found(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_get_default_branch,
    mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/main",
        "commits": [],
    }

    mock_get_repository.return_value = {"target_branch": ""}
    mock_get_token.return_value = "test-token"
    mock_get_default_branch.return_value = None

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_default_branch.assert_called_once()
    mock_get_open_prs.assert_not_called()
    mock_update_pr.assert_not_called()
    mock_logger.info.assert_called()


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.get_default_branch")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_empty_target_branch_non_default_push_ignored(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_get_default_branch,
    mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/feature-branch",
        "commits": [],
    }

    mock_get_repository.return_value = {"target_branch": ""}
    mock_get_token.return_value = "test-token"
    mock_get_default_branch.return_value = "master"

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_default_branch.assert_called_once()
    mock_get_open_prs.assert_not_called()
    mock_update_pr.assert_not_called()
    mock_logger.info.assert_called()


# --- Test-only push filtering tests ---


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.get_required_status_checks")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_test_only_strict_false_skips_updates(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_get_status_checks,
    mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/main",
        "commits": [
            {"added": ["tests/test_utils.py"], "modified": [], "removed": []},
            {"added": [], "modified": ["src/test_app.py"], "removed": []},
        ],
    }

    mock_get_repository.return_value = {"target_branch": "main"}
    mock_get_token.return_value = "test-token"
    mock_get_status_checks.return_value = StatusChecksResult(
        status_code=200, checks=["ci/test"], strict=False
    )

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_status_checks.assert_called_once_with(
        owner="test-owner", repo="test-repo", branch="main", token="test-token"
    )
    mock_get_open_prs.assert_not_called()
    mock_update_pr.assert_not_called()
    # Check the skip log (last info call)
    assert "test-only push" in mock_logger.info.call_args_list[-1][0][0]


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.get_required_status_checks")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_test_only_strict_true_proceeds(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_get_status_checks,
    _mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/main",
        "commits": [
            {"added": ["tests/test_utils.py"], "modified": [], "removed": []},
        ],
    }

    mock_get_repository.return_value = {"target_branch": "main"}
    mock_get_token.return_value = "test-token"
    mock_get_status_checks.return_value = StatusChecksResult(
        status_code=200, checks=["ci/test"], strict=True
    )
    mock_get_open_prs.return_value = [{"number": 1, "title": "PR 1"}]
    mock_update_pr.return_value = ("updated", None)

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_status_checks.assert_called_once_with(
        owner="test-owner", repo="test-repo", branch="main", token="test-token"
    )
    mock_get_open_prs.assert_called_once()
    mock_update_pr.assert_called_once_with(
        owner="test-owner", repo="test-repo", pr_number=1, token="test-token"
    )


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.get_required_status_checks")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_mixed_files_proceeds_regardless(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_get_status_checks,
    _mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/main",
        "commits": [
            {
                "added": ["tests/test_utils.py"],
                "modified": ["src/app.py"],
                "removed": [],
            },
        ],
    }

    mock_get_repository.return_value = {"target_branch": "main"}
    mock_get_token.return_value = "test-token"
    mock_get_open_prs.return_value = [{"number": 1, "title": "PR 1"}]
    mock_update_pr.return_value = ("updated", None)

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_status_checks.assert_not_called()
    mock_get_open_prs.assert_called_once()
    mock_update_pr.assert_called_once()


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.get_required_status_checks")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_empty_commits_proceeds(
    mock_get_repository,
    mock_get_token,
    mock_get_open_prs,
    mock_update_pr,
    mock_get_status_checks,
    _mock_logger,
):
    payload = {
        "repository": {
            "owner": {"id": 123, "login": "test-owner"},
            "id": 456,
            "name": "test-repo",
        },
        "installation": {"id": 789},
        "ref": "refs/heads/main",
        "commits": [],
    }

    mock_get_repository.return_value = {"target_branch": "main"}
    mock_get_token.return_value = "test-token"
    mock_get_open_prs.return_value = [{"number": 1, "title": "PR 1"}]
    mock_update_pr.return_value = ("updated", None)

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_status_checks.assert_not_called()
    mock_get_open_prs.assert_called_once()
    mock_update_pr.assert_called_once()
