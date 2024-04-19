import pytest
from services.supabase import SupabaseManager
from unittest.mock import AsyncMock, patch


@patch("services.supabase.SupabaseManager.create_installation")
@pytest.mark.asyncio
async def test_handle_installation_created(mock_create_installation):
    from services.webhook_handler import handle_installation_created

    mock_payload = {
        "installation": {
            "id": 123,
            "account": {
                "type": "User",
                "login": "testuser",
                "id": 1,
            },
        },
        "sender": {
            "id": 2,
            "login": "senderuser",
        },
    }
    await handle_installation_created(mock_payload)
    mock_create_installation.assert_called_once()

@patch("services.supabase.SupabaseManager.delete_installation")
@pytest.mark.asyncio
async def test_handle_installation_deleted(mock_delete_installation):
    from services.webhook_handler import handle_installation_deleted
    await handle_installation_deleted({"installation": {"id": 123}})
    mock_delete_installation.assert_called_once_with(123)