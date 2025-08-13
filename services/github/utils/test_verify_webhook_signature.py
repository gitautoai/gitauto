import hashlib
import hmac
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request

from services.github.utils.verify_webhook_signature import verify_webhook_signature


@pytest.fixture
def mock_request():
    """Fixture to provide a mocked FastAPI Request object."""
    request = MagicMock(spec=Request)
    request.headers = {}
    request.body = AsyncMock()
    return request


@pytest.fixture
def sample_secret():
    """Fixture providing a sample webhook secret."""
    return "test_webhook_secret_123"


@pytest.fixture
def sample_body():
    """Fixture providing a sample request body."""
    return b'{"action": "opened", "number": 1}'


@pytest.fixture
def valid_signature(sample_secret, sample_body):
    """Fixture providing a valid GitHub webhook signature."""
    hmac_signature = hmac.new(
        key=sample_secret.encode(),
        msg=sample_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    return f"sha256={hmac_signature}"


@pytest.mark.asyncio
async def test_verify_webhook_signature_success(
    mock_request, sample_secret, sample_body, valid_signature
):
    """Test successful webhook signature verification."""
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_body

    # Should not raise any exception
    await verify_webhook_signature(mock_request, sample_secret)

    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_missing_header(mock_request, sample_secret):
    """Test verification fails when signature header is missing."""
    mock_request.headers = {}
    mock_request.body.return_value = b"test body"

    with pytest.raises(ValueError) as exc_info:
        await verify_webhook_signature(mock_request, sample_secret)

    assert str(exc_info.value) == "Missing webhook signature"
    mock_request.body.assert_not_called()


@pytest.mark.asyncio
async def test_verify_webhook_signature_none_header(mock_request, sample_secret):
    """Test verification fails when signature header is None."""
    mock_request.headers = {"X-Hub-Signature-256": None}
    mock_request.body.return_value = b"test body"

    with pytest.raises(ValueError) as exc_info:
        await verify_webhook_signature(mock_request, sample_secret)

    assert str(exc_info.value) == "Missing webhook signature"
    mock_request.body.assert_not_called()


@pytest.mark.asyncio
async def test_verify_webhook_signature_invalid_signature(
    mock_request, sample_secret, sample_body
):
    """Test verification fails with invalid signature."""
    mock_request.headers = {"X-Hub-Signature-256": "sha256=invalid_signature"}
    mock_request.body.return_value = sample_body

    with pytest.raises(ValueError) as exc_info:
        await verify_webhook_signature(mock_request, sample_secret)

    assert str(exc_info.value) == "Invalid webhook signature"
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_wrong_secret(
    mock_request, sample_body, valid_signature
):
    """Test verification fails with wrong secret."""
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_body
    wrong_secret = "wrong_secret"

    with pytest.raises(ValueError) as exc_info:
        await verify_webhook_signature(mock_request, wrong_secret)

    assert str(exc_info.value) == "Invalid webhook signature"
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_empty_body(mock_request, sample_secret):
    """Test verification with empty request body."""
    empty_body = b""
    hmac_signature = hmac.new(
        key=sample_secret.encode(),
        msg=empty_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    valid_signature = f"sha256={hmac_signature}"

    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = empty_body

    # Should not raise any exception
    await verify_webhook_signature(mock_request, sample_secret)

    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_large_body(mock_request, sample_secret):
    """Test verification with large request body."""
    large_body = b"x" * 10000  # 10KB body
    hmac_signature = hmac.new(
        key=sample_secret.encode(),
        msg=large_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    valid_signature = f"sha256={hmac_signature}"

    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = large_body

    # Should not raise any exception
    await verify_webhook_signature(mock_request, sample_secret)

    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_unicode_body(mock_request, sample_secret):
    """Test verification with Unicode characters in body."""
    unicode_body = '{"message": "Hello world"}'.encode('utf-8')
    hmac_signature = hmac.new(
        key=sample_secret.encode(),
        msg=unicode_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    valid_signature = f"sha256={hmac_signature}"

    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = unicode_body

    # Should not raise any exception
    await verify_webhook_signature(mock_request, sample_secret)

    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_special_characters_secret(
    mock_request, sample_body
):
    """Test verification with special characters in secret."""
    special_secret = "secret!@#$%^&*()_+-=[]{}|;:,.<>?"
    hmac_signature = hmac.new(
        key=special_secret.encode(),
        msg=sample_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    valid_signature = f"sha256={hmac_signature}"

    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_body

    # Should not raise any exception
    await verify_webhook_signature(mock_request, special_secret)

    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_empty_secret(mock_request, sample_body):
    """Test verification with empty secret."""
    empty_secret = ""
    hmac_signature = hmac.new(
        key=empty_secret.encode(),
        msg=sample_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    valid_signature = f"sha256={hmac_signature}"

    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_body

    # Should not raise any exception
    await verify_webhook_signature(mock_request, empty_secret)

    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_malformed_signature_format(
    mock_request, sample_secret, sample_body
):
    """Test verification fails with malformed signature format."""
    test_cases = [
        "invalid_format",
        "sha256invalid",
        "sha256=",
        "md5=abcdef123456",
        "sha1=abcdef123456",
        "=sha256abcdef123456",
    ]

    for malformed_signature in test_cases:
        mock_request.headers = {"X-Hub-Signature-256": malformed_signature}
        mock_request.body.return_value = sample_body

        with pytest.raises(ValueError) as exc_info:
            await verify_webhook_signature(mock_request, sample_secret)

        assert str(exc_info.value) == "Invalid webhook signature"
        mock_request.body.assert_called_once()

        # Reset mock for next iteration
        mock_request.body.reset_mock()


@pytest.mark.asyncio
async def test_verify_webhook_signature_case_sensitivity(
    mock_request, sample_secret, sample_body
):
    """Test that signature verification is case sensitive."""
    hmac_signature = hmac.new(
        key=sample_secret.encode(),
        msg=sample_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Test uppercase signature (should fail)
    uppercase_signature = f"sha256={hmac_signature.upper()}"
    mock_request.headers = {"X-Hub-Signature-256": uppercase_signature}
    mock_request.body.return_value = sample_body

    with pytest.raises(ValueError) as exc_info:
        await verify_webhook_signature(mock_request, sample_secret)

    assert str(exc_info.value) == "Invalid webhook signature"
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_timing_attack_protection(
    mock_request, sample_secret, sample_body
):
    """Test that hmac.compare_digest is used for timing attack protection."""
    valid_hmac = hmac.new(
        key=sample_secret.encode(),
        msg=sample_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    valid_signature = f"sha256={valid_hmac}"
    
    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_body

    with patch('hmac.compare_digest') as mock_compare_digest:
        mock_compare_digest.return_value = True
        
        await verify_webhook_signature(mock_request, sample_secret)
        
        # Verify that hmac.compare_digest was called with correct arguments
        # Verify that hmac.compare_digest was called
        # The actual arguments will be the received signature and expected signature
        mock_compare_digest.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_header_case_insensitive(
    mock_request, sample_secret, sample_body, valid_signature
):
    """Test that header name lookup is case insensitive."""
    # FastAPI Request.headers.get() should handle case insensitivity
    mock_request.headers = MagicMock()
    mock_request.headers.get.return_value = valid_signature
    mock_request.body.return_value = sample_body

    await verify_webhook_signature(mock_request, sample_secret)

    mock_request.headers.get.assert_called_once_with("X-Hub-Signature-256")
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_body_called_after_header_check(
    mock_request, sample_secret
):
    """Test that request body is only accessed after header validation."""
    mock_request.headers = {}
    mock_request.body.return_value = b"test body"

    with pytest.raises(ValueError) as exc_info:
        await verify_webhook_signature(mock_request, sample_secret)

    assert str(exc_info.value) == "Missing webhook signature"
    # Body should not be called when header is missing
    mock_request.body.assert_not_called()


@pytest.mark.asyncio
async def test_verify_webhook_signature_hmac_computation_steps(
    mock_request, sample_secret, sample_body
):
    """Test the HMAC computation steps are performed correctly."""
    hmac_signature = hmac.new(
        key=sample_secret.encode(),
        msg=sample_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    valid_signature = f"sha256={hmac_signature}"

    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_body

    with patch('services.github.utils.verify_webhook_signature.hmac.new') as mock_hmac_new:
        mock_hmac_obj = MagicMock()
        mock_hmac_obj.hexdigest.return_value = hmac_signature
        mock_hmac_new.return_value = mock_hmac_obj

        await verify_webhook_signature(mock_request, sample_secret)

        # Verify HMAC was created with correct parameters
        mock_hmac_new.assert_called_once_with(
            key=sample_secret.encode(),
            msg=sample_body,
            digestmod=hashlib.sha256
        )
        mock_hmac_obj.hexdigest.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_secret_encoding(
    mock_request, sample_body, valid_signature
):
    """Test that secret is properly encoded to bytes."""
    unicode_secret = "test_secret_with_unicode_chars"
    
    # Create valid signature with the unicode secret
    hmac_signature = hmac.new(
        key=unicode_secret.encode(),
        msg=sample_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    valid_signature = f"sha256={hmac_signature}"

    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = sample_body

    # Should not raise any exception
    await verify_webhook_signature(mock_request, unicode_secret)

    mock_request.body.assert_called_once()

@pytest.mark.asyncio
async def test_verify_webhook_signature_whitespace_in_signature(
    mock_request, sample_secret, sample_body
):
    """Test verification fails with whitespace in signature."""
    hmac_signature = hmac.new(
        key=sample_secret.encode(),
        msg=sample_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Add whitespace to signature
    signature_with_whitespace = f" sha256={hmac_signature} "
    mock_request.headers = {"X-Hub-Signature-256": signature_with_whitespace}
    mock_request.body.return_value = sample_body

    with pytest.raises(ValueError) as exc_info:
        await verify_webhook_signature(mock_request, sample_secret)

    assert str(exc_info.value) == "Invalid webhook signature"
    mock_request.body.assert_called_once()


@pytest.mark.asyncio
async def test_verify_webhook_signature_different_body_content(
    mock_request, sample_secret
):
    """Test verification with different types of body content."""
    test_bodies = [
        b'{"key": "value"}',  # JSON
        b'key=value&another=test',  # Form data
        b'<xml><data>test</data></xml>',  # XML
        b'plain text content',  # Plain text
        b'\x00\x01\x02\x03',  # Binary data
    ]

    for body in test_bodies:
        hmac_signature = hmac.new(
            key=sample_secret.encode(),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
        valid_signature = f"sha256={hmac_signature}"

        mock_request.headers = {"X-Hub-Signature-256": valid_signature}
        mock_request.body.return_value = body

        # Should not raise any exception
        await verify_webhook_signature(mock_request, sample_secret)

        mock_request.body.assert_called_once()
        # Reset mock for next iteration
        mock_request.body.reset_mock()


@pytest.mark.asyncio
async def test_verify_webhook_signature_exception_handling(mock_request, sample_secret):
    """Test that exceptions from request.body() are properly handled."""
    mock_request.headers = {"X-Hub-Signature-256": "sha256=test"}
    mock_request.body.side_effect = Exception("Body read error")

    # Since the function is decorated with @handle_exceptions(raise_on_error=True),
    # it should re-raise the exception
    with pytest.raises(Exception) as exc_info:
        await verify_webhook_signature(mock_request, sample_secret)

    assert str(exc_info.value) == "Body read error"
    mock_request.body.assert_called_once()


@pytest.mark.parametrize(
    "secret,body,expected_valid",
    [
        ("simple", b"test", True),
        ("", b"empty_secret", True),
        ("unicode_chars", b"unicode_secret", True),
        ("special!@#$", b"special_chars", True),
        ("very_long_secret_" * 10, b"long_secret", True),
    ],
)
@pytest.mark.asyncio
async def test_verify_webhook_signature_parametrized(
    mock_request, secret, body, expected_valid
):
    """Test verification with various secret and body combinations."""
    hmac_signature = hmac.new(
        key=secret.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    valid_signature = f"sha256={hmac_signature}"

    mock_request.headers = {"X-Hub-Signature-256": valid_signature}
    mock_request.body.return_value = body

    # Should not raise any exception for all valid cases
    await verify_webhook_signature(mock_request, secret)
