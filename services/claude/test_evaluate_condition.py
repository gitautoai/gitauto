# pylint: disable=redefined-outer-name,unused-argument
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


@pytest.fixture
def mock_insert_llm_request():
    with patch("services.claude.evaluate_condition.insert_llm_request") as mock:
        yield mock


class TestEvaluateCondition:
    def test_returns_true_with_reason(self, mock_claude, mock_insert_llm_request):
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"result": true, "reason": "has business logic"}')
        ]
        mock_claude.messages.create.return_value = mock_response

        result = evaluate_condition(
            content="class Calculator { add(a, b) { return a + b; } }",
            system_prompt="Return true if this code should have unit tests.",
            usage_id=42,
            created_by="tester",
        )

        assert result == EvaluationResult(True, "has business logic")
        mock_insert_llm_request.assert_called_once()
        call_kwargs = mock_insert_llm_request.call_args.kwargs
        assert call_kwargs["usage_id"] == 42
        assert call_kwargs["created_by"] == "tester"
        assert call_kwargs["provider"] == "claude"
        assert call_kwargs["model_id"] == "claude-opus-4-7"

    def test_returns_false_with_reason(self, mock_claude, mock_insert_llm_request):
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"result": false, "reason": "only imports"}')
        ]
        mock_claude.messages.create.return_value = mock_response

        result = evaluate_condition(
            content="import React from 'react';",
            system_prompt="Return true if this code contains business logic.",
            usage_id=0,
            created_by="tester",
        )

        assert result == EvaluationResult(False, "only imports")
        mock_insert_llm_request.assert_called_once()
        assert mock_insert_llm_request.call_args.kwargs["usage_id"] == 0

    def test_returns_empty_input_for_empty_content(self, mock_insert_llm_request):
        result = evaluate_condition(
            content="",
            system_prompt="test prompt",
            usage_id=1,
            created_by="tester",
        )
        assert result == EvaluationResult(False, "empty input")
        mock_insert_llm_request.assert_not_called()

    def test_returns_empty_input_for_empty_prompt(self, mock_insert_llm_request):
        result = evaluate_condition(
            content="test content",
            system_prompt="",
            usage_id=1,
            created_by="tester",
        )
        assert result == EvaluationResult(False, "empty input")
        mock_insert_llm_request.assert_not_called()

    def test_returns_evaluation_failed_on_exception(
        self, mock_claude, mock_insert_llm_request
    ):
        mock_claude.messages.create.side_effect = RuntimeError("API Error")

        result = evaluate_condition(
            content="test content",
            system_prompt="test prompt",
            usage_id=1,
            created_by="tester",
        )

        assert result == EvaluationResult(False, "evaluation failed")
        mock_insert_llm_request.assert_not_called()

    def test_returns_evaluation_failed_on_invalid_json(
        self, mock_claude, mock_insert_llm_request
    ):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not valid json")]
        mock_claude.messages.create.return_value = mock_response

        result = evaluate_condition(
            content="test content",
            system_prompt="test prompt",
            usage_id=1,
            created_by="tester",
        )

        assert result == EvaluationResult(False, "evaluation failed")

    def test_uses_opus_47_model(self, mock_claude, mock_insert_llm_request):
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"result": true, "reason": "testable"}')
        ]
        mock_claude.messages.create.return_value = mock_response

        evaluate_condition(
            content="code",
            system_prompt="Check this.",
            usage_id=1,
            created_by="tester",
        )

        call_args = mock_claude.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-opus-4-7"

    def test_uses_structured_output_schema(self, mock_claude, mock_insert_llm_request):
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"result": true, "reason": "testable"}')
        ]
        mock_claude.messages.create.return_value = mock_response

        evaluate_condition(
            content="code",
            system_prompt="Check this code.",
            usage_id=1,
            created_by="tester",
        )

        call_args = mock_claude.messages.create.call_args
        assert call_args.kwargs["system"] == "Check this code."
        assert call_args.kwargs["output_config"] == {"format": RESPONSE_SCHEMA}

    def test_call_kwargs_do_not_include_temperature(
        self, mock_claude, mock_insert_llm_request
    ):
        """Opus 4.7 deprecated temperature (AGENT-3HG-3J1 cluster on 2026-04-19).
        Including it raises BadRequestError 400."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"result": true, "reason": "testable"}')
        ]
        mock_claude.messages.create.return_value = mock_response

        evaluate_condition(
            content="code",
            system_prompt="check",
            usage_id=1,
            created_by="tester",
        )

        call_args = mock_claude.messages.create.call_args
        assert set(call_args.kwargs.keys()) == {
            "model",
            "max_tokens",
            "system",
            "messages",
            "output_config",
        }


@pytest.mark.skip(reason="Integration test - calls real API")
def test_integration_returns_true_for_testable_code():
    eval_result = evaluate_condition(
        content="def calculate_total(items): return sum(item.price for item in items)",
        system_prompt="Decide if this code needs unit tests.",
        usage_id=0,
        created_by="integration-test",
    )
    assert eval_result.result is True
    assert isinstance(eval_result.reason, str)
    assert len(eval_result.reason) > 0


@pytest.mark.skip(reason="Integration test - calls real API")
def test_integration_returns_false_for_non_testable_code():
    eval_result = evaluate_condition(
        content="from .models import User, Order, Product",
        system_prompt="Decide if this code needs unit tests.",
        usage_id=0,
        created_by="integration-test",
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
        usage_id=0,
        created_by="integration-test",
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
        usage_id=0,
        created_by="integration-test",
    )
    assert eval_result.result is False
    assert isinstance(eval_result.reason, str)
    assert len(eval_result.reason) > 0
