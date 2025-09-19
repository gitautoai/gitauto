#!/usr/bin/env python3
"""Simple import check for the trim_messages test file."""

try:
    from services.anthropic.trim_messages import trim_messages_to_token_limit
    from unittest.mock import Mock
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)
