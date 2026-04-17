# pyright: reportUnusedVariable=false
from unittest.mock import MagicMock, patch

from services.supabase.llm_requests.get_total_cost_for_pr import get_total_cost_for_pr

MOCK_SUPABASE = "services.supabase.llm_requests.get_total_cost_for_pr.supabase"


@patch(MOCK_SUPABASE)
def test_returns_zero_when_no_usage_records(mock_supabase):
    usage_query = MagicMock()
    usage_query.execute.return_value = MagicMock(data=[])
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value = (
        usage_query
    )

    result = get_total_cost_for_pr("owner", "repo", 1)
    assert result == 0.0


@patch(MOCK_SUPABASE)
def test_sums_costs_across_multiple_usage_ids(mock_supabase):
    # First call: usage table returns 2 usage IDs
    usage_query = MagicMock()
    usage_query.execute.return_value = MagicMock(data=[{"id": 100}, {"id": 200}])

    # Second call: llm_requests table returns costs
    cost_query = MagicMock()
    cost_query.execute.return_value = MagicMock(
        data=[
            {"total_cost_usd": 1.50},
            {"total_cost_usd": 2.30},
            {"total_cost_usd": 0.80},
        ]
    )

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "usage":
            mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value = (
                usage_query
            )
        elif name == "llm_requests":
            mock_table.select.return_value.in_.return_value = cost_query
        return mock_table

    mock_supabase.table.side_effect = table_side_effect

    result = get_total_cost_for_pr("owner", "repo", 42)
    assert result == 4.60


@patch(MOCK_SUPABASE)
def test_returns_zero_when_no_llm_requests(mock_supabase):
    usage_query = MagicMock()
    usage_query.execute.return_value = MagicMock(data=[{"id": 100}])

    cost_query = MagicMock()
    cost_query.execute.return_value = MagicMock(data=[])

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "usage":
            mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value = (
                usage_query
            )
        elif name == "llm_requests":
            mock_table.select.return_value.in_.return_value = cost_query
        return mock_table

    mock_supabase.table.side_effect = table_side_effect

    result = get_total_cost_for_pr("owner", "repo", 42)
    assert result == 0.0
