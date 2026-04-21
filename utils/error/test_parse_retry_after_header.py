from utils.error.parse_retry_after_header import parse_retry_after_header


def test_returns_none_when_headers_is_none():
    assert parse_retry_after_header(None) is None


def test_returns_none_when_headers_is_empty_dict():
    assert parse_retry_after_header({}) is None


def test_returns_none_when_retry_after_missing():
    assert parse_retry_after_header({"Content-Type": "application/json"}) is None


def test_parses_integer_seconds_from_canonical_header():
    assert parse_retry_after_header({"Retry-After": "30"}) == 30.0


def test_parses_float_seconds():
    assert parse_retry_after_header({"Retry-After": "3.5"}) == 3.5


def test_parses_lowercase_header_name():
    assert parse_retry_after_header({"retry-after": "10"}) == 10.0


def test_prefers_canonical_case_over_lowercase():
    # Canonical "Retry-After" wins when both are set (shouldn't happen in real
    # responses, but documents the lookup order).
    headers = {"Retry-After": "5", "retry-after": "99"}
    assert parse_retry_after_header(headers) == 5.0


def test_returns_none_when_value_is_http_date():
    # RFC 7231 allows HTTP-date but we only accept numeric seconds.
    assert (
        parse_retry_after_header({"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})
        is None
    )


def test_returns_none_when_value_is_garbage():
    assert parse_retry_after_header({"Retry-After": "not-a-number"}) is None
