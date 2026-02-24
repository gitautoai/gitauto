from unittest.mock import MagicMock, patch

from services.supabase.email_sends.update_email_send import update_email_send


@patch("services.supabase.email_sends.update_email_send.supabase")
def test_update_email_send_sets_resend_email_id(mock_supabase):
    mock_table = MagicMock()
    mock_update = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.execute.return_value = MagicMock()

    update_email_send(
        owner_id=12345, email_type="uninstall", resend_email_id="re_abc123"
    )

    mock_supabase.table.assert_called_once_with("email_sends")
    mock_table.update.assert_called_once_with({"resend_email_id": "re_abc123"})
    mock_update.eq.assert_called_once_with("owner_id", 12345)
    mock_eq1.eq.assert_called_once_with("email_type", "uninstall")
    mock_eq2.execute.assert_called_once()


@patch("services.supabase.email_sends.update_email_send.supabase")
def test_update_email_send_exception_returns_none(mock_supabase):
    """DB errors return None without raising."""
    mock_supabase.table.side_effect = Exception("Database error")

    result = update_email_send(
        owner_id=12345, email_type="uninstall", resend_email_id="re_abc123"
    )

    assert result is None
