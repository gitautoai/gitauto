from unittest.mock import MagicMock

from utils.error.is_server_error import is_server_error


def test_status_code_500():
    err = Exception("Internal server error")
    err.status_code = 500  # type: ignore[attr-defined]
    assert is_server_error(err) is True


def test_status_code_502():
    err = Exception("Bad Gateway")
    err.status_code = 502  # type: ignore[attr-defined]
    assert is_server_error(err) is True


def test_status_code_400_not_server_error():
    err = Exception("Bad Request")
    err.status_code = 400  # type: ignore[attr-defined]
    assert is_server_error(err) is False


def test_stripe_http_status_500():
    err = Exception("Stripe error")
    err.http_status = 500  # type: ignore[attr-defined]
    assert is_server_error(err) is True


def test_stripe_http_status_429_not_server_error():
    err = Exception("Rate limited")
    err.http_status = 429  # type: ignore[attr-defined]
    assert is_server_error(err) is False


def test_pygithub_status_502():
    err = Exception("Bad Gateway")
    err.status = 502  # type: ignore[attr-defined]
    assert is_server_error(err) is True


def test_pygithub_status_404_not_server_error():
    err = Exception("Not found")
    err.status = 404  # type: ignore[attr-defined]
    assert is_server_error(err) is False


def test_requests_response_status_code_503():
    err = Exception("Service Unavailable")
    mock_response = MagicMock()
    mock_response.status_code = 503
    err.response = mock_response  # type: ignore[attr-defined]
    assert is_server_error(err) is True


def test_requests_response_status_code_403_not_server_error():
    err = Exception("Forbidden")
    mock_response = MagicMock()
    mock_response.status_code = 403
    err.response = mock_response  # type: ignore[attr-defined]
    assert is_server_error(err) is False


def test_gql_code_int_500():
    err = Exception("Server error")
    err.code = 500  # type: ignore[attr-defined]
    assert is_server_error(err) is True


def test_gql_code_int_400_not_server_error():
    err = Exception("Bad request")
    err.code = 400  # type: ignore[attr-defined]
    assert is_server_error(err) is False


def test_supabase_code_502():
    err = Exception("Bad Gateway")
    err.code = "502"  # type: ignore[attr-defined]
    assert is_server_error(err) is True


def test_supabase_code_non_numeric():
    err = Exception("Column not found")
    err.code = "PGRST204"  # type: ignore[attr-defined]
    assert is_server_error(err) is False


def test_boto3_response_dict_500():
    err = Exception("AWS error")
    err.response = {"ResponseMetadata": {"HTTPStatusCode": 500}}  # type: ignore[attr-defined]
    assert is_server_error(err) is True


def test_boto3_response_dict_400_not_server_error():
    err = Exception("AWS error")
    err.response = {"ResponseMetadata": {"HTTPStatusCode": 400}}  # type: ignore[attr-defined]
    assert is_server_error(err) is False


def test_plain_exception():
    err = Exception("Something broke")
    assert is_server_error(err) is False
