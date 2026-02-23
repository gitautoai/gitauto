from typing import cast
from unittest.mock import patch
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
    }

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_repository.assert_not_called()
    mock_get_token.assert_not_called()
    mock_get_open_prs.assert_not_called()
    mock_update_pr.assert_not_called()
    mock_logger.info.assert_not_called()


@patch("services.webhook.push_handler.logger")
@patch("services.webhook.push_handler.update_pull_request_branch")
@patch("services.webhook.push_handler.get_open_pull_requests")
@patch("services.webhook.push_handler.get_installation_access_token")
@patch("services.webhook.push_handler.get_repository")
def test_handle_push_repository_not_found_returns_early(
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
    }

    mock_get_repository.return_value = None

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_repository.assert_called_once_with(owner_id=123, repo_id=456)
    mock_get_token.assert_not_called()
    mock_get_open_prs.assert_not_called()
    mock_update_pr.assert_not_called()
    mock_logger.info.assert_not_called()


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
    }

    mock_get_repository.return_value = {"target_branch": "main"}

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_repository.assert_called_once_with(owner_id=123, repo_id=456)
    mock_get_token.assert_not_called()
    mock_get_open_prs.assert_not_called()
    mock_update_pr.assert_not_called()
    mock_logger.info.assert_not_called()


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
    }

    mock_get_repository.return_value = {"target_branch": "main"}

    result = handle_push(cast(PushWebhookPayload, payload))

    assert result is None
    mock_get_repository.assert_called_once_with(owner_id=123, repo_id=456)
    mock_get_token.assert_not_called()
    mock_get_open_prs.assert_not_called()
    mock_update_pr.assert_not_called()
    mock_logger.info.assert_not_called()


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
    mock_logger.info.assert_not_called()


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
    mock_logger.info.assert_called_once()


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
    mock_logger.info.assert_called_once()


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
    mock_logger.info.assert_called_once()
    call_args = mock_logger.info.call_args[0][0]
    assert "- Failed: 1" in call_args
    assert "PR #2: HTTP 500" in call_args


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
    mock_logger.info.assert_called_once()
    call_args = mock_logger.info.call_args[0][0]
    assert "- Updated: 1" in call_args
    assert "- Up-to-date: 1" in call_args
    assert "- Conflicts: 1" in call_args
    assert "- Failed: 0" in call_args
    assert "PR #2" in call_args


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
    mock_logger.info.assert_not_called()
