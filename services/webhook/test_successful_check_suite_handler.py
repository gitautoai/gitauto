# pylint: disable=too-many-lines,unused-argument
# pyright: reportUnusedVariable=false
import json
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from config import PRODUCT_ID, UTF8
from services.github.branches.get_required_status_checks import StatusChecksResult
from services.github.types.github_types import CheckSuiteCompletedPayload
from services.webhook.successful_check_suite_handler import (
    handle_successful_check_suite,
)


def load_payload(filename: str):
    with open(f"payloads/github/check_suite/{filename}", "r", encoding=UTF8) as f:
        return json.load(f)


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
def test_handle_successful_check_suite_with_pr(
    mock_get_token,
    mock_get_repo_features,
    mock_get_check_suites,
    mock_get_required_checks,
):
    payload = load_payload("completed_by_circleci.json")
    # Modify to use PRODUCT_ID branch pattern
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2-test"

    mock_get_token.return_value = "test-token"
    mock_get_repo_features.return_value = {"auto_merge": False}
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "CircleCI Checks"},
            "status": "completed",
            "latest_check_runs_count": 1,
        }
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], strict=True
    )

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
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_handle_successful_check_suite_no_usage_record_found(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
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
        {
            "app": {"name": "GitHub Actions", "id": 15368},
            "status": "completed",
            "latest_check_runs_count": 1,
        }
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["GitHub Actions"], app_ids={15368}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        }
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
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
            pr_number=2,
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        }
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
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
            pr_number=2,
            token="test-token",
            merge_method="merge",
        )


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.create_comment")
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
    mock_create_comment,
    mock_get_check_suites,
    mock_get_required_checks,
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
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "GitHub Actions", "id": 15368},
            "status": "completed",
            "latest_check_runs_count": 1,
        }
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["GitHub Actions"], app_ids={15368}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        }
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
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
            pr_number=2,
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


@patch("services.webhook.successful_check_suite_handler.slack_notify")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_auto_merge_blocked_skips_notification_when_checks_in_progress(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
    mock_slack_notify,
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "conclusion": "success",
            "latest_check_runs_count": 1,
        },
        {
            "app": {"name": "Cypress", "id": 99999},
            "status": "in_progress",
            "conclusion": None,
            "latest_check_runs_count": 1,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
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

        mock_merge_pr.assert_not_called()
        mock_create_comment.assert_not_called()
        mock_slack_notify.assert_not_called()


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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        }
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        }
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "unstable"}
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
            pr_number=2,
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        }
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
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


@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
def test_skip_ci_returns_early(
    mock_get_token,
    mock_get_pr,
):
    payload = load_payload("completed_failed_github_actions.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2004-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2004-test"
    payload["check_suite"]["head_commit"]["message"] = "Initial commit [skip ci]"

    mock_get_token.return_value = "test-token"

    with patch(
        "services.webhook.successful_check_suite_handler.supabase"
    ) as mock_supabase:
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table

        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))

        mock_get_pr.assert_not_called()


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_ghost_suites_skipped_and_merge_proceeds(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """Ghost suites (queued with 0 check runs) should be skipped, allowing merge."""
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
        {
            "app": {"name": "CircleCI Checks"},
            "status": "completed",
            "latest_check_runs_count": 3,
        },
        {
            "app": {"name": "GitAuto AI"},
            "status": "queued",
            "conclusion": None,
            "latest_check_runs_count": 0,
        },
        {
            "app": {"name": "Codecov"},
            "status": "queued",
            "conclusion": None,
            "latest_check_runs_count": 0,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )
    mock_get_pr.return_value = {"mergeable_state": "unstable"}
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
            pr_number=2,
            token="test-token",
            merge_method="squash",
        )


@patch("services.webhook.successful_check_suite_handler.slack_notify")
@patch("services.webhook.successful_check_suite_handler.delete_comments_by_identifiers")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_all_ghost_suites_should_not_merge(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
    _mock_delete_comments,  # pyright: ignore[reportUnusedVariable]
    _mock_slack_notify,  # pyright: ignore[reportUnusedVariable]
):
    """When all suites are ghost (queued+0 check runs), mergeable_state=unknown blocks merge."""
    payload = load_payload("completed_by_circleci.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2-test"

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "GitAuto AI"},
            "status": "queued",
            "latest_check_runs_count": 0,
        },
        {"app": {"name": "Codecov"}, "status": "queued", "latest_check_runs_count": 0},
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )
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

        mock_merge_pr.assert_not_called()
        mock_create_comment.assert_called_once()


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_real_suite_queued_should_wait(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """When a real suite is queued (has check runs, will run), should wait."""
    payload = load_payload("completed_by_circleci.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2-test"

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "CircleCI Checks"},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
        {
            "app": {"name": "GitHub Actions"},
            "status": "queued",
            "latest_check_runs_count": 2,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )

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
        mock_get_pr.assert_not_called()


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_in_progress_no_required_checks_should_wait(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """When suite is in_progress and no required checks, should wait for all to complete."""
    payload = load_payload("completed_by_circleci.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2-test"

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "CircleCI Checks"},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
        {
            "app": {"name": "GitHub Actions"},
            "status": "in_progress",
            "latest_check_runs_count": 3,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )

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
        mock_get_pr.assert_not_called()


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_required_check_in_progress_should_wait(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """When the suite containing a required check is still in progress, should return."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
        {
            "app": {"name": "GitHub Actions", "id": 15368},
            "status": "in_progress",
            "latest_check_runs_count": 3,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["build"], app_ids={15368}, strict=True
    )

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_not_called()
        mock_get_pr.assert_not_called()


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_required_completed_non_required_in_progress_should_merge(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """When required checks completed but non-required in progress, should merge if mergeable."""
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
        {
            "app": {"name": "Cypress", "id": 99999},
            "status": "in_progress",
            "latest_check_runs_count": 2,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "unstable"}
    mock_get_files.return_value = []

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
            pr_number=2,
            token="test-token",
            merge_method="squash",
        )


# --- #6: All ghost suites with required checks configured → falls through → merge ---


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_all_ghost_with_required_checks_falls_through_to_merge(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """All suites ghost + required checks configured → no active suites → falls through → merge."""
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
        {
            "app": {"name": "GitAuto AI"},
            "status": "queued",
            "latest_check_runs_count": 0,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
    mock_get_files.return_value = []

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
            pr_number=2,
            token="test-token",
            merge_method="merge",
        )


# --- #8: Required check is queued (real, will run) → wait ---


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_required_check_queued_should_wait(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """Suite containing required check is queued → should return."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
        {
            "app": {"name": "GitHub Actions", "id": 15368},
            "status": "queued",
            "latest_check_runs_count": 2,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["build"], app_ids={15368}, strict=True
    )

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_not_called()
        mock_get_pr.assert_not_called()


# --- #14: Can't read branch protection (403) → wait for all → merge ---


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_cant_read_protection_waits_for_all_then_merges(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """403 on branch protection (checks=None) → waits for all active suites → merges."""
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
        {
            "app": {"name": "CircleCI Checks"},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=403, checks=None, strict=False
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
    mock_get_files.return_value = []

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
            pr_number=2,
            token="test-token",
            merge_method="merge",
        )


# --- #18: mergeable_state=has_hooks → proceed to merge ---


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_mergeable_state_has_hooks_merges(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """mergeable_state=has_hooks is allowed → should merge."""
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "has_hooks"}
    mock_get_files.return_value = []

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
            pr_number=2,
            token="test-token",
            merge_method="merge",
        )


# --- #19: blocked + mergeable=False → notify conflicts ---


@patch("services.webhook.successful_check_suite_handler.slack_notify")
@patch("services.webhook.successful_check_suite_handler.delete_comments_by_identifiers")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_blocked_with_merge_conflicts_notifies(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
    _mock_delete_comments,  # pyright: ignore[reportUnusedVariable]
    _mock_slack_notify,  # pyright: ignore[reportUnusedVariable]
):
    """blocked + mergeable=False → still blocked (branch protection) → notify."""
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "blocked", "mergeable": False}

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
        mock_create_comment.assert_called_once()
        comment_body = mock_create_comment.call_args[1]["body"]
        assert "blocked" in comment_body


# --- #22: mergeable_state=behind → notify ---


@patch("services.webhook.successful_check_suite_handler.slack_notify")
@patch("services.webhook.successful_check_suite_handler.delete_comments_by_identifiers")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_mergeable_state_behind_notifies(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
    _mock_delete_comments,  # pyright: ignore[reportUnusedVariable]
    _mock_slack_notify,  # pyright: ignore[reportUnusedVariable]
):
    """mergeable_state=behind → PR branch behind base → notify."""
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "behind"}

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
        mock_create_comment.assert_called_once()
        comment_body = mock_create_comment.call_args[1]["body"]
        assert "behind" in comment_body


# --- #23: mergeable_state=dirty → notify ---


@patch("services.webhook.successful_check_suite_handler.slack_notify")
@patch("services.webhook.successful_check_suite_handler.delete_comments_by_identifiers")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_mergeable_state_dirty_notifies(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
    _mock_delete_comments,  # pyright: ignore[reportUnusedVariable]
    _mock_slack_notify,  # pyright: ignore[reportUnusedVariable]
):
    """mergeable_state=dirty → merge conflicts → notify."""
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "dirty"}

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
        mock_create_comment.assert_called_once()
        comment_body = mock_create_comment.call_args[1]["body"]
        assert "merge conflicts" in comment_body


# --- #24: mergeable_state=draft → notify ---


@patch("services.webhook.successful_check_suite_handler.slack_notify")
@patch("services.webhook.successful_check_suite_handler.delete_comments_by_identifiers")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_mergeable_state_draft_notifies(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
    _mock_delete_comments,  # pyright: ignore[reportUnusedVariable]
    _mock_slack_notify,  # pyright: ignore[reportUnusedVariable]
):
    """mergeable_state=draft → PR is draft → notify."""
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "draft"}

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
        mock_create_comment.assert_called_once()
        comment_body = mock_create_comment.call_args[1]["body"]
        assert "draft" in comment_body


# --- Merge returns 405 → notify ---


@patch("services.webhook.successful_check_suite_handler.slack_notify")
@patch("services.webhook.successful_check_suite_handler.delete_comments_by_identifiers")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_merge_returns_405_notifies(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
    _mock_delete_comments,  # pyright: ignore[reportUnusedVariable]
    _mock_slack_notify,  # pyright: ignore[reportUnusedVariable]
):
    """merge_pull_request returns 405 → blocked by branch protection → notify."""
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
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
    mock_get_files.return_value = []
    mock_merge_pr.return_value = {
        "code": 405,
        "message": "Required status check is expected",
    }

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
        mock_create_comment.assert_called_once()
        comment_body = mock_create_comment.call_args[1]["body"]
        assert "branch protection" in comment_body


# --- Ghost suites + mergeable states that allow merge (#6, #7) ---

GHOST_SUITES = [
    {"app": {"name": "GitAuto AI"}, "status": "queued", "latest_check_runs_count": 0},
]


def _supabase_mock():
    """Return a patch context manager and table mock for supabase usage queries."""
    ctx = patch("services.webhook.successful_check_suite_handler.supabase")
    return ctx


def _setup_supabase(mock_supabase):
    """Wire up the supabase mock chain used by every test."""
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


def _gitauto_payload():
    """Load CircleCI payload and set GitAuto branch."""
    payload = load_payload("completed_by_circleci.json")
    payload["check_suite"]["pull_requests"][0]["head"][
        "ref"
    ] = f"{PRODUCT_ID}/issue-2-test"
    payload["check_suite"]["head_branch"] = f"{PRODUCT_ID}/issue-2-test"
    return payload


@pytest.mark.parametrize("mergeable_state", ["unstable", "has_hooks"])
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_ghost_suites_mergeable_state_merges(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mergeable_state,
):
    """Ghost suites + unstable/has_hooks → merge."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": False,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = list(GHOST_SUITES)
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )
    mock_get_pr.return_value = {"mergeable_state": mergeable_state}
    mock_get_files.return_value = []

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_called_once()


# --- Ghost suites + non-mergeable states (#8, #10, #11, #12) ---


@pytest.mark.parametrize(
    "mergeable_state,expected_substr",
    [
        ("blocked", "blocked"),
        ("behind", "behind"),
        ("dirty", "merge conflicts"),
        ("draft", "draft"),
    ],
)
@patch("services.webhook.successful_check_suite_handler.slack_notify")
@patch("services.webhook.successful_check_suite_handler.delete_comments_by_identifiers")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_ghost_suites_non_mergeable_notifies(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
    _mock_delete_comments,  # pyright: ignore[reportUnusedVariable]
    _mock_slack_notify,  # pyright: ignore[reportUnusedVariable]
    mergeable_state,
    expected_substr,
):
    """Ghost suites + blocked/behind/dirty/draft → notify."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = list(GHOST_SUITES)
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )
    mock_get_pr.return_value = {"mergeable_state": mergeable_state}

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_not_called()
        mock_create_comment.assert_called_once()
        comment_body = mock_create_comment.call_args[1]["body"]
        assert expected_substr in comment_body


# --- Ghost + clean + only_test_files=true, all test files (#3) ---


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_ghost_suites_only_test_files_merges(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """Ghost suites + clean + only_test_files=true + all test files → merge."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": True,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = list(GHOST_SUITES)
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
    mock_get_files.return_value = [{"filename": "test_foo.py", "status": "modified"}]
    mock_is_test_file.return_value = True

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_called_once()


# --- Ghost + clean + only_test_files=true, has non-test files (#4) ---


@patch("services.webhook.successful_check_suite_handler.slack_notify")
@patch("services.webhook.successful_check_suite_handler.delete_comments_by_identifiers")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_ghost_suites_nontest_files_blocked(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
    _mock_delete_comments,  # pyright: ignore[reportUnusedVariable]
    _mock_slack_notify,  # pyright: ignore[reportUnusedVariable]
):
    """Ghost suites + clean + only_test_files=true + has non-test → blocked."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": True,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = list(GHOST_SUITES)
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
    mock_get_files.return_value = [
        {"filename": "test_foo.py", "status": "modified"},
        {"filename": "src/main.py", "status": "modified"},
    ]
    mock_is_test_file.side_effect = lambda f: f == "test_foo.py"

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_not_called()
        mock_create_comment.assert_called_once()
        comment_body = mock_create_comment.call_args[1]["body"]
        assert "non-test files" in comment_body


# --- Ghost + clean + merge returns 405 (#5) ---


@patch("services.webhook.successful_check_suite_handler.slack_notify")
@patch("services.webhook.successful_check_suite_handler.delete_comments_by_identifiers")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_ghost_suites_merge_405_notifies(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
    _mock_delete_comments,  # pyright: ignore[reportUnusedVariable]
    _mock_slack_notify,  # pyright: ignore[reportUnusedVariable]
):
    """Ghost suites + clean + merge returns 405 → notify."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": False,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = list(GHOST_SUITES)
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
    mock_get_files.return_value = []
    mock_merge_pr.return_value = {"code": 405, "message": "Required status check"}

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_called_once()
        mock_create_comment.assert_called_once()
        comment_body = mock_create_comment.call_args[1]["body"]
        assert "branch protection" in comment_body


# --- Queued + can't read protection (403) → wait (#15) ---


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_queued_cant_read_protection_waits(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """Real queued suite + can't read protection (403) → wait for all."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "GitHub Actions"},
            "status": "queued",
            "latest_check_runs_count": 2,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=403, checks=None, strict=False
    )

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_not_called()
        mock_get_pr.assert_not_called()


# --- Queued non-required + required done → merge (#17) ---


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_queued_non_required_with_required_done_merges(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """Required check completed + non-required queued → merge."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "merge",
        "auto_merge_only_test_files": False,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
        {
            "app": {"name": "GitHub Actions", "id": 15368},
            "status": "queued",
            "latest_check_runs_count": 2,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["CircleCI Checks"], app_ids={18001}, strict=True
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
    mock_get_files.return_value = []

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_called_once()


# --- In progress + can't read protection (403) → wait (#19) ---


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_in_progress_cant_read_protection_waits(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """In-progress suite + can't read protection (403) → wait for all."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "GitHub Actions"},
            "status": "in_progress",
            "latest_check_runs_count": 3,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=403, checks=None, strict=False
    )

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_not_called()
        mock_get_pr.assert_not_called()


# --- Mix completed+running + no required → wait (#36) ---


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_mix_completed_running_no_required_waits(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """Mix of completed + in_progress suites, no required checks → wait for all."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "CircleCI Checks"},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
        {
            "app": {"name": "GitHub Actions"},
            "status": "in_progress",
            "latest_check_runs_count": 3,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_not_called()
        mock_get_pr.assert_not_called()


# --- Bug: app name vs check run context mismatch ---


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_website_repo_required_check_context_vs_app_name(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """Website repo: no branch protection (404). GitHub Actions in_progress.
    Should return because no required checks configured → waits for all suites."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "squash"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "GitHub Actions", "id": 15368},
            "status": "in_progress",
            "latest_check_runs_count": 3,
        },
        {
            "app": {"name": "GitAuto AI", "id": 844909},
            "status": "queued",
            "latest_check_runs_count": 0,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_not_called()


@patch("services.webhook.successful_check_suite_handler.slack_notify")
@patch("services.webhook.successful_check_suite_handler.delete_comments_by_identifiers")
@patch("services.webhook.successful_check_suite_handler.create_comment")
@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_website_repo_non_test_files_blocked(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
    mock_create_comment,
    _mock_delete_comments,  # pyright: ignore[reportUnusedVariable]
    _mock_slack_notify,  # pyright: ignore[reportUnusedVariable]
):
    """Website repo: no branch protection (404), all suites completed,
    auto_merge_only_test_files=True, PR changes both impl and test files
    → blocked. Real example: https://github.com/gitautoai/website/pull/810"""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "squash",
        "auto_merge_only_test_files": True,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "GitHub Actions", "id": 15368},
            "status": "completed",
            "latest_check_runs_count": 3,
        },
        {
            "app": {"name": "GitAuto AI", "id": 844909},
            "status": "queued",
            "latest_check_runs_count": 0,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
    mock_get_files.return_value = [
        {"filename": "utils/format-date-time.test.ts", "status": "added"},
        {"filename": "utils/format-date-time.ts", "status": "modified"},
    ]
    mock_is_test_file.side_effect = lambda f: f == "utils/format-date-time.test.ts"

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_not_called()
        mock_create_comment.assert_called_once()
        comment_body = mock_create_comment.call_args[1]["body"]
        assert "non-test files" in comment_body


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_website_repo_only_test_file_merges(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """Website repo: no branch protection (404), all suites completed,
    auto_merge_only_test_files=True, PR changes only a test file
    → merges. Real example: https://github.com/gitautoai/website/pull/809"""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "squash",
        "auto_merge_only_test_files": True,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "GitHub Actions", "id": 15368},
            "status": "completed",
            "latest_check_runs_count": 3,
        },
        {
            "app": {"name": "GitAuto AI", "id": 844909},
            "status": "queued",
            "latest_check_runs_count": 0,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
    mock_get_files.return_value = [
        {"filename": "app/solution/jsonld.test.ts", "status": "added"},
    ]
    mock_is_test_file.return_value = True

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_called_once()


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request_files")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
@patch("services.webhook.successful_check_suite_handler.is_test_file")
def test_website_repo_test_and_integration_test_merges(
    mock_is_test_file,
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_get_files,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """Website repo: no branch protection (404), all suites completed,
    auto_merge_only_test_files=True, PR changes unit test + integration test
    → merges. Real example: https://github.com/gitautoai/website/pull/811"""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {
        "auto_merge": True,
        "merge_method": "squash",
        "auto_merge_only_test_files": True,
    }
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "GitHub Actions", "id": 15368},
            "status": "completed",
            "latest_check_runs_count": 3,
        },
        {
            "app": {"name": "GitAuto AI", "id": 844909},
            "status": "queued",
            "latest_check_runs_count": 0,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=404, checks=[], strict=False
    )
    mock_get_pr.return_value = {"mergeable_state": "clean"}
    mock_get_files.return_value = [
        {
            "filename": "app/actions/stripe/get-owner-ids-with-active-subscription.test.ts",
            "status": "added",
        },
        {
            "filename": "app/actions/stripe/get-owner-ids-with-active-subscription.integration.test.ts",
            "status": "added",
        },
    ]
    mock_is_test_file.return_value = True

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_called_once()


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_fox_repo_required_check_context_vs_app_name(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """Foxquilt repo: required check context is 'build_deploy_development_workflow'
    (app_id=18001) but suite app name is 'CircleCI Checks'. Should return because
    the suite is in_progress."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "in_progress",
            "latest_check_runs_count": 1,
        },
        {
            "app": {"name": "GitAuto AI", "id": 844909},
            "status": "queued",
            "latest_check_runs_count": 0,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200,
        checks=["build_deploy_development_workflow"],
        app_ids={18001},
        strict=True,
    )

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_not_called()


# --- Mix completed+running + can't read protection → wait (#37) ---


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_mix_completed_running_cant_read_waits(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """Mix of completed + in_progress suites, can't read protection (403) → wait."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "CircleCI Checks"},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
        {
            "app": {"name": "GitHub Actions"},
            "status": "in_progress",
            "latest_check_runs_count": 3,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=403, checks=None, strict=False
    )

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_not_called()
        mock_get_pr.assert_not_called()


# --- Mix completed+running + required not done → wait (#38) ---


@patch("services.webhook.successful_check_suite_handler.get_required_status_checks")
@patch("services.webhook.successful_check_suite_handler.get_check_suites")
@patch("services.webhook.successful_check_suite_handler.merge_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_pull_request")
@patch("services.webhook.successful_check_suite_handler.get_installation_access_token")
@patch("services.webhook.successful_check_suite_handler.get_repository_features")
def test_mix_completed_running_required_not_done_waits(
    mock_get_repo_features,
    mock_get_token,
    mock_get_pr,
    mock_merge_pr,
    mock_get_check_suites,
    mock_get_required_checks,
):
    """Mix of completed + in_progress, suite with required check is in_progress → return."""
    payload = _gitauto_payload()

    mock_get_repo_features.return_value = {"auto_merge": True, "merge_method": "merge"}
    mock_get_token.return_value = "test-token"
    mock_get_check_suites.return_value = [
        {
            "app": {"name": "CircleCI Checks", "id": 18001},
            "status": "completed",
            "latest_check_runs_count": 1,
        },
        {
            "app": {"name": "GitHub Actions", "id": 15368},
            "status": "in_progress",
            "latest_check_runs_count": 3,
        },
    ]
    mock_get_required_checks.return_value = StatusChecksResult(
        status_code=200, checks=["build"], app_ids={15368}, strict=True
    )

    with _supabase_mock() as mock_supabase:
        _setup_supabase(mock_supabase)
        handle_successful_check_suite(cast(CheckSuiteCompletedPayload, payload))
        mock_merge_pr.assert_not_called()
        mock_get_pr.assert_not_called()
