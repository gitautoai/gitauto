import json
import pytest
import requests
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

@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_empty_check_runs(mock_create_headers, mock_get):
    """Test when check_runs is an empty array"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"check_runs": []}
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_missing_workflow_id_in_json(
    mock_create_headers, mock_get
):
    """Test when external_id has valid JSON but no workflow-id field"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"external_id": json.dumps({"actor-id": "test-actor"})},
            {"external_id": json.dumps({"source": "notifications"})},
            {"external_id": json.dumps({"workflow-id": "valid-id"})},
        ]
    }
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == ["valid-id"]


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_none_workflow_id(mock_create_headers, mock_get):
    """Test when workflow-id is None in external_id JSON"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"external_id": json.dumps({"workflow-id": None})},
            {"external_id": json.dumps({"workflow-id": "valid-id"})},
        ]
    }
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == ["valid-id"]


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_different_error_codes(mock_create_headers, mock_get):
    """Test different HTTP error status codes"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    # Test 404 Not Found
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_401_unauthorized(mock_create_headers, mock_get):
    """Test 401 Unauthorized error"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_network_timeout(mock_create_headers, mock_get):
    """Test network timeout exception"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}
    
    # Simulate timeout exception
    mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    # Should return default value due to handle_exceptions decorator
    assert result == []


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_connection_error(mock_create_headers, mock_get):
    """Test connection error exception"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}
    
    # Simulate connection error
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

