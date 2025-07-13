#!/usr/bin/env python3
"""Quick syntax test for the verify_webhook_signature module."""

try:
    from services.github.utils.verify_webhook_signature import verify_webhook_signature
    from services.github.utils.test_verify_webhook_signature import TestVerifyWebhookSignature
    print("✅ Import successful - no syntax errors")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)