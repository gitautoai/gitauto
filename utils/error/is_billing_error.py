def is_billing_error(err: Exception):
    """Check if an exception is a billing/credit-balance error that should not be reported to Sentry."""
    message = str(err).lower()
    if "credit balance" in message:
        return True
    return False
