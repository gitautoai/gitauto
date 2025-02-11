"""Unit tests for create_headers function.

Related Documentation: 
https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api#headers
"""

from services.github.create_headers import create_headers


def test_create_headers_default():
    # Testing default headers creation
    token = "testtoken"
    headers = create_headers(token)
    assert headers["Authorization"] == f"Bearer {token}"
    assert headers["Accept"].startswith("application/vnd.github")
    assert "User-Agent" in headers
    assert "X-GitHub-Api-Version" in headers


def test_create_headers_custom_media():
    # Testing custom media type in headers creation
    token = "testtoken"
    media_type = ".v3+test"
    headers = create_headers(token, media_type)
    assert headers["Accept"] == f"application/vnd.github{media_type}+json"
