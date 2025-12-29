from unittest.mock import Mock, patch

import requests

from services.github.check_suites.get_failed_check_runs import (
    get_failed_check_runs_from_check_suite,
)


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_success_with_failures(mock_create_headers, mock_get):
    """Test successful retrieval of failed check runs"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"id": 1, "name": "test1", "conclusion": "failure"},
            {"id": 2, "name": "test2", "conclusion": "success"},
            {"id": 3, "name": "test3", "conclusion": "timed_out"},
            {"id": 4, "name": "test4", "conclusion": "startup_failure"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert len(result) == 3
    assert result[0]["conclusion"] == "failure"
    assert result[1]["conclusion"] == "timed_out"
    assert result[2]["conclusion"] == "startup_failure"
    mock_get.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/check-suites/12345/check-runs",
        headers={"Authorization": "token test-token"},
        timeout=30,
    )


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_all_successful(mock_create_headers, mock_get):
    """Test when all check runs are successful"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"id": 1, "name": "test1", "conclusion": "success"},
            {"id": 2, "name": "test2", "conclusion": "neutral"},
            {"id": 3, "name": "test3", "conclusion": "skipped"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_empty_check_runs(mock_create_headers, mock_get):
    """Test when check_runs is an empty array"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"check_runs": []}
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_no_check_runs_key(mock_create_headers, mock_get):
    """Test when response doesn't have check_runs key"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
@patch("builtins.print")
def test_get_failed_check_runs_404_not_found(
    mock_print, mock_create_headers, mock_get
):
    """Test 404 Not Found error"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result
    mock_print.assert_called_once_with(
        "Failed to get check runs for check suite 12345: Not Found"
    )


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
@patch("builtins.print")
def test_get_failed_check_runs_401_unauthorized(
    mock_print, mock_create_headers, mock_get
):
    """Test 401 Unauthorized error"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result
    mock_print.assert_called_once_with(
        "Failed to get check runs for check suite 12345: Unauthorized"
    )


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
@patch("builtins.print")
def test_get_failed_check_runs_403_forbidden(mock_print, mock_create_headers, mock_get):
    """Test 403 Forbidden error"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden - insufficient permissions"
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result
    mock_print.assert_called_once_with(
        "Failed to get check runs for check suite 12345: Forbidden - insufficient permissions"
    )


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
@patch("builtins.print")
def test_get_failed_check_runs_500_server_error(
    mock_print, mock_create_headers, mock_get
):
    """Test 500 Internal Server Error"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result
    mock_print.assert_called_once_with(
        "Failed to get check runs for check suite 12345: Internal Server Error"
    )


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_network_timeout(mock_create_headers, mock_get):
    """Test network timeout exception"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_connection_error(mock_create_headers, mock_get):
    """Test connection error exception"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_http_error(mock_create_headers, mock_get):
    """Test HTTP error exception"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_get.side_effect = requests.exceptions.HTTPError("HTTP Error occurred")

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_request_exception(mock_create_headers, mock_get):
    """Test general request exception"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_get.side_effect = requests.exceptions.RequestException("Request failed")

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_malformed_json(mock_create_headers, mock_get):
    """Test when the API response has malformed JSON"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_only_failure_conclusion(mock_create_headers, mock_get):
    """Test filtering only 'failure' conclusion"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"id": 1, "name": "test1", "conclusion": "failure"},
            {"id": 2, "name": "test2", "conclusion": "failure"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert len(result) == 2
    assert all(cr["conclusion"] == "failure" for cr in result)


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_only_timed_out_conclusion(
    mock_create_headers, mock_get
):
    """Test filtering only 'timed_out' conclusion"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"id": 1, "name": "test1", "conclusion": "timed_out"},
            {"id": 2, "name": "test2", "conclusion": "success"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert len(result) == 1
    assert result[0]["conclusion"] == "timed_out"


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_only_startup_failure_conclusion(
    mock_create_headers, mock_get
):
    """Test filtering only 'startup_failure' conclusion"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"id": 1, "name": "test1", "conclusion": "startup_failure"},
            {"id": 2, "name": "test2", "conclusion": "cancelled"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert len(result) == 1
    assert result[0]["conclusion"] == "startup_failure"


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_verify_url_construction(mock_create_headers, mock_get):
    """Test that the URL is constructed correctly with different parameters"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"check_runs": []}
    mock_get.return_value = mock_response

    get_failed_check_runs_from_check_suite(
        "test-owner", "test-repo", 99999, "test-token"
    )

    expected_url = "https://api.github.com/repos/test-owner/test-repo/check-suites/99999/check-runs"
    mock_get.assert_called_once_with(
        expected_url,
        headers={"Authorization": "token test-token"},
        timeout=30,
    )
