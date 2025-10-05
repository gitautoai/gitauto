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
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "src/test.py"}]
    mock_get_coverages.return_value = {}
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

    result = handle_pr_merged(payload)

    assert result is None

    mock_create_issue.assert_called_once()
    call_kwargs = mock_create_issue.call_args.kwargs
    assert call_kwargs["title"] == "Test Issue Title"
    assert call_kwargs["body"] == "Test issue body content"

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
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "src/test.py"}]
    mock_get_coverages.return_value = {}
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_is_excluded_from_testing.return_value = False
    mock_get_token.return_value = "test-token"
    mock_get_issue_title.return_value = "Test Issue Title"
    mock_get_issue_body.return_value = "Test issue body content"

    mock_create_issue.return_value = (410, None)

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

    result = handle_pr_merged(payload)

    assert result is None

    mock_create_issue.assert_called_once()

    mock_update_repository.assert_called_once_with(
        repo_id=456, trigger_on_merged=False, updated_by="test-user"
    )

    warning_calls = [
        call
        for call in mock_slack_notify.call_args_list
        if "Issues are disabled" in str(call) and "Disabled merge trigger" in str(call)
    ]
    assert len(warning_calls) > 0

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
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "src/test.py"}]
    mock_get_coverages.return_value = {}
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_is_excluded_from_testing.return_value = False
    mock_get_token.return_value = "test-token"
    mock_get_issue_title.return_value = "Test Issue Title"
    mock_get_issue_body.return_value = "Test issue body content"

    mock_create_issue.return_value = (500, None)

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

    result = handle_pr_merged(payload)

    assert result is None

    mock_create_issue.assert_called_once()

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


@patch("services.webhook.merge_handler.get_installation_access_token")
@patch("services.webhook.merge_handler.get_repository")
def test_handle_pr_merged_trigger_disabled(
    mock_get_repository,
    mock_get_token,
):
    """Test early return when trigger_on_merged is False."""
    mock_get_repository.return_value = {"trigger_on_merged": False}
    mock_get_token.return_value = "test-token"

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

    result = handle_pr_merged(payload)

    assert result is None
    mock_get_repository.assert_called_once_with(repo_id=456)


@patch("services.webhook.merge_handler.get_installation_access_token")
@patch("services.webhook.merge_handler.get_repository")
def test_handle_pr_merged_no_repo_settings(
    mock_get_repository,
    mock_get_token,
):
    """Test early return when repository settings are not found."""
    mock_get_repository.return_value = None
    mock_get_token.return_value = "test-token"

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

    result = handle_pr_merged(payload)

    assert result is None


@patch("services.webhook.merge_handler.slack_notify")
@patch("services.webhook.merge_handler.update_repository")
@patch("services.webhook.merge_handler.create_comment")
@patch("services.webhook.merge_handler.get_installation_access_token")
@patch("services.webhook.merge_handler.get_repository")
@patch("services.webhook.merge_handler.check_availability")
def test_handle_pr_merged_insufficient_credits(
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_create_comment,
    mock_update_repository,
    mock_slack_notify,
):
    """Test handling when owner has insufficient credits."""
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": False}
    mock_get_token.return_value = "test-token"

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

    result = handle_pr_merged(payload)

    assert result is None

    mock_create_comment.assert_called_once()
    call_kwargs = mock_create_comment.call_args.kwargs
    assert "Insufficient credits" in call_kwargs["body"]

    mock_update_repository.assert_called_once_with(
        repo_id=456, trigger_on_merged=False
    )

    slack_calls = [
        call
        for call in mock_slack_notify.call_args_list
        if "insufficient credits" in str(call)
    ]
    assert len(slack_calls) > 0


@patch("services.webhook.merge_handler.slack_notify")
@patch("services.webhook.merge_handler.get_installation_access_token")
@patch("services.webhook.merge_handler.get_repository")
@patch("services.webhook.merge_handler.check_availability")
@patch("services.webhook.merge_handler.get_pull_request_files")
@patch("services.webhook.merge_handler.get_coverages")
@patch("services.webhook.merge_handler.is_excluded_from_testing")
@patch("services.webhook.merge_handler.is_type_file")
@patch("services.webhook.merge_handler.is_test_file")
@patch("services.webhook.merge_handler.is_code_file")
def test_handle_pr_merged_no_code_files(
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_is_excluded_from_testing,
    mock_get_coverages,
    mock_get_pr_files,
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_slack_notify,
):
    """Test early return when no code files are changed."""
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "README.md"}]
    mock_get_coverages.return_value = {}
    mock_is_code_file.return_value = False
    mock_get_token.return_value = "test-token"

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

    result = handle_pr_merged(payload)

    assert result is None

    early_return_calls = [
        call
        for call in mock_slack_notify.call_args_list
        if "No code files changed" in str(call)
    ]
    assert len(early_return_calls) > 0


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
def test_handle_pr_merged_with_coverage_data(
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
    """Test handling files with complete coverage data."""
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "src/test.py"}]
    mock_get_coverages.return_value = {
        "src/test.py": {
            "line_coverage": 75.5,
            "function_coverage": 80.0,
            "branch_coverage": 60.5,
        }
    }
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

    result = handle_pr_merged(payload)

    assert result is None

    mock_get_issue_body.assert_called_once()
    call_kwargs = mock_get_issue_body.call_args.kwargs
    file_list = call_kwargs["file_list"]
    assert len(file_list) == 1
    assert "Line coverage: 75.5%" in file_list[0]
    assert "Function coverage: 80.0%" in file_list[0]
    assert "Branch coverage: 60.5%" in file_list[0]


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
def test_handle_pr_merged_with_partial_coverage_data(
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
    """Test handling files with partial coverage data (some None values)."""
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "src/test.py"}]
    mock_get_coverages.return_value = {
        "src/test.py": {
            "line_coverage": 75.5,
            "function_coverage": None,
            "branch_coverage": 60.5,
        }
    }
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

    result = handle_pr_merged(payload)

    assert result is None

    mock_get_issue_body.assert_called_once()
    call_kwargs = mock_get_issue_body.call_args.kwargs
    file_list = call_kwargs["file_list"]
    assert len(file_list) == 1
    assert "Line coverage: 75.5%" in file_list[0]
    assert "Function coverage" not in file_list[0]
    assert "Branch coverage: 60.5%" in file_list[0]


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
def test_handle_pr_merged_with_all_none_coverage_data(
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
    """Test handling files with all None coverage data."""
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "src/test.py"}]
    mock_get_coverages.return_value = {
        "src/test.py": {
            "line_coverage": None,
            "function_coverage": None,
            "branch_coverage": None,
        }
    }
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

    result = handle_pr_merged(payload)

    assert result is None

    mock_get_issue_body.assert_called_once()
    call_kwargs = mock_get_issue_body.call_args.kwargs
    file_list = call_kwargs["file_list"]
    assert len(file_list) == 1
    assert "coverage" not in file_list[0].lower() or file_list[0] == "src/test.py"


@patch("services.webhook.merge_handler.get_installation_access_token")
def test_handle_pr_merged_merged_by_none(
    mock_get_token,
):
    """Test handling when merged_by is None."""
    mock_get_token.return_value = "test-token"

    payload = {
        "installation": {"id": 12345},
        "repository": {
            "owner": {"login": "test-owner", "id": 123},
            "name": "test-repo",
            "id": 456,
        },
        "pull_request": {
            "merged_by": None,
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/42",
            "user": {"login": "pr-creator"},
        },
        "number": 42,
    }

    result = handle_pr_merged(payload)

    assert result is None


@patch("services.webhook.merge_handler.get_installation_access_token")
def test_handle_pr_merged_merged_by_missing(
    mock_get_token,
):
    """Test handling when merged_by key is missing."""
    mock_get_token.return_value = "test-token"

    payload = {
        "installation": {"id": 12345},
        "repository": {
            "owner": {"login": "test-owner", "id": 123},
            "name": "test-repo",
            "id": 456,
        },
        "pull_request": {
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/42",
            "user": {"login": "pr-creator"},
        },
        "number": 42,
    }

    result = handle_pr_merged(payload)

    assert result is None


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
@patch("services.webhook.merge_handler.PRODUCT_ID", "gitauto")
def test_handle_pr_merged_bot_creator(
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
    """Test handling when PR creator is the bot itself."""
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "src/test.py"}]
    mock_get_coverages.return_value = {}
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
            "user": {"login": "gitauto-for-dev[bot]"},
        },
        "number": 42,
    }

    result = handle_pr_merged(payload)

    assert result is None

    mock_create_issue.assert_called_once()
    call_kwargs = mock_create_issue.call_args.kwargs
    assert call_kwargs["assignees"] == []


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
def test_handle_pr_merged_multiple_files_mixed_coverage(
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
    """Test handling multiple files with mixed coverage data."""
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [
        {"filename": "src/file1.py"},
        {"filename": "src/file2.py"},
        {"filename": "src/file3.py"},
    ]
    mock_get_coverages.return_value = {
        "src/file1.py": {
            "line_coverage": 75.5,
            "function_coverage": 80.0,
            "branch_coverage": 60.5,
        },
        "src/file2.py": {
            "line_coverage": None,
            "function_coverage": 90.0,
            "branch_coverage": None,
        },
    }
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

    result = handle_pr_merged(payload)

    assert result is None

    mock_get_issue_body.assert_called_once()
    call_kwargs = mock_get_issue_body.call_args.kwargs
    file_list = call_kwargs["file_list"]
    assert len(file_list) == 3


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
def test_handle_pr_merged_create_issue_returns_none(
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
    """Test handling when create_issue returns None response."""
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "src/test.py"}]
    mock_get_coverages.return_value = {}
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_is_excluded_from_testing.return_value = False
    mock_get_token.return_value = "test-token"
    mock_get_issue_title.return_value = "Test Issue Title"
    mock_get_issue_body.return_value = "Test issue body content"
    mock_create_issue.return_value = (200, None)

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

    result = handle_pr_merged(payload)

    assert result is None

    failure_calls = [
        call for call in mock_slack_notify.call_args_list if "Failed" in str(call)
    ]
    assert len(failure_calls) > 0


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
def test_handle_pr_merged_create_issue_missing_html_url(
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
    """Test handling when create_issue response is missing html_url."""
    mock_get_repository.return_value = {"trigger_on_merged": True}
    mock_check_availability.return_value = {"can_proceed": True}
    mock_get_pr_files.return_value = [{"filename": "src/test.py"}]
    mock_get_coverages.return_value = {}
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_is_excluded_from_testing.return_value = False
    mock_get_token.return_value = "test-token"
    mock_get_issue_title.return_value = "Test Issue Title"
    mock_get_issue_body.return_value = "Test issue body content"
    mock_create_issue.return_value = (200, {"number": 1})

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

    result = handle_pr_merged(payload)

    assert result is None

    failure_calls = [
        call for call in mock_slack_notify.call_args_list if "Failed" in str(call)
    ]
    assert len(failure_calls) > 0
