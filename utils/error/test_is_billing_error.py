from utils.error.is_billing_error import is_billing_error


def test_detects_credit_balance_error():
    err = Exception(
        "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', "
        "'message': 'Your credit balance is too low to access the Anthropic API.'}}"
    )
    assert is_billing_error(err) is True


def test_ignores_unrelated_error():
    err = Exception("Connection refused")
    assert is_billing_error(err) is False


def test_ignores_server_error():
    err = Exception("Internal server error")
    assert is_billing_error(err) is False
