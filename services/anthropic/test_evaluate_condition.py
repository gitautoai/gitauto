from unittest.mock import Mock, patch
from services.anthropic.evaluate_condition import evaluate_condition


def test_evaluate_condition_returns_true():
    with patch("services.anthropic.evaluate_condition.claude") as mock_claude:
        # Mock response for true condition
        mock_response = Mock()
        mock_response.content = [Mock(text="TRUE")]
        mock_claude.messages.create.return_value = mock_response

        result = evaluate_condition(
            content="class Calculator { add(a, b) { return a + b; } }",
            system_prompt="Return true if this code should have unit tests.",
        )

        assert result is True
        mock_claude.messages.create.assert_called_once()


def test_evaluate_condition_returns_false():
    with patch("services.anthropic.evaluate_condition.claude") as mock_claude:
        # Mock response for false condition
        mock_response = Mock()
        mock_response.content = [Mock(text="FALSE")]
        mock_claude.messages.create.return_value = mock_response

        result = evaluate_condition(
            content="import React from 'react';",
            system_prompt="Return true if this code contains business logic.",
        )

        assert result is False


def test_evaluate_condition_mixed_case():
    with patch("services.anthropic.evaluate_condition.claude") as mock_claude:
        # Mock response with mixed case
        mock_response = Mock()
        mock_response.content = [Mock(text="True")]
        mock_claude.messages.create.return_value = mock_response

        result = evaluate_condition(
            content="function test() {}", system_prompt="Check if testable"
        )

        assert result is True


def test_evaluate_condition_with_extra_text():
    with patch("services.anthropic.evaluate_condition.claude") as mock_claude:
        # Mock response with extra text (should still work)
        mock_response = Mock()
        mock_response.content = [Mock(text="The answer is TRUE")]
        mock_claude.messages.create.return_value = mock_response

        result = evaluate_condition(content="test content", system_prompt="test prompt")

        assert result is True


def test_evaluate_condition_invalid_input():
    # Test with empty content
    result = evaluate_condition(content="", system_prompt="test prompt")
    assert result is False

    # Test with empty system prompt
    result = evaluate_condition(content="test content", system_prompt="")
    assert result is False


def test_evaluate_condition_exception_handling():
    with patch("services.anthropic.evaluate_condition.claude") as mock_claude:
        # Mock an exception
        mock_claude.messages.create.side_effect = Exception("API Error")

        result = evaluate_condition(content="test content", system_prompt="test prompt")

        assert result is False


def test_evaluate_condition_ambiguous_response():
    with patch("services.anthropic.evaluate_condition.claude") as mock_claude:
        # Mock response with neither true nor false
        mock_response = Mock()
        mock_response.content = [Mock(text="maybe")]
        mock_claude.messages.create.return_value = mock_response

        result = evaluate_condition(content="test content", system_prompt="test prompt")

        # Should return False when can't determine true/false
        assert result is False
