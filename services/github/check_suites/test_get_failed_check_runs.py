from unittest.mock import Mock, patch

import requests
from services.github.check_suites.get_failed_check_runs import (
    get_failed_check_runs_from_check_suite,
)


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_returns_failed_check_runs_when_mixed_outcomes(mock_create_headers, mock_get):
    """Returns only failed check runs when suite includes failed and non-failed runs"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

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


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_returns_all_when_only_failures(mock_create_headers, mock_get):
    """Returns all check runs when all are failures"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

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
def test_returns_empty_when_no_failures(mock_create_headers, mock_get):
    """Returns empty list when there are no failed check runs"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"id": 1, "name": "test1", "conclusion": "success"},
            {"id": 2, "name": "test2", "conclusion": "skipped"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
@patch("builtins.print")
def test_returns_empty_when_api_error(mock_print, mock_create_headers, mock_get):
    """Returns empty list when API returns error status code"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []
    mock_print.assert_called_once()


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_returns_empty_when_not_found(mock_create_headers, mock_get):
    """Returns empty list when check suite is not found"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
@patch("builtins.print")
def test_returns_empty_when_unauthorized(mock_print, mock_create_headers, mock_get):
    """Returns empty list when authentication fails"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []
    mock_print.assert_called_once()


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_returns_empty_when_response_has_no_check_runs_key(
    mock_create_headers, mock_get
):
    """Returns empty list when API response doesn't contain check_runs key"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
@patch("builtins.print")
def test_returns_empty_when_forbidden(mock_print, mock_create_headers, mock_get):
    """Returns empty list when access is forbidden"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden - insufficient permissions"
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []
    mock_print.assert_called_once()


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_returns_empty_when_check_runs_array_is_empty(mock_create_headers, mock_get):
    """Returns empty list when check_runs array is empty"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"check_runs": []}
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_returns_empty_when_network_timeout(mock_create_headers, mock_get):
    """Returns empty list when network request times out"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_returns_empty_when_connection_error(mock_create_headers, mock_get):
    """Returns empty list when connection fails"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_returns_empty_when_http_error(mock_create_headers, mock_get):
    """Returns empty list when HTTP error occurs"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_get.side_effect = requests.exceptions.HTTPError("HTTP Error occurred")

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_returns_empty_when_request_exception(mock_create_headers, mock_get):
    """Returns empty list when general request exception occurs"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_get.side_effect = requests.exceptions.RequestException("Request failed")

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_returns_all_failure_types(mock_create_headers, mock_get):
    """Returns all types of failures including startup_failure, failure, and timed_out"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"id": 1, "name": "test1", "conclusion": "startup_failure"},
            {"id": 2, "name": "test2", "conclusion": "failure"},
            {"id": 3, "name": "test3", "conclusion": "timed_out"},
            {"id": 4, "name": "test4", "conclusion": "success"},
            {"id": 5, "name": "test5", "conclusion": "neutral"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert len(result) == 3
    conclusions = [cr["conclusion"] for cr in result]
    assert "startup_failure" in conclusions
    assert "failure" in conclusions
    assert "timed_out" in conclusions
    assert "success" not in conclusions
    assert "neutral" not in conclusions


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_skips_check_runs_without_conclusion(mock_create_headers, mock_get):
    """Skips check runs that don't have a conclusion field"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"id": 1, "name": "test1"},
            {"id": 2, "name": "test2", "conclusion": "failure"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert len(result) == 1
    assert result[0]["conclusion"] == "failure"


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_skips_check_runs_with_none_conclusion(mock_create_headers, mock_get):
    """Skips check runs with None as conclusion value"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"id": 1, "name": "test1", "conclusion": None},
            {"id": 2, "name": "test2", "conclusion": "failure"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert len(result) == 1
    assert result[0]["conclusion"] == "failure"


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_handles_large_number_of_check_runs(mock_create_headers, mock_get):
    """Correctly filters large number of check runs"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    check_runs = []
    for i in range(100):
        conclusion = "failure" if i % 2 == 0 else "success"
        check_runs.append({"id": i, "name": f"test-{i}", "conclusion": conclusion})

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"check_runs": check_runs}
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert len(result) == 50
    assert all(cr["conclusion"] == "failure" for cr in result)


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_filters_various_conclusion_values(mock_create_headers, mock_get):
    """Correctly filters check runs with various conclusion values"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"id": 1, "name": "test1", "conclusion": "failure"},
            {"id": 2, "name": "test2", "conclusion": "success"},
            {"id": 3, "name": "test3", "conclusion": "timed_out"},
            {"id": 4, "name": "test4", "conclusion": "cancelled"},
            {"id": 5, "name": "test5", "conclusion": "startup_failure"},
            {"id": 6, "name": "test6", "conclusion": "neutral"},
            {"id": 7, "name": "test7", "conclusion": "skipped"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert len(result) == 3
    conclusions = [cr["conclusion"] for cr in result]
    assert "failure" in conclusions
    assert "timed_out" in conclusions
    assert "startup_failure" in conclusions


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_returns_empty_when_json_parsing_fails(mock_create_headers, mock_get):
    """Returns empty list when API response has malformed JSON"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_skips_check_runs_with_empty_string_conclusion(mock_create_headers, mock_get):
    """Skips check runs with empty string as conclusion"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"id": 1, "name": "test1", "conclusion": ""},
            {"id": 2, "name": "test2", "conclusion": "failure"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert len(result) == 1
    assert result[0]["conclusion"] == "failure"


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
@patch("builtins.print")
def test_returns_empty_when_unprocessable_entity(
    mock_print, mock_create_headers, mock_get
):
    """Returns empty list when API returns 422 Unprocessable Entity"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 422
    mock_response.text = "Unprocessable Entity"
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert result == []
    mock_print.assert_called_once()


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_preserves_order_of_failed_check_runs(mock_create_headers, mock_get):
    """Preserves original order of failed check runs in result"""
    mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [
            {"id": 3, "name": "test3", "conclusion": "timed_out"},
            {"id": 1, "name": "test1", "conclusion": "failure"},
            {"id": 2, "name": "test2", "conclusion": "success"},
            {"id": 4, "name": "test4", "conclusion": "startup_failure"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert len(result) == 3
    assert result[0]["id"] == 3
    assert result[1]["id"] == 1
    assert result[2]["id"] == 4
