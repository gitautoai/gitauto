# pyright: reportUnusedVariable=false

from typing import cast
from unittest.mock import patch

import pytest

from services.github.types.github_types import InstallationPayload
from services.webhook.handle_installation_deleted_or_suspended import (
    handle_installation_deleted_or_suspended,
)


def _make_payload(action: str):
    return {
        "action": action,
        "installation": {
            "account": {"login": "test-owner", "id": 11111},
            "id": 12345,
        },
        "sender": {"login": "test-sender", "id": 67890},
    }


@patch(
    "services.webhook.handle_installation_deleted_or_suspended.get_schedulers_by_owner_id",
    return_value=[],
)
@patch("services.webhook.handle_installation_deleted_or_suspended.update_email_send")
@patch(
    "services.webhook.handle_installation_deleted_or_suspended.send_email",
    return_value={"id": "re_abc"},
)
@patch(
    "services.webhook.handle_installation_deleted_or_suspended.get_first_name",
    return_value="Test",
)
@patch(
    "services.webhook.handle_installation_deleted_or_suspended.get_user",
    return_value={"email": "u@example.com", "user_name": "Test User"},
)
@patch(
    "services.webhook.handle_installation_deleted_or_suspended.insert_email_send",
    return_value=True,
)
@patch("services.webhook.handle_installation_deleted_or_suspended.delete_installation")
@patch("services.webhook.handle_installation_deleted_or_suspended.slack_notify")
def test_deleted_sends_uninstall_email(
    mock_slack,
    mock_delete_inst,
    mock_insert_email,
    mock_get_user,
    _mock_get_first_name,
    mock_send_email,
    mock_update_email,
    _mock_get_schedulers,
):
    handle_installation_deleted_or_suspended(
        payload=cast(InstallationPayload, _make_payload("deleted")), action="deleted"
    )

    mock_slack.assert_called_once_with(
        ":skull: Installation deleted by `test-sender` for `test-owner`"
    )
    mock_delete_inst.assert_called_once_with(
        installation_id=12345, user_id=67890, user_name="test-sender"
    )
    mock_insert_email.assert_called_once_with(
        owner_id=67890, owner_name="test-sender", email_type="uninstall"
    )
    mock_get_user.assert_called_once_with(67890)
    mock_send_email.assert_called_once()
    mock_update_email.assert_called_once_with(
        owner_id=67890, email_type="uninstall", resend_email_id="re_abc"
    )


@patch(
    "services.webhook.handle_installation_deleted_or_suspended.get_schedulers_by_owner_id",
    return_value=[],
)
@patch("services.webhook.handle_installation_deleted_or_suspended.update_email_send")
@patch(
    "services.webhook.handle_installation_deleted_or_suspended.send_email",
    return_value={"id": "re_xyz"},
)
@patch(
    "services.webhook.handle_installation_deleted_or_suspended.get_first_name",
    return_value="Test",
)
@patch(
    "services.webhook.handle_installation_deleted_or_suspended.get_user",
    return_value={"email": "u@example.com", "user_name": "Test User"},
)
@patch(
    "services.webhook.handle_installation_deleted_or_suspended.insert_email_send",
    return_value=True,
)
@patch("services.webhook.handle_installation_deleted_or_suspended.delete_installation")
@patch("services.webhook.handle_installation_deleted_or_suspended.slack_notify")
def test_suspend_sends_suspend_email(
    mock_slack,
    mock_delete_inst,
    mock_insert_email,
    mock_get_user,
    _mock_get_first_name,
    mock_send_email,
    mock_update_email,
    _mock_get_schedulers,
):
    handle_installation_deleted_or_suspended(
        payload=cast(InstallationPayload, _make_payload("suspend")), action="suspend"
    )

    mock_slack.assert_called_once_with(
        ":skull: Installation suspended by `test-sender` for `test-owner`"
    )
    mock_delete_inst.assert_called_once_with(
        installation_id=12345, user_id=67890, user_name="test-sender"
    )
    mock_insert_email.assert_called_once_with(
        owner_id=67890, owner_name="test-sender", email_type="suspend"
    )
    mock_get_user.assert_called_once_with(67890)
    mock_send_email.assert_called_once()
    mock_update_email.assert_called_once_with(
        owner_id=67890, email_type="suspend", resend_email_id="re_xyz"
    )


@patch(
    "services.webhook.handle_installation_deleted_or_suspended.get_schedulers_by_owner_id",
    return_value=[],
)
@patch("services.webhook.handle_installation_deleted_or_suspended.send_email")
@patch("services.webhook.handle_installation_deleted_or_suspended.get_user")
@patch(
    "services.webhook.handle_installation_deleted_or_suspended.insert_email_send",
    return_value=False,
)
@patch("services.webhook.handle_installation_deleted_or_suspended.delete_installation")
@patch("services.webhook.handle_installation_deleted_or_suspended.slack_notify")
def test_duplicate_email_skipped(
    _mock_slack,
    _mock_delete_inst,
    _mock_insert_email,
    mock_get_user,
    mock_send_email,
    _mock_get_schedulers,
):
    handle_installation_deleted_or_suspended(
        payload=cast(InstallationPayload, _make_payload("deleted")), action="deleted"
    )

    mock_get_user.assert_not_called()
    mock_send_email.assert_not_called()


@pytest.mark.parametrize("action", ["deleted", "suspend"])
@patch("services.webhook.handle_installation_deleted_or_suspended.delete_scheduler")
@patch(
    "services.webhook.handle_installation_deleted_or_suspended.get_schedulers_by_owner_id",
    return_value=["sched-1", "sched-2"],
)
@patch(
    "services.webhook.handle_installation_deleted_or_suspended.insert_email_send",
    return_value=False,
)
@patch("services.webhook.handle_installation_deleted_or_suspended.delete_installation")
@patch("services.webhook.handle_installation_deleted_or_suspended.slack_notify")
def test_schedulers_deleted(
    _mock_slack,
    _mock_delete_inst,
    _mock_insert_email,
    mock_get_schedulers,
    mock_delete_scheduler,
    action,
):
    handle_installation_deleted_or_suspended(
        payload=cast(InstallationPayload, _make_payload(action)), action=action
    )

    mock_get_schedulers.assert_called_once_with(11111)
    assert mock_delete_scheduler.call_count == 2
