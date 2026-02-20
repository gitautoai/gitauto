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


def test_supabase_code_502():
    err = Exception("Bad Gateway")
    err.code = "502"  # type: ignore[attr-defined]
    assert is_server_error(err) is True


def test_supabase_code_non_numeric():
    err = Exception("Column not found")
    err.code = "PGRST204"  # type: ignore[attr-defined]
    assert is_server_error(err) is False


def test_plain_exception():
    err = Exception("Something broke")
    assert is_server_error(err) is False
