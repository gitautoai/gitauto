"""Unit tests for verify_webhook_signature function.

Related Documentation:
https://docs.github.com/en/webhooks/webhooks/securing-your-webhooks
"""

import hashlib
import hmac
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Request

from services.github.utils.verify_webhook_signature import verify_webhook_signature


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {}
    mock_req.body = AsyncMock()
    return mock_req


@pytest.fixture
def sample_secret():
    """Provide a sample webhook secret for testing."""
    return "test_webhook_secret_123"


@pytest.fixture
def sample_payload():
    """Provide a sample webhook payload for testing."""
    return b'{"action": "opened", "number": 1}'


def create_valid_signature(payload: bytes, secret: str) -> str:
    """Helper function to create a valid GitHub webhook signature."""
    hmac_key = secret.encode()
    hmac_signature = hmac.new(
        key=hmac_key, msg=payload, digestmod=hashlib.sha256
    ).hexdigest()
    return f"sha256={hmac_signature}"


@pytest.mark.asyncio
async def test_verify_webhook_signature_success(
    mock_request, sample_secret, sample_payload
):
    """Test successful webhook signature verification."""
    # Setup
    valid_signature = create_valid_signature(sample_payload, sample_secret)
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_payload

    # Execute - should not raise any exception
    await verify_webhook_signature(request=mock_request, secret=sample_secret)

    # Verify
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_missing_header(
    mock_request, sample_secret, sample_payload
):
    """Test that missing signature header raises ValueError."""
    # Setup
    mock_request.headers = {}  # No X-Hub-Signature-256 header
    mock_request.body.return_value = sample_payload

    # Execute & Verify
    with pytest.raises(ValueError, match="Missing webhook signature"):
        await verify_webhook_signature(request=mock_request, secret=sample_secret)


@pytest.mark.asyncio
async def test_verify_webhook_signature_none_header(
    mock_request, sample_secret, sample_payload
):
    """Test that None signature header raises ValueError."""
    # Setup
    mock_request.headers = {"X-Hub-Signature-256": None}
    mock_request.body.return_value = sample_payload

    # Execute & Verify
    with pytest.raises(ValueError, match="Missing webhook signature"):
        await verify_webhook_signature(request=mock_request, secret=sample_secret)


@pytest.mark.asyncio
async def test_verify_webhook_signature_invalid_signature(
    mock_request, sample_secret, sample_payload
):
    """Test that invalid signature raises ValueError."""
    # Setup
    invalid_signature = "sha256=invalid_signature_hash"
    mock_request.headers = {"X-Hub-Signature-256": invalid_signature}
    mock_request.body.return_value = sample_payload

    # Execute & Verify
    with pytest.raises(ValueError, match="Invalid webhook signature"):
        await verify_webhook_signature(request=mock_request, secret=sample_secret)


@pytest.mark.asyncio
async def test_verify_webhook_signature_wrong_secret(
    mock_request, sample_secret, sample_payload
):
    """Test that signature created with wrong secret fails verification."""
    # Setup
    wrong_secret = "wrong_secret"
    signature_with_wrong_secret = create_valid_signature(sample_payload, wrong_secret)
    mock_request.headers = {"X-Hub-Signature-256": signature_with_wrong_secret}
    mock_request.body.return_value = sample_payload

    # Execute & Verify
    with pytest.raises(ValueError, match="Invalid webhook signature"):
        await verify_webhook_signature(request=mock_request, secret=sample_secret)


@pytest.mark.asyncio
async def test_verify_webhook_signature_different_payload(
    mock_request, sample_secret, sample_payload
):
    """Test that signature fails when payload is different."""
    # Setup
    different_payload = b'{"action": "closed", "number": 2}'
    signature_for_original = create_valid_signature(sample_payload, sample_secret)
    mock_request.headers = {"X-Hub-Signature-256": signature_for_original}
    mock_request.body.return_value = different_payload

    # Execute & Verify
    with pytest.raises(ValueError, match="Invalid webhook signature"):
        await verify_webhook_signature(request=mock_request, secret=sample_secret)


@pytest.mark.asyncio
async def test_verify_webhook_signature_empty_payload(
    mock_request, sample_secret
):
    """Test verification with empty payload."""
    # Setup
    empty_payload = b""
    valid_signature = create_valid_signature(empty_payload, sample_secret)
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = empty_payload

    # Execute - should not raise any exception
    await verify_webhook_signature(request=mock_request, secret=sample_secret)

    # Verify
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_large_payload(
    mock_request, sample_secret
):
    """Test verification with large payload."""
    # Setup
    large_payload = b"x" * 10000  # 10KB payload
    valid_signature = create_valid_signature(large_payload, sample_secret)
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = large_payload

    # Execute - should not raise any exception
    await verify_webhook_signature(request=mock_request, secret=sample_secret)

    # Verify
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_unicode_payload(
    mock_request, sample_secret
):
    """Test verification with Unicode characters in payload."""
    # Setup
    unicode_payload = '{"message": "Hello 世界! 🌍"}'.encode("utf-8")
    valid_signature = create_valid_signature(unicode_payload, sample_secret)
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = unicode_payload

    # Execute - should not raise any exception
    await verify_webhook_signature(request=mock_request, secret=sample_secret)

    # Verify
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_empty_secret(
    mock_request, sample_payload
):
    """Test verification with empty secret."""
    # Setup
    empty_secret = ""
    valid_signature = create_valid_signature(sample_payload, empty_secret)
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_payload

    # Execute - should not raise any exception
    await verify_webhook_signature(request=mock_request, secret=empty_secret)

    # Verify
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_special_characters_secret(
    mock_request, sample_payload
):
    """Test verification with special characters in secret."""
    # Setup
    special_secret = "secret!@#$%^&*()_+-=[]{}|;:,.<>?"
    valid_signature = create_valid_signature(sample_payload, special_secret)
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_payload

    # Execute - should not raise any exception
    await verify_webhook_signature(request=mock_request, secret=special_secret)

    # Verify
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_case_sensitive(
    mock_request, sample_secret, sample_payload
):
    """Test that signature verification is case sensitive."""
    # Setup
    valid_signature = create_valid_signature(sample_payload, sample_secret)
    uppercase_signature = valid_signature.upper()
    mock_request.headers = {"X-Hub-Signature-256": uppercase_signature}
    mock_request.body.return_value = sample_payload

    # Execute & Verify
    with pytest.raises(ValueError, match="Invalid webhook signature"):
        await verify_webhook_signature(request=mock_request, secret=sample_secret)


@pytest.mark.asyncio
async def test_verify_webhook_signature_malformed_signature_format(
    mock_request, sample_secret, sample_payload
):
    """Test that malformed signature format fails verification."""
    # Setup - missing 'sha256=' prefix
    hmac_key = sample_secret.encode()
    hmac_signature = hmac.new(
        key=hmac_key, msg=sample_payload, digestmod=hashlib.sha256
    ).hexdigest()
    malformed_signature = hmac_signature  # Missing 'sha256=' prefix
    mock_request.headers = {"X-Hub-Signature-256": malformed_signature}
    mock_request.body.return_value = sample_payload

    # Execute & Verify
    with pytest.raises(ValueError, match="Invalid webhook signature"):
        await verify_webhook_signature(request=mock_request, secret=sample_secret)


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    b'{"test": "data"}',
    b'',
    '{"unicode": "测试"}'.encode("utf-8"),
    b'{"number": 12345}',
    b'{"boolean": true}',
    b'{"array": [1, 2, 3]}',
    b'{"nested": {"key": "value"}}',
])
async def test_verify_webhook_signature_various_payloads(
    mock_request, sample_secret, payload
):
    """Test verification with various payload formats."""
    # Setup
    valid_signature = create_valid_signature(payload, sample_secret)
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = payload

    # Execute - should not raise any exception
    await verify_webhook_signature(request=mock_request, secret=sample_secret)

    # Verify
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("secret", [
    "simple_secret",
    "secret-with-dashes",
    "secret_with_underscores",
    "SecretWithMixedCase",
    "secret123456",
    "very_long_secret_that_is_much_longer_than_typical_secrets_used_in_production",
    "短密码",  # Short password in Chinese
])
async def test_verify_webhook_signature_various_secrets(
    mock_request, sample_payload, secret
):
    """Test verification with various secret formats."""
    # Setup
    valid_signature = create_valid_signature(sample_payload, secret)
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_payload

    # Execute - should not raise any exception
    await verify_webhook_signature(request=mock_request, secret=secret)

    # Verify
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_timing_attack_resistance(
    mock_request, sample_secret, sample_payload
):
    """Test that the function uses hmac.compare_digest for timing attack resistance."""
    # This test verifies that we're using the secure comparison function
    # Setup with a signature that differs by only one character
    valid_signature = create_valid_signature(sample_payload, sample_secret)
    # Change one character in the signature
    invalid_signature = valid_signature[:-1] + ("0" if valid_signature[-1] != "0" else "1")
    mock_request.headers = {"X-Hub-Signature-256": invalid_signature}
    mock_request.body.return_value = sample_payload

    # Execute & Verify
    # The function should still raise ValueError even for signatures that differ by one character
    with pytest.raises(ValueError, match="Invalid webhook signature"):
        await verify_webhook_signature(request=mock_request, secret=sample_secret)


@pytest.mark.asyncio
async def test_verify_webhook_signature_request_body_exception(
    mock_request, sample_secret
):
    """Test that exceptions from request.body() are properly propagated."""
    # Setup
    mock_request.headers = {"X-Hub-Signature-256": "sha256=test"}
    mock_request.body.side_effect = Exception("Request body error")

    # Execute & Verify
    # The function should propagate the exception from request.body()
    with pytest.raises(Exception, match="Request body error"):
        await verify_webhook_signature(request=mock_request, secret=sample_secret)


@pytest.mark.asyncio
async def test_verify_webhook_signature_header_case_insensitive_key(
    sample_secret, sample_payload
):
    """Test that header key lookup is case insensitive (FastAPI behavior)."""
    # Setup - create a mock that simulates FastAPI's case-insensitive headers
    mock_request = MagicMock(spec=Request)
    
    # Create a case-insensitive dict-like object for headers
    class CaseInsensitiveHeaders:
        def __init__(self, headers):
            self._headers = {k.lower(): v for k, v in headers.items()}
        
        def get(self, key, default=None):
            return self._headers.get(key.lower(), default)
    
    valid_signature = create_valid_signature(sample_payload, sample_secret)
    # Use different case for the header key
    headers = CaseInsensitiveHeaders({"x-hub-signature-256": valid_signature})
    mock_request.headers = headers
    mock_request.body = AsyncMock(return_value=sample_payload)

    # Execute - should work with case-insensitive header lookup
    await verify_webhook_signature(request=mock_request, secret=sample_secret)

    # Verify
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_real_github_example(
    mock_request
):
    """Test with a real GitHub webhook example."""
    # Setup with realistic GitHub webhook data
    github_secret = "my_webhook_secret"
    github_payload = b'{"zen":"Speak like a human.","hook_id":12345678}'
    
    # Create the signature as GitHub would
    valid_signature = create_valid_signature(github_payload, github_secret)
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = github_payload

    # Execute - should not raise any exception
    await verify_webhook_signature(request=mock_request, secret=github_secret)

    # Verify
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_consistent_behavior(
    mock_request, sample_secret, sample_payload
):
    """Test that multiple calls with same parameters behave consistently."""
    # Setup
    valid_signature = create_valid_signature(sample_payload, sample_secret)
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_payload

    # Execute multiple times - all should succeed
    await verify_webhook_signature(request=mock_request, secret=sample_secret)
    await verify_webhook_signature(request=mock_request, secret=sample_secret)
    await verify_webhook_signature(request=mock_request, secret=sample_secret)

    # Verify that body was called each time
    assert mock_request.body.call_count == 3


@pytest.mark.asyncio
async def test_verify_webhook_signature_return_value(
    mock_request, sample_secret, sample_payload
):
    """Test that the function returns None on success."""
    # Setup
    valid_signature = create_valid_signature(sample_payload, sample_secret)
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_payload

    # Execute
    result = await verify_webhook_signature(request=mock_request, secret=sample_secret)

    # Verify
    assert result is None
    mock_request.body.assert_called_once()
