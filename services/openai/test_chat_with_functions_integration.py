"""Integration tests for chat_with_functions.py with GPT-5"""

import os
import pytest
from services.openai.chat_with_functions import chat_with_openai


@pytest.mark.skipif(os.getenv("CI"), reason="Skip integration tests in CI")
def test_chat_with_openai_gpt5_integration():
    """Test chat_with_openai function with real GPT-5 API call"""
    messages = [{"role": "user", "content": "Say exactly: function test"}]
    system_content = "Be concise"
    tools = []

    response, _tool_call_id, _tool_name, _tool_args, _token_input, _token_output = (
        chat_with_openai(messages=messages, system_content=system_content, tools=tools)
    )

    assert isinstance(response, dict)
    assert "content" in response
    assert isinstance(response["content"], str)
    assert len(response["content"]) > 0
    print(f"GPT-5 function response: {response['content']}")


@pytest.mark.skipif(os.getenv("CI"), reason="Skip integration tests in CI")
def test_chat_with_openai_gpt5_with_tools():
    """Test chat_with_openai with tools using GPT-5"""
    messages = [{"role": "user", "content": "What's 2+2? Use the calculator."}]
    system_content = "Use tools when appropriate"
    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Calculate math expressions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Math expression",
                        }
                    },
                    "required": ["expression"],
                },
            },
        }
    ]

    response, _tool_call_id, tool_name, tool_args, _token_input, _token_output = (
        chat_with_openai(messages=messages, system_content=system_content, tools=tools)
    )

    assert isinstance(response, dict)
    # Should either return content or make a tool call
    assert "content" in response or "tool_calls" in response
    print(f"GPT-5 tools response: {response}")
    print(f"Tool called: {tool_name}, Args: {tool_args}")
