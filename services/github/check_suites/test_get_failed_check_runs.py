import inspect
from unittest.mock import Mock, patch


from services.github.check_suites.get_failed_check_runs import get_failed_check_runs_from_check_suite
import requests



@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_success(mock_create_headers, mock_get):
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
def test_get_failed_check_runs_only_failures(mock_create_headers, mock_get):
    """Test filtering only failed check runs"""
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
def test_get_failed_check_runs_no_failures(mock_create_headers, mock_get):
    """Test when there are no failed check runs"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

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

    assert not result


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
@patch("builtins.print")
def test_get_failed_check_runs_api_error_500(
    mock_print, mock_create_headers, mock_get
):
    """Test API error response (500) and print output"""
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
def test_get_failed_check_runs_404_not_found(mock_create_headers, mock_get):
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


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
@patch("builtins.print")
def test_get_failed_check_runs_401_unauthorized(
    mock_print, mock_create_headers, mock_get
):
    """Test 401 Unauthorized error with print output"""
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
def test_get_failed_check_runs_empty_response(mock_create_headers, mock_get):
    """Test handling of empty API response"""
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
def test_get_failed_check_runs_403_forbidden(
    mock_print, mock_create_headers, mock_get
):
    """Test 403 Forbidden error with print output verification"""
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
def test_get_failed_check_runs_http_error_exception(mock_create_headers, mock_get):
    """Test HTTP error exception handling"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_get.side_effect = requests.exceptions.HTTPError("HTTP Error occurred")

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_request_exception(mock_create_headers, mock_get):
    """Test general request exception handling"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_get.side_effect = requests.exceptions.RequestException("Request failed")

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_all_failure_types(mock_create_headers, mock_get):
    """Test all types of failures from GITHUB_CHECK_RUN_FAILURES"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

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
def test_get_failed_check_runs_missing_conclusion(mock_create_headers, mock_get):
    """Test handling of check runs without conclusion field"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

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
def test_get_failed_check_runs_none_conclusion(mock_create_headers, mock_get):
    """Test handling of check runs with None conclusion"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

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


def test_get_failed_check_runs_function_signature():
    """Test that the function has the correct signature"""
    sig = inspect.signature(get_failed_check_runs_from_check_suite)
    params = list(sig.parameters.keys())
    assert params == ["owner", "repo", "check_suite_id", "github_token"]


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_verify_url_construction(
    mock_create_headers, mock_get
):
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


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_verify_headers_called(mock_create_headers, mock_get):
    """Test that create_headers is called with the correct token"""
    mock_create_headers.return_value = {"Authorization": "Bearer custom-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"check_runs": []}
    mock_get.return_value = mock_response

    get_failed_check_runs_from_check_suite("owner", "repo", 12345, "custom-token")

    mock_create_headers.assert_called_once_with("custom-token")
    mock_get.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/check-suites/12345/check-runs",
        headers={"Authorization": "Bearer custom-token"},
        timeout=30,
    )


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_timeout_parameter(mock_create_headers, mock_get):
    """Test that the timeout parameter is set correctly"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"check_runs": []}
    mock_get.return_value = mock_response

    get_failed_check_runs_from_check_suite("owner", "repo", 12345, "test-token")

    _, kwargs = mock_get.call_args
    assert kwargs["timeout"] == 30


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_large_dataset(mock_create_headers, mock_get):
    """Test with a large number of check runs"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

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
def test_get_failed_check_runs_mixed_conclusions(mock_create_headers, mock_get):
    """Test with various conclusion values"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

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
def test_get_failed_check_runs_malformed_response_json(
    mock_create_headers, mock_get
):
    """Test when the API response itself has malformed JSON"""
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
def test_get_failed_check_runs_special_characters_in_owner_repo(
    mock_create_headers, mock_get
):
    """Test with special characters in owner and repo names"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "check_runs": [{"id": 1, "name": "test1", "conclusion": "failure"}]
    }
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner-with-dash", "repo_with_underscore", 12345, "test-token"
    )

    assert len(result) == 1
    expected_url = "https://api.github.com/repos/owner-with-dash/repo_with_underscore/check-suites/12345/check-runs"
    mock_get.assert_called_once_with(
        expected_url,
        headers={"Authorization": "token test-token"},
        timeout=30,
    )


@patch("services.github.check_suites.get_failed_check_runs.requests.get")
@patch("services.github.check_suites.get_failed_check_runs.create_headers")
def test_get_failed_check_runs_empty_conclusion_string(mock_create_headers, mock_get):
    """Test handling of check runs with empty string conclusion"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

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
def test_get_failed_check_runs_different_error_codes(
    mock_print, mock_create_headers, mock_get
):
    """Test different HTTP error status codes"""
    mock_create_headers.return_value = {"Authorization": "token test-token"}

    mock_response = Mock()
    mock_response.status_code = 422
    mock_response.text = "Unprocessable Entity"
    mock_get.return_value = mock_response

    result = get_failed_check_runs_from_check_suite(
        "owner", "repo", 12345, "test-token"
    )

    assert not result
    mock_print.assert_called_once_with(
        "Failed to get check runs for check suite 12345: Unprocessable Entity"
    )
