from unittest.mock import patch

from services.stripe.get_billing_type import get_billing_type


@patch(
    "services.stripe.get_billing_type.EXCEPTION_OWNERS",
    ["exception_owner", "test_owner"],
)
def test_get_billing_type_returns_exception_for_exception_owner():
    result = get_billing_type(owner_name="exception_owner")
    assert result == "exception"

    result = get_billing_type(owner_name="test_owner")
    assert result == "exception"


def test_get_billing_type_returns_credit_for_regular_owner():
    result = get_billing_type(owner_name="regular_owner")
    assert result == "credit"


@patch("services.stripe.get_billing_type.EXCEPTION_OWNERS", ["exception_owner"])
def test_get_billing_type_exception_owner_takes_precedence():
    result = get_billing_type(owner_name="exception_owner")
    assert result == "exception"


@patch("services.stripe.get_billing_type.EXCEPTION_OWNERS")
def test_get_billing_type_handles_exceptions_gracefully(mock_exception_owners):
    mock_exception_owners.__contains__.side_effect = Exception("Test exception")

    result = get_billing_type(owner_name="any_owner")

    assert result == "credit"


def test_get_billing_type_function_signature():
    assert get_billing_type.__name__ == "get_billing_type"
    assert callable(get_billing_type)


@patch("services.stripe.get_billing_type.EXCEPTION_OWNERS", [])
def test_get_billing_type_with_empty_exception_owners():
    result = get_billing_type(owner_name="any_owner")
    assert result == "credit"
