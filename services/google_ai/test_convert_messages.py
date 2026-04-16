# pyright: reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportArgumentType=false, reportOptionalIterable=false
import json
from pathlib import Path

from services.google_ai.convert_messages import convert_messages_to_google

# Real Claude conversation captured from services/claude/test_messages.json
FIXTURE_PATH = Path(__file__).parent.parent / "claude" / "test_messages.json"


def _load_real_messages():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_convert_real_messages_count():
    """All 9 real messages produce 9 Google Content objects."""
    messages = _load_real_messages()
    result = convert_messages_to_google(messages)
    assert len(result) == 9


def test_convert_real_messages_roles():
    """Roles convert correctly: user->user, assistant->model."""
    messages = _load_real_messages()
    result = convert_messages_to_google(messages)
    expected_roles = [
        "user",
        "model",
        "user",
        "model",
        "user",
        "model",
        "user",
        "model",
        "user",
    ]
    actual_roles = [c.role for c in result]
    assert actual_roles == expected_roles


def test_convert_real_messages_first_user_text():
    """First message is plain text 'First message'."""
    messages = _load_real_messages()
    result = convert_messages_to_google(messages)
    assert len(result[0].parts) == 1
    assert result[0].parts[0].text == "First message"


def test_convert_real_messages_assistant_text_and_tool_use():
    """Second message (assistant) has text + tool_use -> Part(text) + Part(function_call)."""
    messages = _load_real_messages()
    result = convert_messages_to_google(messages)
    msg = result[1]
    assert msg.role == "model"
    assert len(msg.parts) == 2
    assert msg.parts[0].text == "Second message"
    fc = msg.parts[1].function_call
    assert fc.name == "get_remote_file_content"
    assert fc.args == {"file_path": "services/anthropic/test_client.py"}
    assert fc.id == "toolu_01UqpdeuMtRAfShXJjZnM1xr"


def test_convert_real_messages_tool_result():
    """Third message (user) has tool_result -> Part(function_response)."""
    messages = _load_real_messages()
    result = convert_messages_to_google(messages)
    msg = result[2]
    assert msg.role == "user"
    assert len(msg.parts) == 1
    fr = msg.parts[0].function_response
    assert fr.name == "toolu_01UqpdeuMtRAfShXJjZnM1xr"
    assert fr.id == "toolu_01UqpdeuMtRAfShXJjZnM1xr"
    assert fr.response == {
        "result": "Opened file: 'services/anthropic/test_client.py' with line numbers for your information.\n\n```services/anthropic/test_client.py\n 1:import pytest\n```"
    }


def test_convert_real_messages_all_tool_use_ids():
    """All 4 tool_use blocks have correct IDs and names."""
    messages = _load_real_messages()
    result = convert_messages_to_google(messages)
    expected_tool_calls = [
        ("toolu_01UqpdeuMtRAfShXJjZnM1xr", "get_remote_file_content"),
        ("toolu_01TfGJfs9sTn2hZnG9DscBcr", "get_remote_file_content"),
        ("toolu_0186eQgzhNNQmxwC5NmvsaHC", "get_remote_file_content"),
        ("toolu_01783z1Lrhbs38GvsnvGEX8o", "write_and_commit_file"),
    ]
    actual_tool_calls = []
    for content in result:
        for part in content.parts:
            if part.function_call:
                actual_tool_calls.append(
                    (part.function_call.id, part.function_call.name)
                )
    assert actual_tool_calls == expected_tool_calls


def test_convert_real_messages_all_tool_result_ids():
    """All 4 tool_result blocks reference the correct tool_use_ids."""
    messages = _load_real_messages()
    result = convert_messages_to_google(messages)
    expected_tool_result_ids = [
        "toolu_01UqpdeuMtRAfShXJjZnM1xr",
        "toolu_01TfGJfs9sTn2hZnG9DscBcr",
        "toolu_0186eQgzhNNQmxwC5NmvsaHC",
        "toolu_01783z1Lrhbs38GvsnvGEX8o",
    ]
    actual_ids = []
    for content in result:
        for part in content.parts:
            if part.function_response:
                actual_ids.append(part.function_response.name)
    assert actual_ids == expected_tool_result_ids


def test_convert_real_messages_write_and_commit_args():
    """Last tool_use (write_and_commit_file) has correct args with file content."""
    messages = _load_real_messages()
    result = convert_messages_to_google(messages)
    # 8th message (index 7) is assistant with write_and_commit_file
    msg = result[7]
    fc = msg.parts[1].function_call
    assert fc.name == "write_and_commit_file"
    assert fc.args == {
        "file_path": "services/anthropic/test_client.py",
        "file_content": "import pytest\nfrom unittest.mock import patch, MagicMock\n\nfrom anthropic import Anthropic\n",
    }


def test_convert_real_messages_last_tool_result_content():
    """Last tool_result has exact success message."""
    messages = _load_real_messages()
    result = convert_messages_to_google(messages)
    msg = result[8]
    fr = msg.parts[0].function_response
    assert fr.response == {
        "result": "Content replaced in the file: services/anthropic/test_client.py successfully."
    }
