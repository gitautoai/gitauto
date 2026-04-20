# pylint: disable=redefined-outer-name
from unittest.mock import MagicMock, patch

import pytest

from services.claude.evaluate_condition import (
    RESPONSE_SCHEMA,
    EvaluationResult,
    evaluate_condition,
)
from utils.prompts.should_test_file import SHOULD_TEST_FILE_PROMPT


@pytest.fixture
def mock_claude():
    with patch("services.claude.evaluate_condition.claude") as mock:
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

        assert result == EvaluationResult(True, "has business logic")

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

        assert result == EvaluationResult(False, "only imports")

    def test_returns_empty_input_for_empty_content(self):
        result = evaluate_condition(content="", system_prompt="test prompt")
        assert result == EvaluationResult(False, "empty input")

    def test_returns_empty_input_for_empty_prompt(self):
        result = evaluate_condition(content="test content", system_prompt="")
        assert result == EvaluationResult(False, "empty input")

    def test_returns_evaluation_failed_on_exception(self, mock_claude):
        mock_claude.beta.messages.create.side_effect = RuntimeError("API Error")

        result = evaluate_condition(content="test content", system_prompt="test prompt")

        assert result == EvaluationResult(False, "evaluation failed")

    def test_returns_evaluation_failed_on_invalid_json(self, mock_claude):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not valid json")]
        mock_claude.beta.messages.create.return_value = mock_response

        result = evaluate_condition(content="test content", system_prompt="test prompt")

        assert result == EvaluationResult(False, "evaluation failed")

    def test_uses_opus_47_model(self, mock_claude):
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"result": true, "reason": "testable"}')
        ]
        mock_claude.beta.messages.create.return_value = mock_response

        evaluate_condition(content="code", system_prompt="Check this.")

        call_args = mock_claude.beta.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-opus-4-7"

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
        assert call_args.kwargs["output_config"] == {"format": RESPONSE_SCHEMA}

    def test_call_kwargs_do_not_include_temperature(self, mock_claude):
        """Opus 4.7 deprecated temperature (AGENT-3HG-3J1 cluster on 2026-04-19).
        Including it raises BadRequestError 400."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"result": true, "reason": "testable"}')
        ]
        mock_claude.beta.messages.create.return_value = mock_response

        evaluate_condition(content="code", system_prompt="check")

        call_args = mock_claude.beta.messages.create.call_args
        assert set(call_args.kwargs.keys()) == {
            "model",
            "max_tokens",
            "system",
            "messages",
            "betas",
            "output_config",
        }


@pytest.mark.skip(reason="Integration test - calls real API")
def test_integration_returns_true_for_testable_code():
    eval_result = evaluate_condition(
        content="def calculate_total(items): return sum(item.price for item in items)",
        system_prompt="Decide if this code needs unit tests.",
    )
    assert eval_result.result is True
    assert isinstance(eval_result.reason, str)
    assert len(eval_result.reason) > 0


@pytest.mark.skip(reason="Integration test - calls real API")
def test_integration_returns_false_for_non_testable_code():
    eval_result = evaluate_condition(
        content="from .models import User, Order, Product",
        system_prompt="Decide if this code needs unit tests.",
    )
    assert eval_result.result is False
    assert isinstance(eval_result.reason, str)
    assert len(eval_result.reason) > 0


@pytest.mark.skip(reason="Integration test - calls real API")
def test_integration_returns_false_for_graphql_document_definition():
    gql_document = """import gql from 'graphql-tag';

gql`
  mutation generateId($type: IdType!) {
    generateId(type: $type)
  }
`;
"""
    eval_result = evaluate_condition(
        content=f"File path: src/models/graphql/operation/document/generateId.ts\n\nContent:\n{gql_document}",
        system_prompt=SHOULD_TEST_FILE_PROMPT,
    )
    assert eval_result.result is False
    assert isinstance(eval_result.reason, str)
    assert len(eval_result.reason) > 0


@pytest.mark.skip(reason="Integration test - calls real API")
def test_integration_returns_false_for_untestable_php_script():
    php_script = """<?php

require_once('import_export.inc');

header('Content-type: application/json');

session_start();
if (!isset($_SESSION['login_id']) || $_SESSION['login_id'] == '') {
    print '{"status": "error", "msg":"セッションが切れています。再度ログインの上、操作してください。"}' . "\\n";
    exit;
}

$class = new ImportExport();
$class->export();
"""
    eval_result = evaluate_condition(
        content=f"File path: web/maintenance/get_json_pile_detail_csv.php\n\nContent:\n{php_script}",
        system_prompt=SHOULD_TEST_FILE_PROMPT,
    )
    assert eval_result.result is False
    assert isinstance(eval_result.reason, str)
    assert len(eval_result.reason) > 0
