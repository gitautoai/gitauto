import json
from unittest.mock import Mock, patch

from services.github.check_suites.get_circleci_workflow_id import (
    get_circleci_workflow_ids_from_check_suite,
)


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_success(mock_create_headers, mock_get):
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {
                "external_id": json.dumps(
                    {"workflow-id": "abc123-456-def", "actor-id": "test-actor"}
                )
            },
            {
                "external_id": json.dumps(
                    {"workflow-id": "xyz789-012-ghi", "source": "notifications"}
                )
            },
        ]
    }
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == ["abc123-456-def", "xyz789-012-ghi"]
    mock_get.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/check-suites/12345/check-runs",
        headers={"Authorization": "token test-token"},
        timeout=30,
    )


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_duplicate_workflow_ids(
    mock_create_headers, mock_get
):
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"external_id": json.dumps({"workflow-id": "abc123-456-def"})},
            {"external_id": json.dumps({"workflow-id": "abc123-456-def"})},
        ]
    }
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == ["abc123-456-def"]


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_no_external_id(mock_create_headers, mock_get):
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [{"name": "test-run"}, {"external_id": None}, {"external_id": ""}]
    }
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_invalid_json(mock_create_headers, mock_get):
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"external_id": "invalid-json"},
            {"external_id": json.dumps({"workflow-id": "valid-workflow-id"})},
        ]
    }
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result  # Should return empty list due to handle_exceptions


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_api_error(mock_create_headers, mock_get):
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_empty_response(mock_create_headers, mock_get):
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result
