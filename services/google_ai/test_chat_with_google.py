# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import json
from pathlib import Path
from typing import cast
from unittest.mock import Mock, patch

import pytest
from anthropic.types import MessageParam, ToolUnionParam
from google.genai import errors as google_errors

from constants.models import GoogleModelId
from services.google_ai.chat_with_google import chat_with_google

TOOLS_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "real_tools_for_setup.json"


def _mock_text_response(text, prompt_tokens=20, candidates_tokens=15):
    """Build a mock Google GenerateContentResponse with a text part."""
    part = Mock()
    part.text = text
    part.function_call = None

    candidate = Mock()
    candidate.content = Mock()
    candidate.content.parts = [part]

    response = Mock()
    response.candidates = [candidate]
    response.usage_metadata = Mock(
        prompt_token_count=prompt_tokens, candidates_token_count=candidates_tokens
    )
    return response


def _mock_tool_call_response(
    text, fc_name, fc_args, fc_id="toolu_abc123", prompt_tokens=30, candidates_tokens=25
):
    """Build a mock Google GenerateContentResponse with text + function_call."""
    text_part = Mock()
    text_part.text = text
    text_part.function_call = None

    fc_part = Mock()
    fc_part.text = None
    fc_part.function_call = Mock()
    fc_part.function_call.name = fc_name
    fc_part.function_call.args = fc_args
    fc_part.function_call.id = fc_id

    candidate = Mock()
    candidate.content = Mock()
    candidate.content.parts = [text_part, fc_part]

    response = Mock()
    response.candidates = [candidate]
    response.usage_metadata = Mock(
        prompt_token_count=prompt_tokens, candidates_token_count=candidates_tokens
    )
    return response


@patch("services.google_ai.chat_with_google.insert_llm_request")
@patch("services.google_ai.chat_with_google.get_google_ai_client")
def test_text_response(mock_get_client, mock_insert):
    """Text-only response returns correct assistant message and token counts."""
    mock_insert.return_value = {"total_cost_usd": 0.0}
    mock_client = Mock()
    mock_client.models.generate_content.return_value = _mock_text_response(
        "Hello! How can I help?", prompt_tokens=20, candidates_tokens=15
    )
    mock_client.models.count_tokens.return_value = Mock(total_tokens=1)
    mock_get_client.return_value = mock_client

    messages = cast(list[MessageParam], [{"role": "user", "content": "Hello"}])
    tools: list[ToolUnionParam] = []

    result = chat_with_google(
        messages=messages,
        system_content="You are a helpful assistant.",
        tools=tools,
        model_id=GoogleModelId.GEMMA_4_31B,
        usage_id=123,
        created_by="4:test-user",
    )

    assert result.assistant_message == {
        "role": "assistant",
        "content": [{"type": "text", "text": "Hello! How can I help?"}],
    }
    assert not result.tool_calls
    assert result.token_input == 20
    assert result.token_output == 15
    assert result.cost_usd == 0.0

    mock_insert.assert_called_once()
    call_kwargs = mock_insert.call_args[1]
    assert call_kwargs["usage_id"] == 123
    assert call_kwargs["provider"] == "google"
    assert call_kwargs["model_id"] == "gemma-4-31b-it"
    assert call_kwargs["input_tokens"] == 20
    assert call_kwargs["output_tokens"] == 15
    assert call_kwargs["system_prompt"] == "You are a helpful assistant."


@patch("services.google_ai.chat_with_google.insert_llm_request")
@patch("services.google_ai.chat_with_google.get_google_ai_client")
def test_tool_call_response(mock_get_client, mock_insert):
    """Response with text + function_call returns tool_calls and correct message."""
    mock_insert.return_value = {"total_cost_usd": 0.05}
    mock_client = Mock()
    mock_client.models.generate_content.return_value = _mock_tool_call_response(
        text="I'll read that file.",
        fc_name="get_remote_file_content",
        fc_args={"file_path": "README.md"},
        fc_id="toolu_abc123",
        prompt_tokens=30,
        candidates_tokens=25,
    )
    mock_client.models.count_tokens.return_value = Mock(total_tokens=1)
    mock_get_client.return_value = mock_client

    messages = cast(list[MessageParam], [{"role": "user", "content": "Read README.md"}])
    tools = cast(
        list[ToolUnionParam],
        [
            {
                "name": "get_remote_file_content",
                "description": "Get file content",
                "input_schema": {"type": "object", "properties": {}},
            }
        ],
    )

    result = chat_with_google(
        messages=messages,
        system_content="You are a helpful assistant.",
        tools=tools,
        model_id=GoogleModelId.GEMINI_2_5_FLASH,
        usage_id=456,
        created_by="4:test-user",
    )

    assert result.assistant_message == {
        "role": "assistant",
        "content": [
            {"type": "text", "text": "I'll read that file."},
            {
                "type": "tool_use",
                "id": "toolu_abc123",
                "name": "get_remote_file_content",
                "input": {"file_path": "README.md"},
            },
        ],
    }
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].id == "toolu_abc123"
    assert result.tool_calls[0].name == "get_remote_file_content"
    assert result.tool_calls[0].args == {"file_path": "README.md"}
    assert result.token_input == 30
    assert result.token_output == 25


@patch("services.google_ai.chat_with_google.insert_llm_request")
@patch("services.google_ai.chat_with_google.get_google_ai_client")
def test_no_usage_metadata(mock_get_client, mock_insert):
    """When usage_metadata is None, token counts default to 0."""
    mock_insert.return_value = {"total_cost_usd": 0.0}
    response = _mock_text_response("Response")
    response.usage_metadata = None
    mock_client = Mock()
    mock_client.models.generate_content.return_value = response
    mock_client.models.count_tokens.return_value = Mock(total_tokens=1)
    mock_get_client.return_value = mock_client

    result = chat_with_google(
        messages=cast(list[MessageParam], [{"role": "user", "content": "test"}]),
        system_content="assistant",
        tools=[],
        model_id=GoogleModelId.GEMMA_4_31B,
        usage_id=789,
        created_by="4:test-user",
    )

    assert result.token_input == 0
    assert result.token_output == 0


@patch("services.google_ai.chat_with_google.insert_llm_request")
@patch("services.google_ai.chat_with_google.get_google_ai_client")
def test_empty_candidates(mock_get_client, mock_insert):
    """When candidates list is empty, returns empty content."""
    mock_insert.return_value = {"total_cost_usd": 0.0}
    response = Mock()
    response.candidates = []
    response.usage_metadata = Mock(prompt_token_count=10, candidates_token_count=0)
    mock_client = Mock()
    mock_client.models.generate_content.return_value = response
    mock_client.models.count_tokens.return_value = Mock(total_tokens=1)
    mock_get_client.return_value = mock_client

    result = chat_with_google(
        messages=cast(list[MessageParam], [{"role": "user", "content": "test"}]),
        system_content="assistant",
        tools=[],
        model_id=GoogleModelId.GEMMA_4_31B,
        usage_id=101,
        created_by="4:test-user",
    )

    # No parts → content_list is empty → falls back to empty content_text
    assert result.assistant_message == {"role": "assistant", "content": ""}
    assert not result.tool_calls


@patch("services.google_ai.chat_with_google.insert_llm_request")
@patch("services.google_ai.chat_with_google.get_google_ai_client")
def test_function_call_without_id_generates_one(mock_get_client, mock_insert):
    """When function_call has no id, a toolu_ prefixed id is generated."""
    fc_part = Mock()
    fc_part.text = None
    fc_part.function_call = Mock()
    fc_part.function_call.name = "run_command"
    fc_part.function_call.args = {"command": "ls"}
    fc_part.function_call.id = None  # No id from Google

    candidate = Mock()
    candidate.content = Mock()
    candidate.content.parts = [fc_part]

    response = Mock()
    response.candidates = [candidate]
    response.usage_metadata = Mock(prompt_token_count=10, candidates_token_count=5)

    mock_client = Mock()
    mock_client.models.generate_content.return_value = response
    mock_client.models.count_tokens.return_value = Mock(total_tokens=1)
    mock_get_client.return_value = mock_client

    result = chat_with_google(
        messages=cast(list[MessageParam], [{"role": "user", "content": "list files"}]),
        system_content="assistant",
        tools=cast(
            list[ToolUnionParam],
            [
                {
                    "name": "run_command",
                    "description": "Run a command",
                    "input_schema": {"type": "object", "properties": {}},
                }
            ],
        ),
        model_id=GoogleModelId.GEMMA_4_31B,
        usage_id=202,
        created_by="4:test-user",
    )

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].id.startswith("toolu_")
    assert len(result.tool_calls[0].id) == 30  # "toolu_" + 24 hex chars
    assert result.tool_calls[0].name == "run_command"
    assert result.tool_calls[0].args == {"command": "ls"}


# --- Sociable integration tests: real Google AI API calls ---
# Gemma 4 on Google AI Studio is free tier as of 2026-04, but skip by default in case that changes.


def _load_real_tools():
    with open(TOOLS_FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.skip(
    reason="Real LLM call — run manually with pytest --no-header -rN -k integration"
)
@pytest.mark.integration
@patch("services.google_ai.chat_with_google.insert_llm_request")
def test_integration_text_response(mock_insert):
    """Real API call with Gemma 4 returns a text response."""
    messages = cast(
        list[MessageParam],
        [{"role": "user", "content": "Reply with exactly: PONG"}],
    )
    tools: list[ToolUnionParam] = []

    result = chat_with_google(
        messages=messages,
        system_content="You are a helpful assistant. Follow instructions exactly.",
        tools=tools,
        model_id=GoogleModelId.GEMMA_4_31B,
        usage_id=9001,
        created_by="4:integration-test",
    )

    assert result.assistant_message["role"] == "assistant"
    assert isinstance(result.assistant_message["content"], (str, list))
    assert not result.tool_calls
    assert result.token_input > 0
    assert result.token_output > 0

    mock_insert.assert_called_once()
    call_kwargs = mock_insert.call_args[1]
    assert call_kwargs["provider"] == "google"
    assert call_kwargs["model_id"] == "gemma-4-31b-it"


@pytest.mark.skip(
    reason="Real LLM call — run manually with pytest --no-header -rN -k integration"
)
@pytest.mark.integration
@patch("services.google_ai.chat_with_google.insert_llm_request")
def test_integration_tool_call_with_real_tools(mock_insert):
    """Real API call with 18 real tool definitions triggers a function call."""
    real_tools = cast(list[ToolUnionParam], _load_real_tools())
    messages = cast(
        list[MessageParam],
        [{"role": "user", "content": "Read the file at path README.md"}],
    )

    result = chat_with_google(
        messages=messages,
        system_content="You are a coding assistant. Use the provided tools to complete tasks.",
        tools=real_tools,
        model_id=GoogleModelId.GEMMA_4_31B,
        usage_id=9002,
        created_by="4:integration-test",
    )

    assert result.assistant_message["role"] == "assistant"
    assert result.token_input > 0
    assert result.token_output > 0
    # Model should call a file-reading tool
    assert len(result.tool_calls) >= 1
    tool_names = [tc.name for tc in result.tool_calls]
    assert any(
        name in tool_names for name in ("get_local_file_content", "query_file")
    ), f"Expected a file-reading tool call, got: {tool_names}"
    # Each tool call has a valid id
    for tc in result.tool_calls:
        assert tc.id
        assert tc.name


@patch("services.google_ai.chat_with_google.insert_llm_request")
@patch("services.google_ai.chat_with_google.get_google_ai_client")
def test_429_is_not_retried_locally_bubbles_to_handle_exceptions(
    mock_get_client, mock_insert
):
    """Rate-limit retry is handled at the handle_exceptions layer (via
    get_rate_limit_retry_after), not inside chat_with_google. A single 429 from
    the SDK should propagate unchanged — the decorator picks it up, sleeps the
    retry-after hint, and re-invokes the wrapper. Verify chat_with_google itself
    does not swallow or loop on 429."""
    err = google_errors.ClientError(
        code=429,
        response_json={
            "error": {
                "code": 429,
                "message": "quota exceeded. Please retry in 5s.",
                "status": "RESOURCE_EXHAUSTED",
            }
        },
    )
    client = Mock()
    client.models.generate_content.side_effect = err
    client.models.count_tokens.return_value = Mock(total_tokens=1)
    mock_get_client.return_value = client

    with patch("utils.error.handle_exceptions.time.sleep"):
        with pytest.raises(google_errors.ClientError):
            chat_with_google(
                messages=cast(list[MessageParam], [{"role": "user", "content": "hi"}]),
                system_content="sys",
                tools=[],
                model_id=GoogleModelId.GEMMA_4_31B,
                usage_id=1,
                created_by="1:t",
            )
    # handle_exceptions retries up to TRANSIENT_MAX_ATTEMPTS=3 times before giving up, so the SDK gets called 3 times (honoring the 5s hint between each).
    assert client.models.generate_content.call_count == 3
    mock_insert.assert_not_called()
