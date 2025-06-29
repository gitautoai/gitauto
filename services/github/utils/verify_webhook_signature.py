import hashlib  # For HMAC (Hash-based Message Authentication Code) signatures
import hmac  # For HMAC (Hash-based Message Authentication Code) signatures
from fastapi import Request
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
async def verify_webhook_signature(request: Request, secret: str) -> None:
    """Verify the webhook signature for security"""
    signature: str | None = request.headers.get("X-Hub-Signature-256")
    if signature is None:
        raise ValueError("Missing webhook signature")
    body: bytes = await request.body()

    # Compare the computed signature with the one in the headers
    hmac_key: bytes = secret.encode()
    hmac_signature: str = hmac.new(
        key=hmac_key, msg=body, digestmod=hashlib.sha256
    ).hexdigest()
    expected_signature: str = "sha256=" + hmac_signature
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid webhook signature")
