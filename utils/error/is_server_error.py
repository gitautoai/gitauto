def is_server_error(err: Exception):
    """Check if an exception represents a 5xx server error from any SDK."""
    # Anthropic SDK: APIStatusError has status_code attribute
    status_code = getattr(err, "status_code", None)
    if isinstance(status_code, int) and status_code >= 500:
        return True
    # Supabase/PostgREST: APIError has code attribute (string like "502", "PGRST204")
    code = getattr(err, "code", None)
    if isinstance(code, str) and code.isdigit() and int(code) >= 500:
        return True
    return False
