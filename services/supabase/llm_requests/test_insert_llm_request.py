import json
from unittest.mock import Mock, patch
from services.supabase.llm_requests.insert_llm_request import insert_llm_request


@patch("services.supabase.llm_requests.insert_llm_request.supabase")
@patch("services.supabase.llm_requests.insert_llm_request.calculate_costs")
def test_insert_llm_request_success(mock_calculate_costs, mock_supabase):
    mock_calculate_costs.return_value = (0.001, 0.005)
    mock_result = Mock()
    mock_result.data = [{"id": 1}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = (
        mock_result
    )

    input_messages = [{"role": "user", "content": "test"}]
    output_message = {"role": "assistant", "content": "response"}

    result = insert_llm_request(
        usage_id=123,
        provider="claude",
        model_id="claude-3-7-sonnet-latest",
        input_messages=input_messages,
        input_tokens=10,
        output_message=output_message,
        output_tokens=5,
        response_time_ms=1000,
        created_by="test",
    )

    assert result == {"id": 1}
    mock_calculate_costs.assert_called_once_with(
        "claude", "claude-3-7-sonnet-latest", 10, 5
    )

    expected_data = {
        "usage_id": 123,
        "provider": "claude",
        "model_id": "claude-3-7-sonnet-latest",
        "input_content": json.dumps(input_messages, ensure_ascii=False),
        "input_length": len(json.dumps(input_messages, ensure_ascii=False)),
        "input_tokens": 10,
        "input_cost_usd": 0.001,
        "output_content": json.dumps(output_message, ensure_ascii=False),
        "output_length": len(json.dumps(output_message, ensure_ascii=False)),
        "output_tokens": 5,
        "output_cost_usd": 0.005,
        "total_cost_usd": 0.006,
        "response_time_ms": 1000,
        "error_message": None,
        "created_by": "test",
        "updated_by": "test",
    }

    mock_supabase.table.return_value.insert.assert_called_once_with(expected_data)


@patch("services.supabase.llm_requests.insert_llm_request.supabase")
def test_insert_llm_request_database_error(mock_supabase):
    mock_supabase.table().insert().execute.side_effect = Exception("Database error")

    result = insert_llm_request(
        usage_id=123,
        provider="claude",
        model_id="claude-3-7-sonnet-latest",
        input_messages=[{"role": "user", "content": "test"}],
        input_tokens=10,
        output_message={"role": "assistant", "content": "response"},
        output_tokens=5,
    )

    assert result is None
