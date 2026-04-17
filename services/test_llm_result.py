from services.llm_result import LlmResult, ToolCall


def test_tool_call_fields():
    tc = ToolCall(id="call_1", name="my_tool", args={"key": "value"})
    assert tc.id == "call_1"
    assert tc.name == "my_tool"
    assert tc.args == {"key": "value"}


def test_tool_call_none_args():
    tc = ToolCall(id="call_2", name="my_tool", args=None)
    assert tc.args is None


def test_llm_result_fields():
    result = LlmResult(
        assistant_message={"role": "assistant", "content": "hello"},
        tool_calls=[],
        token_input=100,
        token_output=50,
        cost_usd=0.025,
    )
    assert result.assistant_message == {"role": "assistant", "content": "hello"}
    assert not result.tool_calls
    assert result.token_input == 100
    assert result.token_output == 50
    assert result.cost_usd == 0.025


def test_llm_result_with_tool_calls():
    tc = ToolCall(id="call_1", name="read_file", args={"path": "/tmp/foo"})
    result = LlmResult(
        assistant_message={"role": "assistant", "content": ""},
        tool_calls=[tc],
        token_input=200,
        token_output=100,
        cost_usd=0.05,
    )
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "read_file"
