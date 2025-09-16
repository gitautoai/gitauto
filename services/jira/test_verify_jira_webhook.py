# Placeholder to check file content
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from services.jira.verify_jira_webhook import verify_jira_webhook


@pytest.fixture
def mock_request():
    """Fixture to provide a mocked FastAPI Request object."""
    request = MagicMock(spec=Request)
    request.headers = {}
    request.json = AsyncMock()
    return request


@pytest.fixture
def valid_headers():
    """Fixture providing valid Atlassian Forge headers."""
    return {
        "user-agent": "node-fetch/1.0",
        "x-b3-traceid": "test-trace-id",
        "x-b3-spanid": "test-span-id",
    }


@pytest.fixture
def sample_payload():
    """Fixture providing a sample JIRA webhook payload."""
    return {
        "webhookEvent": "jira:issue_created",
        "issue": {
            "id": "12345",
            "key": "TEST-123",
            "fields": {"summary": "Test issue", "description": "Test description"},
        },
    }


@pytest.mark.asyncio
async def test_verify_jira_webhook_success(mock_request, valid_headers, sample_payload):
    """Test successful verification with valid headers and payload."""
    mock_request.headers = valid_headers
    mock_request.json.return_value = sample_payload

    result = await verify_jira_webhook(mock_request)

    assert result == sample_payload
    mock_request.json.assert_called_once()


@pytest.mark.asyncio
async def test_verify_jira_webhook_missing_user_agent(mock_request, sample_payload):
    """Test verification fails when user-agent header is missing."""
    mock_request.headers = {
        "x-b3-traceid": "test-trace-id",
        "x-b3-spanid": "test-span-id",
    }
    mock_request.json.return_value = sample_payload

    with pytest.raises(HTTPException) as exc_info:
        await verify_jira_webhook(mock_request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid request source"
    mock_request.json.assert_not_called()


@pytest.mark.asyncio
async def test_verify_jira_webhook_invalid_user_agent(mock_request, sample_payload):
    """Test verification fails when user-agent doesn't contain 'node-fetch'."""
    mock_request.headers = {
        "user-agent": "curl/7.68.0",
        "x-b3-traceid": "test-trace-id",
        "x-b3-spanid": "test-span-id",
    }
    mock_request.json.return_value = sample_payload

    with pytest.raises(HTTPException) as exc_info:
        await verify_jira_webhook(mock_request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid request source"
    mock_request.json.assert_not_called()


@pytest.mark.asyncio
async def test_verify_jira_webhook_missing_b3_traceid(mock_request, sample_payload):
    """Test verification fails when x-b3-traceid header is missing."""
    mock_request.headers = {
        "user-agent": "node-fetch/1.0",
        "x-b3-spanid": "test-span-id",
    }
    mock_request.json.return_value = sample_payload

    with pytest.raises(HTTPException) as exc_info:
        await verify_jira_webhook(mock_request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid request source"
    mock_request.json.assert_not_called()


@pytest.mark.asyncio
async def test_verify_jira_webhook_missing_b3_spanid(mock_request, sample_payload):
    """Test verification fails when x-b3-spanid header is missing."""
    mock_request.headers = {
        "user-agent": "node-fetch/1.0",
        "x-b3-traceid": "test-trace-id",
    }
    mock_request.json.return_value = sample_payload

    with pytest.raises(HTTPException) as exc_info:
        await verify_jira_webhook(mock_request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid request source"
    mock_request.json.assert_not_called()


@pytest.mark.asyncio
async def test_verify_jira_webhook_empty_b3_headers(mock_request, sample_payload):
    """Test verification fails when B3 headers are empty strings."""
    mock_request.headers = {
        "user-agent": "node-fetch/1.0",
        "x-b3-traceid": "",
        "x-b3-spanid": "",
    }
    mock_request.json.return_value = sample_payload

    with pytest.raises(HTTPException) as exc_info:
        await verify_jira_webhook(mock_request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid request source"
    mock_request.json.assert_not_called()


@pytest.mark.asyncio
async def test_verify_jira_webhook_none_b3_headers(mock_request, sample_payload):
    """Test verification fails when B3 headers are None."""
    mock_request.headers = {
        "user-agent": "node-fetch/1.0",
        "x-b3-traceid": None,
        "x-b3-spanid": None,
    }
    mock_request.json.return_value = sample_payload

    with pytest.raises(HTTPException) as exc_info:
        await verify_jira_webhook(mock_request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid request source"
    mock_request.json.assert_not_called()


@pytest.mark.asyncio
async def test_verify_jira_webhook_partial_user_agent_match(
    mock_request, valid_headers, sample_payload
):
    """Test verification succeeds when user-agent contains 'node-fetch' as substring."""
    mock_request.headers = {
        **valid_headers,
        "user-agent": "Mozilla/5.0 node-fetch/2.6.1 (+https://github.com/bitinn/node-fetch)",
    }
    mock_request.json.return_value = sample_payload

    result = await verify_jira_webhook(mock_request)

    assert result == sample_payload
    mock_request.json.assert_called_once()


@pytest.mark.asyncio
async def test_verify_jira_webhook_case_sensitive_user_agent(
    mock_request, sample_payload
):
    """Test verification fails when user-agent has wrong case."""
    mock_request.headers = {
        "user-agent": "NODE-FETCH/1.0",
        "x-b3-traceid": "test-trace-id",
        "x-b3-spanid": "test-span-id",
    }
    mock_request.json.return_value = sample_payload

    with pytest.raises(HTTPException) as exc_info:
        await verify_jira_webhook(mock_request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid request source"
    mock_request.json.assert_not_called()


@pytest.mark.asyncio
async def test_verify_jira_webhook_empty_payload(mock_request, valid_headers):
    """Test verification succeeds with empty payload."""
    mock_request.headers = valid_headers
    mock_request.json.return_value = {}

    result = await verify_jira_webhook(mock_request)

    assert result == {}
    mock_request.json.assert_called_once()


@pytest.mark.asyncio
async def test_verify_jira_webhook_complex_payload(mock_request, valid_headers):
    """Test verification succeeds with complex nested payload."""
    complex_payload = {
        "webhookEvent": "jira:issue_updated",
        "issue": {
            "id": "67890",
            "key": "PROJ-456",
            "fields": {
                "summary": "Complex issue with nested data",
                "assignee": {"accountId": "user123", "displayName": "John Doe"},
                "customfield_10001": ["value1", "value2"],
                "labels": [],
            },
        },
        "changelog": {
            "items": [
                {"field": "status", "fromString": "To Do", "toString": "In Progress"}
            ]
        },
    }

    mock_request.headers = valid_headers
    mock_request.json.return_value = complex_payload

    result = await verify_jira_webhook(mock_request)

    assert result == complex_payload
    mock_request.json.assert_called_once()


@pytest.mark.asyncio
@patch("services.jira.verify_jira_webhook.dumps")
async def test_verify_jira_webhook_headers_logging(
    mock_dumps, mock_request, valid_headers, sample_payload
):
    """Test that request headers are logged using dumps."""
    mock_request.headers = valid_headers
    mock_request.json.return_value = sample_payload
    mock_dumps.return_value = "mocked_json_output"

    result = await verify_jira_webhook(mock_request)

    assert result == sample_payload
    mock_dumps.assert_called_once_with(dict(valid_headers), indent=2)


@pytest.mark.asyncio
async def test_verify_jira_webhook_headers_get_method_calls(
    mock_request, valid_headers, sample_payload
):
    """Test that headers.get() is called with correct parameters."""
    mock_request.headers = MagicMock()
    mock_request.headers.get.side_effect = lambda key, default="": valid_headers.get(
        key, default
    )
    mock_request.json.return_value = sample_payload

    result = await verify_jira_webhook(mock_request)

    assert result == sample_payload
    mock_request.headers.get.assert_any_call("user-agent", "")
    mock_request.headers.get.assert_any_call("x-b3-traceid")
    mock_request.headers.get.assert_any_call("x-b3-spanid")


@pytest.mark.parametrize(
    "user_agent,expected_valid",
    [
        ("node-fetch", True),
        ("node-fetch/1.0", True),
        ("node-fetch/2.6.1", True),
        ("custom-agent node-fetch/1.0", True),
        ("node-fetch custom-suffix", True),
        ("curl/7.68.0", False),
        ("wget/1.20.3", False),
        ("python-requests/2.25.1", False),
        ("", False),
        ("NODE-FETCH", False),
        ("Node-Fetch", False),
    ],
)
@pytest.mark.asyncio
async def test_verify_jira_webhook_user_agent_variations(
    mock_request, sample_payload, user_agent, expected_valid
):
    """Test various user-agent values to ensure proper validation."""
    mock_request.headers = {
        "user-agent": user_agent,
        "x-b3-traceid": "test-trace-id",
        "x-b3-spanid": "test-span-id",
    }
    mock_request.json.return_value = sample_payload

    if expected_valid:
        result = await verify_jira_webhook(mock_request)
        assert result == sample_payload
        mock_request.json.assert_called_once()
    else:
        with pytest.raises(HTTPException) as exc_info:
            await verify_jira_webhook(mock_request)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid request source"
        mock_request.json.assert_not_called()


@pytest.mark.asyncio
async def test_verify_jira_webhook_json_exception(mock_request, valid_headers):
    """Test verification handles JSON parsing exceptions gracefully."""
    mock_request.headers = valid_headers
    mock_request.json.side_effect = Exception("JSON parsing failed")

    # Since the function is decorated with @handle_exceptions(raise_on_error=True),
    # it should re-raise the exception
    with pytest.raises(Exception) as exc_info:
        await verify_jira_webhook(mock_request)

    assert str(exc_info.value) == "JSON parsing failed"
    mock_request.json.assert_called_once()


@pytest.mark.asyncio
async def test_verify_jira_webhook_print_statements(
    mock_request, valid_headers, sample_payload
):
    """Test that print statements are called during execution."""
    mock_request.headers = valid_headers
    mock_request.json.return_value = sample_payload

    with patch("builtins.print") as mock_print:
        result = await verify_jira_webhook(mock_request)

        assert result == sample_payload
        # Verify that print was called for logging headers
        mock_print.assert_called_once()
        args, _ = mock_print.call_args
        assert "Request Headers:" in args[0]


@pytest.mark.asyncio
async def test_verify_jira_webhook_validation_failure_print(
    mock_request, sample_payload
):
    """Test that validation failure print statement is called."""
    mock_request.headers = {
        "user-agent": "invalid-agent",
        "x-b3-traceid": "test-trace-id",
        "x-b3-spanid": "test-span-id",
    }
    mock_request.json.return_value = sample_payload

    with patch("builtins.print") as mock_print:
        with pytest.raises(HTTPException):
            await verify_jira_webhook(mock_request)

        # Verify that both print statements were called
        assert mock_print.call_count == 2
        # First call should be for headers logging
        first_call_args, _ = mock_print.call_args_list[0]
        assert "Request Headers:" in first_call_args[0]
        # Second call should be for validation failure
        second_call_args, _ = mock_print.call_args_list[1]
        assert "Not a valid Forge request" in second_call_args[0]


@pytest.mark.asyncio
async def test_verify_jira_webhook_all_function_calls_order(
    mock_request, valid_headers, sample_payload
):
    """Test the order of function calls during successful execution."""
    mock_request.headers = valid_headers
    mock_request.json.return_value = sample_payload

    with patch("services.jira.verify_jira_webhook.dumps") as mock_dumps, patch(
        "builtins.print"
    ) as mock_print:

        mock_dumps.return_value = "mocked_headers_json"

        result = await verify_jira_webhook(mock_request)

        assert result == sample_payload

        # Verify the order of operations
        # 1. Headers are converted to dict and logged
        mock_dumps.assert_called_once_with(dict(valid_headers), indent=2)
        mock_print.assert_called_once_with("Request Headers:", "mocked_headers_json")

        # 2. Headers are accessed for validation
        assert mock_request.headers.get("user-agent", "") == "node-fetch/1.0"

        # 3. JSON payload is retrieved
        mock_request.json.assert_called_once()


@pytest.mark.asyncio
async def test_verify_jira_webhook_b3_headers_edge_cases(mock_request, sample_payload):
    """Test edge cases for B3 headers validation."""
    test_cases = [
        # Both headers missing
        {"user-agent": "node-fetch/1.0"},
        # Only one header present
        {"user-agent": "node-fetch/1.0", "x-b3-traceid": "trace123"},
        {"user-agent": "node-fetch/1.0", "x-b3-spanid": "span456"},
    ]

    for headers in test_cases:
        mock_request.headers = headers
        mock_request.json.return_value = sample_payload

        with pytest.raises(HTTPException) as exc_info:
            await verify_jira_webhook(mock_request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid request source"
        mock_request.json.assert_not_called()

        # Reset the mock for next iteration
        mock_request.json.reset_mock()


@pytest.mark.asyncio
async def test_verify_jira_webhook_b3_headers_valid_edge_cases(
    mock_request, sample_payload
):
    """Test that whitespace and zero values are considered valid B3 headers."""
    test_cases = [
        # Headers with whitespace (considered valid by current implementation)
        {"user-agent": "node-fetch/1.0", "x-b3-traceid": "  ", "x-b3-spanid": "  "},
        # Headers with zero values (considered valid by current implementation)
        {"user-agent": "node-fetch/1.0", "x-b3-traceid": "0", "x-b3-spanid": "0"},
    ]

    for headers in test_cases:
        mock_request.headers = headers
        mock_request.json.return_value = sample_payload

        # These should succeed with the current implementation
        result = await verify_jira_webhook(mock_request)

        assert result == sample_payload
        mock_request.json.assert_called_once()

        # Reset the mock for next iteration
        mock_request.json.reset_mock()


@pytest.mark.asyncio
async def test_verify_jira_webhook_user_agent_edge_cases(mock_request, sample_payload):
    """Test edge cases for user-agent validation."""
    test_cases = [
        # Empty user-agent
        {"user-agent": "", "x-b3-traceid": "trace", "x-b3-spanid": "span"},
        # Whitespace only user-agent
        {"user-agent": "   ", "x-b3-traceid": "trace", "x-b3-spanid": "span"},
        # Partial match but wrong position
        {"user-agent": "fetch-node", "x-b3-traceid": "trace", "x-b3-spanid": "span"},
    ]

    for headers in test_cases:
        mock_request.headers = headers
        mock_request.json.return_value = sample_payload

        with pytest.raises(HTTPException) as exc_info:
            await verify_jira_webhook(mock_request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid request source"
        mock_request.json.assert_not_called()

        # Reset the mock for next iteration
        mock_request.json.reset_mock()
