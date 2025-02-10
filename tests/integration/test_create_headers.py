
from services.github.create_headers import create_headers
from tests.constants import TOKEN, OWNER, REPO


def test_create_headers_integration():
    """Test the integration behavior of create_headers."""
    headers = create_headers()

    # Ensure the result is a dictionary
    assert isinstance(headers, dict)

    # Verify the presence of Authorization header with proper token prefix
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("token ")
