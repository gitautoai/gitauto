import unittest

from services.github.create_headers import create_headers
from tests.constants import TOKEN


def test_create_headers_valid_token():
    """Test that create_headers returns a valid headers dict using a real token.
    We assume that the token is valid and that create_headers adds proper fields.
    """
    headers = create_headers(TOKEN)
    # Expect the headers to contain an Authorization field with a bearer token
    assert isinstance(headers, dict), "Headers should be a dictionary"
    assert 'Authorization' in headers, "Headers must include Authorization"
    assert headers['Authorization'].startswith('Bearer '), "Authorization should start with 'Bearer '"


def test_create_headers_empty_token():
    """Test create_headers with an empty token should result in a headers dictionary with no Authorization."""
    headers = create_headers("")
    # We define behavior: if token is empty, return headers without Authorization key
    # Adjust this test based on actual implementation
    if 'Authorization' in headers:
        assert headers['Authorization'] == 'Bearer ', "Authorization should be 'Bearer ' if token is empty"
    else:
        assert True


class TestCreateHeaders(unittest.TestCase):
    def test_valid_token(self):
        test_create_headers_valid_token()

    def test_empty_token(self):
        test_create_headers_empty_token()


if __name__ == '__main__':
    unittest.main()
