import pytest

from services.github.create_headers import create_headers
from config import GITHUB_API_VERSION, GITHUB_APP_NAME


def test_create_headers_default_media_type():
    token = "abc123"
    headers = create_headers(token)
    expected_accept = "application/vnd.github.v3+json"
    assert headers["Accept"] == expected_accept, f"Expected Accept header to be {expected_accept}, got {headers['Accept']}"
    assert headers["Authorization"] == f"Bearer {token}", f"Expected Authorization header to be Bearer {token}, got {headers['Authorization']}"
    assert headers["User-Agent"] == GITHUB_APP_NAME, f"Expected User-Agent header to be {GITHUB_APP_NAME}, got {headers['User-Agent']}"
    assert headers["X-GitHub-Api-Version"] == GITHUB_API_VERSION, f"Expected X-GitHub-Api-Version header to be {GITHUB_API_VERSION}, got {headers['X-GitHub-Api-Version']}"


def test_create_headers_custom_media_type():
    token = "xyz789"
    custom_media = ".custom"
    headers = create_headers(token, media_type=custom_media)
    expected_accept = f"application/vnd.github{custom_media}+json"
    assert headers["Accept"] == expected_accept, f"Expected Accept header to be {expected_accept}, got {headers['Accept']}"
    assert headers["Authorization"] == f"Bearer {token}", f"Expected Authorization header to be Bearer {token}, got {headers['Authorization']}"
    assert headers["User-Agent"] == GITHUB_APP_NAME, f"Expected User-Agent header to be {GITHUB_APP_NAME}, got {headers['User-Agent']}"
    assert headers["X-GitHub-Api-Version"] == GITHUB_API_VERSION, f"Expected X-GitHub-Api-Version header to be {GITHUB_API_VERSION}, got {headers['X-GitHub-Api-Version']}"
