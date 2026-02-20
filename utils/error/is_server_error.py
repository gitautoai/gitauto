def _check_int(value, threshold: int = 500):
    return isinstance(value, int) and value >= threshold


def is_server_error(err: Exception):
    """Check if an exception represents a 5xx server error from any SDK."""
    # Anthropic / OpenAI SDK: APIStatusError.status_code (int)
    if _check_int(getattr(err, "status_code", None)):
        return True
    # Stripe SDK: StripeError.http_status (int)
    if _check_int(getattr(err, "http_status", None)):
        return True
    # PyGithub: GithubException.status (int property)
    if _check_int(getattr(err, "status", None)):
        return True
    # requests.HTTPError: err.response.status_code (int)
    response = getattr(err, "response", None)
    if response is not None and _check_int(getattr(response, "status_code", None)):
        return True
    # GQL: TransportServerError.code (int)
    code = getattr(err, "code", None)
    if _check_int(code):
        return True
    # Supabase/PostgREST: APIError.code (string like "502", "PGRST204")
    if isinstance(code, str) and code.isdigit() and int(code) >= 500:
        return True
    # boto3/botocore: ClientError.response["ResponseMetadata"]["HTTPStatusCode"] (int)
    if isinstance(response, dict):
        http_status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if _check_int(http_status):
            return True
    return False
