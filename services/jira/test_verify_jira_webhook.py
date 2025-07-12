# Standard imports
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
