#!/usr/bin/env python3

import sys
sys.path.append('.')

from unittest.mock import Mock
from services.anthropic.trim_messages import trim_messages_to_token_limit

def make_message(role, content="test"):
    """Create a simple message dictionary."""
    return {"role": role, "content": content}

def make_tool_result_message(tool_use_id, result="test result"):
    """Create a message with tool_result content."""
    return {
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": tool_use_id, "content": result}
        ],
    }

# Test the failing scenario
messages = [
    make_message("user", "query"),
    {
        "role": "assistant",
        "content": [
            {"type": "text", "text": "Here's the result:"},
            {"type": "tool_use", "id": "tool1", "name": "search", "input": {}},
            {"type": "text", "text": "Additional text"},
            {"type": "tool_use", "id": "tool2", "name": "analyze", "input": {}},  # Second tool_use
        ],
    },
    make_tool_result_message("tool1"),  # Only matches first tool_use
]

# Mock client
mock_client = Mock()
def count_tokens_progressive(messages, model):
    if len(messages) >= 3:
        return Mock(input_tokens=5000)  # Over limit
    return Mock(input_tokens=800)  # Under limit

mock_client.messages.count_tokens.side_effect = count_tokens_progressive

trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

print(f"Original messages: {len(messages)}")
print(f"Trimmed messages: {len(trimmed)}")
print(f"Expected: 2, Got: {len(trimmed)}")
