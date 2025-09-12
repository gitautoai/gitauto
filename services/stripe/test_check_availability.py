from unittest.mock import patch

from services.stripe.check_availability import check_availability


@patch("services.stripe.check_availability.trigger_auto_reload")
@patch("services.stripe.check_availability.get_owner")
@patch("services.stripe.check_availability.get_stripe_customer_id")
@patch("services.stripe.check_availability.get_billing_type")
def test_check_availability_triggers_auto_reload_when_below_threshold(
    mock_get_billing_type,
    mock_get_stripe_customer_id,
    mock_get_owner,
    mock_trigger_auto_reload,
):
    mock_get_billing_type.return_value = "credit"
    mock_get_stripe_customer_id.return_value = None
    mock_get_owner.return_value = {
        "credit_balance_usd": 5,
        "auto_reload_enabled": True,
        "auto_reload_threshold_usd": 10,
    }

    result = check_availability(
        owner_id=123,
        owner_name="test_owner",
        repo_name="test_repo",
        installation_id=456,
        sender_name="test_sender",
    )

    assert result["can_proceed"] is True
    assert result["credit_balance_usd"] == 5
    mock_trigger_auto_reload.assert_called_once()


@patch("services.stripe.check_availability.trigger_auto_reload")
@patch("services.stripe.check_availability.get_owner")
@patch("services.stripe.check_availability.get_stripe_customer_id")
@patch("services.stripe.check_availability.get_billing_type")
def test_check_availability_no_auto_reload_when_above_threshold(
    mock_get_billing_type,
    mock_get_stripe_customer_id,
    mock_get_owner,
    mock_trigger_auto_reload,
):
    mock_get_billing_type.return_value = "credit"
    mock_get_stripe_customer_id.return_value = None
    mock_get_owner.return_value = {
        "credit_balance_usd": 15,
        "auto_reload_enabled": True,
        "auto_reload_threshold_usd": 10,
    }

    result = check_availability(
        owner_id=123,
        owner_name="test_owner",
        repo_name="test_repo",
        installation_id=456,
        sender_name="test_sender",
    )

    assert result["can_proceed"] is True
    assert result["credit_balance_usd"] == 15
    mock_trigger_auto_reload.assert_not_called()


@patch("services.stripe.check_availability.trigger_auto_reload")
@patch("services.stripe.check_availability.get_owner")
@patch("services.stripe.check_availability.get_stripe_customer_id")
@patch("services.stripe.check_availability.get_billing_type")
def test_check_availability_no_auto_reload_when_disabled(
    mock_get_billing_type,
    mock_get_stripe_customer_id,
    mock_get_owner,
    mock_trigger_auto_reload,
):
    mock_get_billing_type.return_value = "credit"
    mock_get_stripe_customer_id.return_value = None
    mock_get_owner.return_value = {
        "credit_balance_usd": 5,
        "auto_reload_enabled": False,
        "auto_reload_threshold_usd": 10,
    }

    result = check_availability(
        owner_id=123,
        owner_name="test_owner",
        repo_name="test_repo",
        installation_id=456,
        sender_name="test_sender",
    )

    assert result["can_proceed"] is True
    assert result["credit_balance_usd"] == 5
    mock_trigger_auto_reload.assert_not_called()


@patch("services.stripe.check_availability.trigger_auto_reload")
@patch("services.stripe.check_availability.get_owner")
@patch("services.stripe.check_availability.get_stripe_customer_id")
@patch("services.stripe.check_availability.get_billing_type")
def test_check_availability_no_auto_reload_when_insufficient_credits(
    mock_get_billing_type,
    mock_get_stripe_customer_id,
    mock_get_owner,
    mock_trigger_auto_reload,
):
    mock_get_billing_type.return_value = "credit"
    mock_get_stripe_customer_id.return_value = None
    mock_get_owner.return_value = {
        "credit_balance_usd": 0,
        "auto_reload_enabled": True,
        "auto_reload_threshold_usd": 10,
    }

    result = check_availability(
        owner_id=123,
        owner_name="test_owner",
        repo_name="test_repo",
        installation_id=456,
        sender_name="test_sender",
    )

    assert result["can_proceed"] is False
    assert result["credit_balance_usd"] == 0
    mock_trigger_auto_reload.assert_not_called()
