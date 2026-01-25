from unittest.mock import patch

import pytest
from fastapi import HTTPException

from services.website.verify_api_key import verify_api_key


def test_verify_api_key_valid():
    with patch("services.website.verify_api_key.GITAUTO_API_KEY", "test-api-key"):
        verify_api_key(api_key="test-api-key")


def test_verify_api_key_invalid():
    with patch("services.website.verify_api_key.GITAUTO_API_KEY", "test-api-key"):
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(api_key="wrong-key")
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid API key"


def test_verify_api_key_empty():
    with patch("services.website.verify_api_key.GITAUTO_API_KEY", "test-api-key"):
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(api_key="")
        assert exc_info.value.status_code == 401
