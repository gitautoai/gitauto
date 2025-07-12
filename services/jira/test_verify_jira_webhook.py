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
            "fields": {
                "summary": "Test issue",
                "description": "Test description"
            }
        }
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
async def test_verify_jira_webhook_partial_user_agent_match(mock_request, valid_headers, sample_payload):
    """Test verification succeeds when user-agent contains 'node-fetch' as substring."""
    mock_request.headers = {
        **valid_headers,
        "user-agent": "Mozilla/5.0 node-fetch/2.6.1 (+https://github.com/bitinn/node-fetch)"
    }
    mock_request.json.return_value = sample_payload
    
    result = await verify_jira_webhook(mock_request)
    
    assert result == sample_payload
    mock_request.json.assert_called_once()


@pytest.mark.asyncio
async def test_verify_jira_webhook_case_sensitive_user_agent(mock_request, sample_payload):
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
                "assignee": {
                    "accountId": "user123",
                    "displayName": "John Doe"
                },
                "customfield_10001": ["value1", "value2"],
                "labels": []
            }
        },
        "changelog": {
            "items": [
                {
                    "field": "status",
                    "fromString": "To Do",
                    "toString": "In Progress"
                }
            ]
        }
    }
    
    mock_request.headers = valid_headers
    mock_request.json.return_value = complex_payload
    
    result = await verify_jira_webhook(mock_request)
    
    assert result == complex_payload
    mock_request.json.assert_called_once()


@pytest.mark.asyncio
@patch('services.jira.verify_jira_webhook.dumps')
async def test_verify_jira_webhook_headers_logging(mock_dumps, mock_request, valid_headers, sample_payload):
    """Test that request headers are logged using dumps."""
    mock_request.headers = valid_headers
    mock_request.json.return_value = sample_payload
    mock_dumps.return_value = "mocked_json_output"
    
    result = await verify_jira_webhook(mock_request)
    
    assert result == sample_payload
    mock_dumps.assert_called_once_with(dict(valid_headers), indent=2)


@pytest.mark.asyncio
async def test_verify_jira_webhook_headers_get_method_calls(mock_request, valid_headers, sample_payload):
    """Test that headers.get() is called with correct parameters."""
    mock_request.headers = MagicMock()
    mock_request.headers.get.side_effect = lambda key, default="": valid_headers.get(key, default)
    mock_request.json.return_value = sample_payload
    
    result = await verify_jira_webhook(mock_request)
    
    assert result == sample_payload
    mock_request.headers.get.assert_any_call("user-agent", "")
    mock_request.headers.get.assert_any_call("x-b3-traceid")
    mock_request.headers.get.assert_any_call("x-b3-spanid")


@pytest.mark.parametrize("user_agent,expected_valid", [
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
])
@pytest.mark.asyncio
async def test_verify_jira_webhook_user_agent_variations(mock_request, sample_payload, user_agent, expected_valid):
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
