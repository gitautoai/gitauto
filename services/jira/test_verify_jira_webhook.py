# Standard imports
import json
from unittest.mock import MagicMock, AsyncMock, patch

# Third party imports
import pytest
from fastapi import HTTPException, Request

# Local imports
from services.jira.verify_jira_webhook import verify_jira_webhook


@pytest.fixture
def mock_request():
    """Fixture to provide a mocked Request object."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {}
    mock_req.json = AsyncMock(return_value={"test": "payload"})
    return mock_req


@pytest.fixture
def valid_forge_headers():
    """Fixture providing valid Atlassian Forge headers."""
    return {
        "user-agent": "node-fetch/1.0",
        "x-b3-traceid": "abc123def456",
        "x-b3-spanid": "789xyz012"
    }


@pytest.fixture
def sample_jira_payload():
    """Fixture providing sample Jira webhook payload."""
    return {
        "issue": {
            "key": "JIRA-123",
            "fields": {
                "summary": "Test issue",
                "description": "Test description"
            }
        },
        "user": {
            "displayName": "Test User"
        }
    }


class TestVerifyJiraWebhook:
    @pytest.mark.asyncio
    async def test_verify_jira_webhook_valid_request_success(
        self, mock_request, valid_forge_headers, sample_jira_payload
    ):
        """Test successful verification of valid Atlassian Forge request."""
        # Setup
        mock_request.headers = valid_forge_headers
        mock_request.json.return_value = sample_jira_payload
        
        # Execute
        result = await verify_jira_webhook(mock_request)
        
        # Verify
        assert result == sample_jira_payload
        mock_request.json.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_missing_user_agent(self, mock_request):
        """Test rejection when user-agent header is missing."""
        # Setup
        mock_request.headers = {
            "x-b3-traceid": "abc123def456",
            "x-b3-spanid": "789xyz012"
        }
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await verify_jira_webhook(mock_request)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid request source"
        mock_request.json.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_invalid_user_agent(self, mock_request):
        """Test rejection when user-agent doesn't contain 'node-fetch'."""
        # Setup
        mock_request.headers = {
            "user-agent": "curl/7.68.0",
            "x-b3-traceid": "abc123def456",
            "x-b3-spanid": "789xyz012"
        }
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await verify_jira_webhook(mock_request)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid request source"
        mock_request.json.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_missing_b3_traceid(self, mock_request):
        """Test rejection when x-b3-traceid header is missing."""
        # Setup
        mock_request.headers = {
            "user-agent": "node-fetch/1.0",
            "x-b3-spanid": "789xyz012"
        }
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await verify_jira_webhook(mock_request)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid request source"
        mock_request.json.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_missing_b3_spanid(self, mock_request):
        """Test rejection when x-b3-spanid header is missing."""
        # Setup
        mock_request.headers = {
            "user-agent": "node-fetch/1.0",
            "x-b3-traceid": "abc123def456"
        }
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await verify_jira_webhook(mock_request)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid request source"
        mock_request.json.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_empty_b3_headers(self, mock_request):
        """Test rejection when B3 headers are empty strings."""
        # Setup
        mock_request.headers = {
            "user-agent": "node-fetch/1.0",
            "x-b3-traceid": "",
            "x-b3-spanid": ""
        }
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await verify_jira_webhook(mock_request)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid request source"
        mock_request.json.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_none_b3_headers(self, mock_request):
        """Test rejection when B3 headers are None."""
        # Setup
        mock_request.headers = {
            "user-agent": "node-fetch/1.0",
            "x-b3-traceid": None,
            "x-b3-spanid": None
        }
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await verify_jira_webhook(mock_request)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid request source"
        mock_request.json.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_user_agent_case_sensitivity(self, mock_request):
        """Test that user-agent check is case sensitive."""
        # Setup
        mock_request.headers = {
            "user-agent": "NODE-FETCH/1.0",  # Uppercase
            "x-b3-traceid": "abc123def456",
            "x-b3-spanid": "789xyz012"
        }
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await verify_jira_webhook(mock_request)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid request source"
        mock_request.json.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_user_agent_substring_match(self, mock_request):
        """Test that user-agent allows substring match for 'node-fetch'."""
        # Setup
        mock_request.headers = {
            "user-agent": "Mozilla/5.0 node-fetch/2.6.1 (+https://github.com/bitinn/node-fetch)",
            "x-b3-traceid": "abc123def456",
            "x-b3-spanid": "789xyz012"
        }
        mock_request.json.return_value = {"test": "payload"}
        
        # Execute
        result = await verify_jira_webhook(mock_request)
        
        # Verify
        assert result == {"test": "payload"}
        mock_request.json.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_empty_payload(self, mock_request, valid_forge_headers):
        """Test handling of empty JSON payload."""
        # Setup
        mock_request.headers = valid_forge_headers
        mock_request.json.return_value = {}
        
        # Execute
        result = await verify_jira_webhook(mock_request)
        
        # Verify
        assert result == {}
        mock_request.json.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_complex_payload(self, mock_request, valid_forge_headers):
        """Test handling of complex JSON payload."""
        # Setup
        complex_payload = {
            "issue": {
                "key": "PROJ-456",
                "fields": {
                    "summary": "Complex issue",
                    "description": "A very detailed description",
                    "assignee": {"displayName": "John Doe"},
                    "labels": ["bug", "urgent"],
                    "customfield_10001": "custom value"
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
        mock_request.headers = valid_forge_headers
        mock_request.json.return_value = complex_payload
        
        # Execute
        result = await verify_jira_webhook(mock_request)
        
        # Verify
        assert result == complex_payload
        mock_request.json.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.jira.verify_jira_webhook.print")
    async def test_verify_jira_webhook_prints_headers(
        self, mock_print, mock_request, valid_forge_headers
    ):
        """Test that request headers are printed for debugging."""
        # Setup
        mock_request.headers = valid_forge_headers
        mock_request.json.return_value = {"test": "payload"}
        
        # Execute
        await verify_jira_webhook(mock_request)
        
        # Verify print was called with headers
        mock_print.assert_called()
        print_calls = [call.args for call in mock_print.call_args_list]
        assert any("Request Headers:" in str(call) for call in print_calls)

    @pytest.mark.asyncio
    @patch("services.jira.verify_jira_webhook.print")
    async def test_verify_jira_webhook_prints_invalid_request_message(
        self, mock_print, mock_request
    ):
        """Test that invalid request message is printed."""
        # Setup
        mock_request.headers = {"user-agent": "invalid"}
        
        # Execute & Verify
        with pytest.raises(HTTPException):
            await verify_jira_webhook(mock_request)
        
        # Verify print was called with invalid request message
        mock_print.assert_called()
        print_calls = [call.args for call in mock_print.call_args_list]
        assert any("Not a valid Forge request" in str(call) for call in print_calls)

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_request_json_exception(self, mock_request, valid_forge_headers):
        """Test handling when request.json() raises an exception."""
        # Setup
        mock_request.headers = valid_forge_headers
        mock_request.json.side_effect = Exception("JSON parsing error")
        
        # Execute & Verify - should re-raise due to handle_exceptions(raise_on_error=True)
        with pytest.raises(Exception, match="JSON parsing error"):
            await verify_jira_webhook(mock_request)

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_request_json_decode_error(self, mock_request, valid_forge_headers):
        """Test handling when request.json() raises JSONDecodeError."""
        # Setup
        mock_request.headers = valid_forge_headers
        mock_request.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        # Execute & Verify - should re-raise due to handle_exceptions(raise_on_error=True)
        with pytest.raises(json.JSONDecodeError):
            await verify_jira_webhook(mock_request)

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_headers_get_method_called(self, mock_request, valid_forge_headers):
        """Test that headers.get() method is called with correct parameters."""
        # Setup
        mock_headers = MagicMock()
        mock_headers.get.side_effect = lambda key, default="": valid_forge_headers.get(key, default)
        mock_request.headers = mock_headers
        mock_request.json.return_value = {"test": "payload"}
        
        # Execute
        await verify_jira_webhook(mock_request)
        
        # Verify headers.get was called for the required headers
        mock_headers.get.assert_any_call("user-agent", "")
        mock_headers.get.assert_any_call("x-b3-traceid")
        mock_headers.get.assert_any_call("x-b3-spanid")

    @pytest.mark.asyncio
    async def test_verify_jira_webhook_partial_node_fetch_in_user_agent(self, mock_request):
        """Test that partial 'node-fetch' string in user-agent is accepted."""
        # Setup
        mock_request.headers = {
            "user-agent": "some-prefix-node-fetch-some-suffix",
            "x-b3-traceid": "abc123def456",
            "x-b3-spanid": "789xyz012"
        }
        mock_request.json.return_value = {"test": "payload"}
        
        # Execute
        result = await verify_jira_webhook(mock_request)
        
        # Verify
        assert result == {"test": "payload"}
        mock_request.json.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("user_agent,expected_valid", [
        ("node-fetch/1.0", True),
        ("node-fetch", True),
        ("prefix-node-fetch-suffix", True),
        ("NODE-FETCH", False),  # Case sensitive
        ("nodefetch", False),   # Must have hyphen
        ("node_fetch", False),  # Must have hyphen
        ("curl/7.68.0", False),
        ("", False),
        ("Mozilla/5.0", False),
    ])
    async def test_verify_jira_webhook_user_agent_variations(
        self, mock_request, user_agent, expected_valid
    ):
        """Test various user-agent string variations."""
        # Setup
        mock_request.headers = {
            "user-agent": user_agent,
            "x-b3-traceid": "abc123def456",
            "x-b3-spanid": "789xyz012"
        }
        mock_request.json.return_value = {"test": "payload"}
        
        if expected_valid:
            # Execute - should succeed
            result = await verify_jira_webhook(mock_request)
            assert result == {"test": "payload"}
            mock_request.json.assert_called_once()
        else:
            # Execute - should fail
            with pytest.raises(HTTPException) as exc_info:
                await verify_jira_webhook(mock_request)
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid request source"
            mock_request.json.assert_not_called()