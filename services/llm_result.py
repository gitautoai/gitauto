from dataclasses import dataclass

from anthropic.types import MessageParam


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict | None


@dataclass
class LlmResult:
    assistant_message: MessageParam
    tool_calls: list[ToolCall]
    token_input: int
    token_output: int
    cost_usd: float
