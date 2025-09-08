from unittest.mock import patch
from services.webhook.merge_handler import handle_pr_merged


@patch("services.webhook.merge_handler.slack_notify")
@patch("services.webhook.merge_handler.get_issue_body_for_pr_merged")
@patch("services.webhook.merge_handler.get_issue_title_for_pr_merged")
@patch("services.webhook.merge_handler.create_issue")
@patch("services.webhook.merge_handler.get_installation_access_token")
@patch("services.webhook.merge_handler.get_repository")
@patch("services.webhook.merge_handler.check_availability")
@patch("services.webhook.merge_handler.get_pull_request_files")
@patch("services.webhook.merge_handler.get_coverages")
@patch("services.webhook.merge_handler.is_excluded_from_testing")
@patch("services.webhook.merge_handler.is_type_file")
@patch("services.webhook.merge_handler.is_test_file")
@patch("services.webhook.merge_handler.is_code_file")
def test_handle_pr_merged_success(
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_is_excluded_from_testing,
    mock_get_coverages,
    mock_get_pr_files,
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_create_issue,
    mock_get_issue_title,
    mock_get_issue_body,
    mock_slack_notify,
):
    """Test that handle_pr_merged successfully creates an issue."""
    # Setup mocks
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "src/test.py"}]
    mock_get_coverages.return_value = []
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_is_excluded_from_testing.return_value = False
    mock_get_token.return_value = "test-token"
    mock_get_issue_title.return_value = "Test Issue Title"
    mock_get_issue_body.return_value = "Test issue body content"
    mock_create_issue.return_value = (
        200,
        {"html_url": "https://github.com/test/repo/issues/1"},
    )

    # Create payload
    payload = {
        "installation": {"id": 12345},
        "repository": {
            "owner": {"login": "test-owner", "id": 123},
            "name": "test-repo",
            "id": 456,
        },
        "pull_request": {
            "merged_by": {"login": "test-user"},
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/42",
            "user": {"login": "pr-creator"},
        },
        "number": 42,
    }

    # Execute
    result = handle_pr_merged(payload)

    # Verify
    assert result is None  # Function returns None

    # Verify create_issue was called with correct parameters
    mock_create_issue.assert_called_once()
    call_kwargs = mock_create_issue.call_args.kwargs
    assert call_kwargs["title"] == "Test Issue Title"
    assert call_kwargs["body"] == "Test issue body content"

    # Verify success notification was sent
    success_calls = [
        call
        for call in mock_slack_notify.call_args_list
        if "Issue created" in str(call)
    ]
    assert len(success_calls) > 0


@patch("services.webhook.merge_handler.slack_notify")
@patch("services.webhook.merge_handler.update_repository")
@patch("services.webhook.merge_handler.get_issue_body_for_pr_merged")
@patch("services.webhook.merge_handler.get_issue_title_for_pr_merged")
@patch("services.webhook.merge_handler.create_issue")
@patch("services.webhook.merge_handler.get_installation_access_token")
@patch("services.webhook.merge_handler.get_repository")
@patch("services.webhook.merge_handler.check_availability")
@patch("services.webhook.merge_handler.get_pull_request_files")
@patch("services.webhook.merge_handler.get_coverages")
@patch("services.webhook.merge_handler.is_excluded_from_testing")
@patch("services.webhook.merge_handler.is_type_file")
@patch("services.webhook.merge_handler.is_test_file")
@patch("services.webhook.merge_handler.is_code_file")
def test_handle_pr_merged_410_issues_disabled(
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_is_excluded_from_testing,
    mock_get_coverages,
    mock_get_pr_files,
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_create_issue,
    mock_get_issue_title,
    mock_get_issue_body,
    mock_update_repository,
    mock_slack_notify,
):
    """Test that handle_pr_merged handles 410 (issues disabled) correctly."""
    # Setup mocks
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "src/test.py"}]
    mock_get_coverages.return_value = []
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_is_excluded_from_testing.return_value = False
    mock_get_token.return_value = "test-token"
    mock_get_issue_title.return_value = "Test Issue Title"
    mock_get_issue_body.return_value = "Test issue body content"

    # Mock create_issue to return 410 (issues disabled)
    mock_create_issue.return_value = (410, None)

    # Create payload
    payload = {
        "installation": {"id": 12345},
        "repository": {
            "owner": {"login": "test-owner", "id": 123},
            "name": "test-repo",
            "id": 456,
        },
        "pull_request": {
            "merged_by": {"login": "test-user"},
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/42",
            "user": {"login": "pr-creator"},
        },
        "number": 42,
    }

    # Execute
    result = handle_pr_merged(payload)

    # Verify
    assert result is None  # Function returns None

    # Verify create_issue was called
    mock_create_issue.assert_called_once()

    # Verify repository was updated to disable merge trigger
    mock_update_repository.assert_called_once_with(
        repo_id=456, trigger_on_merged=False, updated_by="test-user"
    )

    # Verify warning notification was sent with correct message
    warning_calls = [
        call
        for call in mock_slack_notify.call_args_list
        if "Issues are disabled" in str(call) and "Disabled merge trigger" in str(call)
    ]
    assert len(warning_calls) > 0

    # Verify no success notifications were sent
    success_calls = [
        call
        for call in mock_slack_notify.call_args_list
        if "Issue created" in str(call)
    ]
    assert len(success_calls) == 0


@patch("services.webhook.merge_handler.slack_notify")
@patch("services.webhook.merge_handler.get_issue_body_for_pr_merged")
@patch("services.webhook.merge_handler.get_issue_title_for_pr_merged")
@patch("services.webhook.merge_handler.create_issue")
@patch("services.webhook.merge_handler.get_installation_access_token")
@patch("services.webhook.merge_handler.get_repository")
@patch("services.webhook.merge_handler.check_availability")
@patch("services.webhook.merge_handler.get_pull_request_files")
@patch("services.webhook.merge_handler.get_coverages")
@patch("services.webhook.merge_handler.is_excluded_from_testing")
@patch("services.webhook.merge_handler.is_type_file")
@patch("services.webhook.merge_handler.is_test_file")
@patch("services.webhook.merge_handler.is_code_file")
def test_handle_pr_merged_other_error(
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_is_excluded_from_testing,
    mock_get_coverages,
    mock_get_pr_files,
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_create_issue,
    mock_get_issue_title,
    mock_get_issue_body,
    mock_slack_notify,
):
    """Test that handle_pr_merged handles other errors (500, etc.) correctly."""
    # Setup mocks
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "src/test.py"}]
    mock_get_coverages.return_value = []
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_is_excluded_from_testing.return_value = False
    mock_get_token.return_value = "test-token"
    mock_get_issue_title.return_value = "Test Issue Title"
    mock_get_issue_body.return_value = "Test issue body content"

    # Mock create_issue to return 500 (server error)
    mock_create_issue.return_value = (500, None)

    # Create payload
    payload = {
        "installation": {"id": 12345},
        "repository": {
            "owner": {"login": "test-owner", "id": 123},
            "name": "test-repo",
            "id": 456,
        },
        "pull_request": {
            "merged_by": {"login": "test-user"},
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/42",
            "user": {"login": "pr-creator"},
        },
        "number": 42,
    }

    # Execute
    result = handle_pr_merged(payload)

    # Verify
    assert result is None  # Function returns None

    # Verify create_issue was called
    mock_create_issue.assert_called_once()

    # Verify failure notification was sent (not success)
    failure_calls = [
        call for call in mock_slack_notify.call_args_list if "Failed" in str(call)
    ]
    assert len(failure_calls) > 0

    success_calls = [
        call
        for call in mock_slack_notify.call_args_list
        if "Issue created" in str(call)
    ]
    assert len(success_calls) == 0
