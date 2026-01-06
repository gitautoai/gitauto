import json
from typing import cast
from unittest.mock import MagicMock, patch

from config import PRODUCT_ID, UTF8
from services.github.types.github_types import CheckSuiteCompletedPayload
from services.webhook.successful_check_suite_handler import (
    BLOCKED,
    handle_successful_check_suite,
)


def load_payload(filename: str):
    with open(f"payloads/github/check_suite/{filename}", "r", encoding=UTF8) as f:
        return json.load(f)


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
def test_handle_successful_check_suite_with_pr(
    mock_get_token, mock_get_check_suites, mock_get_required_checks
):
    payload = load_payload("completed_by_circleci.json")
    # Modify to use PRODUCT_ID branch pattern
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2-test"

    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {"app": {"name": "CircleCI Checks"}, "status": "completed"}
    ]
    mock_get_required_checks.return_value = (200, ["CircleCI Checks"])

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
        mock_select.eq.assert_called_once_with("repo_id", 1048247380)
        mock_eq1.eq.assert_called_once_with("pr_number", 2)
        mock_eq2.eq.assert_called_once_with("owner_id", 159883862)

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


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.check_commit_has_skip_ci")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_handle_successful_check_suite_no_usage_record_found(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_check_skip_ci,
    mock_get_files,
    mock_merge_pr,  # pylint: disable=unused-argument
    mock_get_check_suites,
    mock_get_required_checks,
):
    payload = load_payload("completed_failed_github_actions.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2004-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2004-test"

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {"app": {"name": "GitHub Actions"}, "status": "completed"}
    ]
    mock_get_required_checks.return_value = (200, ["GitHub Actions"])
    mock_get_pr.return_value = {"mergeable_state": "clean"}
    mock_check_skip_ci.return_value = False
    mock_get_files.return_value = []

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


@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
def test_handle_successful_check_suite_with_exception(mock_get_token):
    payload = load_payload("completed_failed_github_actions.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2004-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2004-test"

    mock_get_token.return_value = "test-token"

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


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.check_commit_has_skip_ci")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_auto_merge_success(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_check_skip_ci,
    mock_get_check_suites,
    mock_get_required_checks,
):
    payload = load_payload("completed_by_circleci.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2-test"

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "squash",
        "auto_merge_only_test_files": False,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {"app": {"name": "CircleCI Checks"}, "status": "completed"}
    ]
    mock_get_required_checks.return_value = (200, ["CircleCI Checks"])
    mock_get_pr.return_value = {"mergeable_state": "clean"}
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
            owner="gitautoai",
            repo="circle-ci-test",
            pull_number=2,
            token="test-token",
            merge_method="squash",
        )

        # Verify get_repository_features was called with owner_id and repo_id
        mock_get_repo_features.assert_called_once_with(
            owner_id=159883862, repo_id=1048247380
        )


@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_auto_merge_disabled(
    mock_get_repo_features,
    mock_get_pr,
):
    payload = load_payload("completed_failed_github_actions.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2004-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2004-test"

    mock_get_repo_features.return_value = {"auto_merge": False}
    mock_get_pr.return_value = {"mergeable_state": "clean"}

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


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.check_commit_has_skip_ci")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_auto_merge_multiple_test_files_changed(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_check_skip_ci,
    mock_get_check_suites,
    mock_get_required_checks,
):
    payload = load_payload("completed_by_circleci.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2-test"

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": True,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {"app": {"name": "CircleCI Checks"}, "status": "completed"}
    ]
    mock_get_required_checks.return_value = (200, ["CircleCI Checks"])
    mock_get_pr.return_value = {"mergeable_state": "clean"}
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

        mock_merge_pr.assert_called_once_with(
            owner="gitautoai",
            repo="circle-ci-test",
            pull_number=2,
            token="test-token",
            merge_method="merge",
        )


@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.check_commit_has_skip_ci")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_auto_merge_mixed_test_and_non_test_files(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_check_skip_ci,
    mock_create_comment,  # pylint: disable=unused-argument
):
    payload = load_payload("completed_failed_github_actions.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2004-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2004-test"

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": True,
    }
    mock_get_token.return_value = "test-token"
    mock_get_pr.return_value = {"mergeable_state": "clean"}
    mock_check_skip_ci.return_value = False
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


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.check_commit_has_skip_ci")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_auto_merge_with_non_test_files_allowed(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_check_skip_ci,
    mock_get_check_suites,
    mock_get_required_checks,
):
    payload = load_payload("completed_by_circleci.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2-test"

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": False,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {"app": {"name": "CircleCI Checks"}, "status": "completed"}
    ]
    mock_get_required_checks.return_value = (200, ["CircleCI Checks"])
    mock_get_pr.return_value = {"mergeable_state": "clean"}
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

        mock_merge_pr.assert_called_once_with(
            owner="gitautoai",
            repo="circle-ci-test",
            pull_number=2,
            token="test-token",
            merge_method="merge",
        )


@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_auto_merge_skipped_for_human_pr(
    mock_get_repo_features,
    mock_get_token,
    mock_merge_pr,
    mock_get_pr,
):
    payload = load_payload("completed_by_circleci.json")
    payload["check_suite"]["pull_requests"][0]["head"]["ref"] = "human-branch"
    payload["check_suite"]["head_branch"] = "human-branch"

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "squash",
    }
    mock_get_token.return_value = "test-token"
    mock_get_pr.return_value = {"mergeable_state": "clean"}

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


@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_auto_merge_with_blocked_state(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
):
    payload = load_payload("completed_by_circleci.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2-test"

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "squash",
        "auto_merge_only_test_files": False,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {"app": {"name": "CircleCI Checks"}, "status": "completed"}
    ]
    mock_get_required_checks.return_value = (200, ["CircleCI Checks"])
    mock_get_pr.return_value = {"mergeable_state": "blocked"}

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

        # Blocked state should prevent merge and create a comment
        mock_merge_pr.assert_not_called()
        mock_create_comment.assert_called_once()


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.check_commit_has_skip_ci")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_auto_merge_with_unstable_state(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_check_skip_ci,
    mock_get_check_suites,
    mock_get_required_checks,
):
    payload = load_payload("completed_by_circleci.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2-test"

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": False,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {"app": {"name": "CircleCI Checks"}, "status": "completed"}
    ]
    mock_get_required_checks.return_value = (200, ["CircleCI Checks"])
    mock_get_pr.return_value = {"mergeable_state": "unstable"}
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

        # Unstable state allows merge (non-required checks failing)
        mock_merge_pr.assert_called_once_with(
            owner="gitautoai",
            repo="circle-ci-test",
            pull_number=2,
            token="test-token",
            merge_method="merge",
        )


@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_auto_merge_with_unknown_state_no_comment(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
):
    payload = load_payload("completed_by_circleci.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2-test"

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": False,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {"app": {"name": "CircleCI Checks"}, "status": "completed"}
    ]
    mock_get_required_checks.return_value = (200, ["CircleCI Checks"])
    mock_get_pr.return_value = {"mergeable_state": "unknown"}

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

        # Unknown state should return early with comment
        mock_merge_pr.assert_not_called()
        mock_create_comment.assert_called_once()


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.create_empty_commit")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.check_commit_has_skip_ci")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_auto_merge_blocked_skip_ci(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_check_skip_ci,
    mock_create_comment,
    mock_create_empty_commit,
    mock_get_check_suites,
    mock_get_required_checks,
):
    payload = load_payload("completed_failed_github_actions.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2004-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2004-test"

    mock_get_repo_features.return_value = {"auto_merge": True}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {"app": {"name": "GitHub Actions"}, "status": "completed"}
    ]
    mock_get_required_checks.return_value = (200, ["GitHub Actions"])
    mock_get_pr.return_value = {"mergeable_state": "clean"}
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
            owner="gitautoai",
            repo="gitauto",
            commit_sha="f8a15e5cc8987ef16de232e6a7d6d27c62ace05b",
            token="test-token",
        )
        mock_create_comment.assert_called_once_with(
            owner="gitautoai",
            repo="gitauto",
            token="test-token",
            issue_number=2004,
            body=f"{BLOCKED}: last commit has [skip ci], triggering tests instead...",
        )
        mock_create_empty_commit.assert_called_once()
