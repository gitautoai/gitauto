"""Integration tests for chat.py with OpenAI"""

import os

import pytest

from services.openai.chat import chat_with_ai


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Skip integration tests by default to avoid costs",
)
def test_chat_with_ai_integration():
    """Test chat_with_ai function with real OpenAI API call"""
    response = chat_with_ai("You are a test assistant", "Say exactly: test")

    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Skip integration tests by default to avoid costs",
)
def test_chat_with_ai_properties():
    """Test that OpenAI supports all properties used in chat_with_ai"""
    # Test with system and user input (the actual parameters used)
    response = chat_with_ai("Be concise", "What is 2+2?")

    assert isinstance(response, str)
    assert len(response) > 0
    # Should contain "4" since it's a simple math question
    assert "4" in response
