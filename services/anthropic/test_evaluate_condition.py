# pylint: disable=redefined-outer-name
from unittest.mock import MagicMock, patch

import pytest

from services.anthropic.evaluate_condition import evaluate_condition


@pytest.fixture
def mock_claude():
    with patch("services.anthropic.evaluate_condition.claude") as mock:
        yield mock


class TestEvaluateCondition:
    def test_returns_true_with_reason(self, mock_claude):
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"result": true, "reason": "has business logic"}')
        ]
        mock_claude.beta.messages.create.return_value = mock_response

        result = evaluate_condition(
            content="class Calculator { add(a, b) { return a + b; } }",
            system_prompt="Return true if this code should have unit tests.",
        )

        assert result == (True, "has business logic")

    def test_returns_false_with_reason(self, mock_claude):
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"result": false, "reason": "only imports"}')
        ]
        mock_claude.beta.messages.create.return_value = mock_response

        result = evaluate_condition(
            content="import React from 'react';",
            system_prompt="Return true if this code contains business logic.",
        )

        assert result == (False, "only imports")

    def test_returns_empty_input_for_empty_content(self):
        result = evaluate_condition(content="", system_prompt="test prompt")
        assert result == (False, "empty input")

    def test_returns_empty_input_for_empty_prompt(self):
        result = evaluate_condition(content="test content", system_prompt="")
        assert result == (False, "empty input")

    def test_returns_evaluation_failed_on_exception(self, mock_claude):
        mock_claude.beta.messages.create.side_effect = RuntimeError("API Error")

        result = evaluate_condition(content="test content", system_prompt="test prompt")

        assert result == (False, "evaluation failed")

    def test_returns_evaluation_failed_on_invalid_json(self, mock_claude):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not valid json")]
        mock_claude.beta.messages.create.return_value = mock_response

        result = evaluate_condition(content="test content", system_prompt="test prompt")

        assert result == (False, "evaluation failed")

    def test_uses_structured_output_schema(self, mock_claude):
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"result": true, "reason": "testable"}')
        ]
        mock_claude.beta.messages.create.return_value = mock_response

        evaluate_condition(content="code", system_prompt="Check this code.")

        call_args = mock_claude.beta.messages.create.call_args
        assert call_args.kwargs["system"] == "Check this code."
        assert call_args.kwargs["betas"] == ["structured-outputs-2025-11-13"]
        assert "output_format" in call_args.kwargs


@pytest.mark.skip(reason="Integration test - calls real API")
def test_integration_returns_true_for_testable_code():
    result, reason = evaluate_condition(
        content="def calculate_total(items): return sum(item.price for item in items)",
        system_prompt="Decide if this code needs unit tests.",
    )
    assert result is True
    assert isinstance(reason, str)
    assert len(reason) > 0


@pytest.mark.skip(reason="Integration test - calls real API")
def test_integration_returns_false_for_non_testable_code():
    result, reason = evaluate_condition(
        content="from .models import User, Order, Product",
        system_prompt="Decide if this code needs unit tests.",
    )
    assert result is False
    assert isinstance(reason, str)
    assert len(reason) > 0
