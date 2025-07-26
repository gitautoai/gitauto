import asyncio
from unittest.mock import patch, AsyncMock
import pytest

from services.webhook.webhook_handler import handle_webhook_event


@pytest.mark.asyncio
async def test_installation_created_simple():
    with patch("services.webhook.webhook_handler.slack_notify") as mock_slack:
        with patch("services.webhook.webhook_handler.handle_installation_created", new_callable=AsyncMock) as mock_handler:
            payload = {
                "action": "created",
                "installation": {"account": {"login": "test-owner"}},
                "sender": {"login": "test-sender"}
            }
            
            await handle_webhook_event("installation", payload)
            
            mock_handler.assert_called_once_with(payload=payload)