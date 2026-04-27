# pyright: reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportArgumentType=false, reportOptionalIterable=false
import json
from pathlib import Path
from typing import cast

from anthropic.types import MessageParam

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
    # name must be function name (matching FunctionDeclaration), not tool_use_id
    assert fr.name == "get_remote_file_content"
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
    """All 4 tool_result blocks have correct IDs."""
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
                actual_ids.append(part.function_response.id)
    assert actual_ids == expected_tool_result_ids


def test_function_response_name_matches_function_declaration_name():
    """FunctionResponse.name must be the function name, not tool_use_id.
    Google AI requires FunctionResponse.name to match FunctionDeclaration.name.
    Using tool_use_id as the name causes 400 INVALID_ARGUMENT on the second API call.
    Bug: PR 782 failed because FunctionResponse.name was 'vpfs0f3y' instead of
    'get_local_file_content'."""
    messages = _load_real_messages()
    result = convert_messages_to_google(messages)
    # Expected: function names from the preceding tool_use blocks
    expected_function_names = [
        "get_remote_file_content",
        "get_remote_file_content",
        "get_remote_file_content",
        "write_and_commit_file",
    ]
    actual_names = []
    for content in result:
        for part in content.parts:
            if part.function_response:
                actual_names.append(part.function_response.name)
    assert actual_names == expected_function_names


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


def test_consecutive_user_messages_merged_into_one_content():
    """Sentry AGENT-36R/36K/36N/36P (gitautoai/website 2026-04-16): chat_with_agent emits two consecutive user messages on the first turn (one with the JSON task payload, one with the source code). Anthropic accepts that, Google rejects with 400 INVALID_ARGUMENT because Contents must alternate user/model. The fix merges consecutive same-role messages into one Content with both parts in original order."""
    messages = cast(
        list[MessageParam],
        [
            {"role": "user", "content": "task payload"},
            {"role": "user", "content": "source code"},
            {"role": "assistant", "content": "model reply"},
        ],
    )

    result = convert_messages_to_google(messages)

    assert [c.role for c in result] == ["user", "model"]
    assert [p.text for p in result[0].parts] == ["task payload", "source code"]
    assert [p.text for p in result[1].parts] == ["model reply"]


def test_consecutive_assistant_messages_merged_into_one_content():
    """Mirror of the consecutive-user case: two consecutive assistant messages must merge to a single 'model' Content. Locks the contract symmetrically."""
    messages = cast(
        list[MessageParam],
        [
            {"role": "user", "content": "ask"},
            {"role": "assistant", "content": "thinking"},
            {"role": "assistant", "content": "decided"},
        ],
    )

    result = convert_messages_to_google(messages)

    assert [c.role for c in result] == ["user", "model"]
    assert [p.text for p in result[1].parts] == ["thinking", "decided"]


def test_alternating_messages_unchanged_by_merge_logic():
    """Negative case for the merge: when input already alternates, output should be one Content per input message (no false merging across role boundaries). Guards against an over-eager merge that collapses everything into a single Content."""
    messages = cast(
        list[MessageParam],
        [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
        ],
    )

    result = convert_messages_to_google(messages)

    assert [c.role for c in result] == ["user", "model", "user", "model"]
    assert [c.parts[0].text for c in result] == ["u1", "a1", "u2", "a2"]
