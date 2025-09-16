"""Integration tests for chat.py with GPT-5"""

import os
import pytest
from services.openai.chat import chat_with_ai


@pytest.mark.skipif(bool(os.getenv("CI")), reason="Skip integration tests in CI")
def test_chat_with_ai_gpt5_integration():
    """Test chat_with_ai function with real GPT-5 API call"""
    response = chat_with_ai("You are a test assistant", "Say exactly: test")

    assert isinstance(response, str)
    assert len(response) > 0
    print(f"GPT-5 chat response: {response}")


@pytest.mark.skipif(bool(os.getenv("CI")), reason="Skip integration tests in CI")
def test_chat_with_ai_gpt5_properties():
    """Test that GPT-5 supports all properties used in chat_with_ai"""
    # Test with system and user input (the actual parameters used)
    response = chat_with_ai("Be concise", "What is 2+2?")

    assert isinstance(response, str)
    assert len(response) > 0
    # Should contain "4" since it's a simple math question
    assert "4" in response
    print(f"GPT-5 math response: {response}")
