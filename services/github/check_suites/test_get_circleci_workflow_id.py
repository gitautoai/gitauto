import inspect
import json
import pytest
from unittest.mock import Mock, patch

import requests

from services.github.check_suites.get_circleci_workflow_id import (
    get_circleci_workflow_ids_from_check_suite,
)


# Fixtures for better mock management
@pytest.fixture
def mock_create_headers():
    """Mock create_headers function with proper lifecycle management."""
    with patch("services.github.check_suites.get_circleci_workflow_id.create_headers") as mock:
        mock.return_value = {"Authorization": "Bearer test-token"}
        yield mock


@pytest.fixture
def mock_requests_get():
    """Mock requests.get with proper lifecycle management."""
    with patch("services.github.check_suites.get_circleci_workflow_id.requests.get") as mock:
        yield mock


@pytest.fixture
def mock_logging_error():
    """Mock logging.error with proper lifecycle management."""
    with patch("services.github.check_suites.get_circleci_workflow_id.logging.error") as mock:
        yield mock


# Behavioral tests focusing on outcomes rather than implementation details
@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_success(mock_create_headers, mock_get):
    """Test successful retrieval of workflow IDs"""
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
    """Test deduplication of duplicate workflow IDs"""
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
    """Test handling of check runs without external_id"""
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
    """Test handling of invalid JSON in external_id"""
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
@patch("services.github.check_suites.get_circleci_workflow_id.logging.error")
def test_get_circleci_workflow_ids_api_error(
    mock_logging_error, mock_create_headers, mock_get
):
    """Test API error response and logging"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result

    # Verify logging was called with correct parameters
    mock_logging_error.assert_called_once_with(
        "Failed to get check runs for check suite %s: %s",
        12345,
        "Internal Server Error",
    )


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_empty_response(mock_create_headers, mock_get):
    """Test handling of empty API response"""
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

    assert not result


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
def test_get_circleci_workflow_ids_empty_workflow_id(mock_create_headers, mock_get):
    """Test when workflow-id is an empty string in external_id JSON"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"external_id": json.dumps({"workflow-id": ""})},
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

    assert not result


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
@patch("services.github.check_suites.get_circleci_workflow_id.logging.error")
def test_get_circleci_workflow_ids_401_unauthorized(
    mock_logging_error, mock_create_headers, mock_get
):
    """Test 401 Unauthorized error with logging"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result
    mock_logging_error.assert_called_once_with(
        "Failed to get check runs for check suite %s: %s", 12345, "Unauthorized"
    )


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
    assert not result


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_connection_error(mock_create_headers, mock_get):
    """Test connection error exception"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    # Simulate connection error
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    # Should return default value due to handle_exceptions decorator
    assert not result


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_malformed_response_json(
    mock_create_headers, mock_get
):
    """Test when the API response itself has malformed JSON"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )
    assert not result


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_mixed_valid_invalid_external_ids(
    mock_create_headers, mock_get
):
    """Test mix of valid and invalid external_ids"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"external_id": "invalid-json"},
            {"external_id": json.dumps({"workflow-id": "valid-id-1"})},
            {"external_id": None},
            {"external_id": json.dumps({"workflow-id": "valid-id-2"})},
            {"external_id": ""},
            {"external_id": json.dumps({"other-field": "value"})},
        ]
    }
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    # Should return empty list due to handle_exceptions catching JSON decode error
    assert not result


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_large_dataset(mock_create_headers, mock_get):
    """Test with a large number of check runs"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    # Create 100 check runs with unique workflow IDs
    check_runs = []
    expected_ids = []
    for i in range(100):
        workflow_id = f"workflow-{i:03d}"
        check_runs.append({"external_id": json.dumps({"workflow-id": workflow_id})})
        expected_ids.append(workflow_id)

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"check_runs": check_runs}
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert len(result) == 100
    assert result == expected_ids


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_special_characters_in_workflow_id(
    mock_create_headers, mock_get
):
    """Test workflow IDs with special characters"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"external_id": json.dumps({"workflow-id": "workflow-with-dashes"})},
            {"external_id": json.dumps({"workflow-id": "workflow_with_underscores"})},
            {"external_id": json.dumps({"workflow-id": "workflow.with.dots"})},
            {"external_id": json.dumps({"workflow-id": "workflow@with@symbols"})},
            {"external_id": json.dumps({"workflow-id": "workflow with spaces"})},
        ]
    }
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    expected = [
        "workflow-with-dashes",
        "workflow_with_underscores",
        "workflow.with.dots",
        "workflow@with@symbols",
        "workflow with spaces",
    ]
    assert result == expected


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_unicode_characters(mock_create_headers, mock_get):
    """Test workflow IDs with unicode characters"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"external_id": json.dumps({"workflow-id": "workflow-测试"})},
            {"external_id": json.dumps({"workflow-id": "workflow-🚀"})},
        ]
    }
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == ["workflow-测试", "workflow-🚀"]


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
@patch("services.github.check_suites.get_circleci_workflow_id.logging.error")
def test_get_circleci_workflow_ids_403_forbidden_with_logging(
    mock_logging_error, mock_create_headers, mock_get
):
    """Test 403 Forbidden error with logging verification"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden - insufficient permissions"
    mock_get.return_value = mock_response

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result
    mock_logging_error.assert_called_once_with(
        "Failed to get check runs for check suite %s: %s",
        12345,
        "Forbidden - insufficient permissions",
    )


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_http_error_exception(mock_create_headers, mock_get):
    """Test HTTP error exception handling"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    # Simulate HTTP error exception
    mock_get.side_effect = requests.exceptions.HTTPError("HTTP Error occurred")

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    # Should return default value due to handle_exceptions decorator
    assert not result


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_request_exception(mock_create_headers, mock_get):
    """Test general request exception handling"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    # Simulate general request exception
    mock_get.side_effect = requests.exceptions.RequestException("Request failed")

    result = get_circleci_workflow_ids_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    # Should return default value due to handle_exceptions decorator
    assert not result


def test_get_circleci_workflow_ids_function_signature():
    """Test that the function has the correct signature"""
    sig = inspect.signature(get_circleci_workflow_ids_from_check_suite)
    params = list(sig.parameters.keys())
    assert params == ["owner", "repo", "check_suite_id", "github_token"]


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_verify_url_construction(
    mock_create_headers, mock_get
):
    """Test that the URL is constructed correctly with different parameters"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"check_runs": []}
    mock_get.return_value = mock_response

    # Test with different owner/repo/check_suite_id combinations
    get_circleci_workflow_ids_from_check_suite(
        "test-owner", "test-repo", 99999, "test-token"
    )

    expected_url = "https://api.github.com/repos/test-owner/test-repo/check-suites/99999/check-runs"
    mock_get.assert_called_once_with(
        expected_url,
        headers={"Authorization": "token test-token"},
        timeout=30,
    )


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_verify_headers_called(mock_create_headers, mock_get):
    """Test that create_headers is called with the correct token"""
    mock_create_headers.return_value = {"Authorization": "Bearer custom-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"check_runs": []}
    mock_get.return_value = mock_response

    get_circleci_workflow_ids_from_check_suite("owner", "repo", 12345, "custom-token")

    mock_create_headers.assert_called_once_with("custom-token")
    mock_get.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/check-suites/12345/check-runs",
        headers={"Authorization": "Bearer custom-token"},
        timeout=30,
    )


@patch("services.github.check_suites.get_circleci_workflow_id.requests.get")
@patch("services.github.check_suites.get_circleci_workflow_id.create_headers")
def test_get_circleci_workflow_ids_timeout_parameter(mock_create_headers, mock_get):
    """Test that the timeout parameter is set correctly"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"check_runs": []}
    mock_get.return_value = mock_response

    get_circleci_workflow_ids_from_check_suite("owner", "repo", 12345, "test-token")

    # Verify timeout is set to 30 seconds
    _, kwargs = mock_get.call_args
    assert kwargs["timeout"] == 30
