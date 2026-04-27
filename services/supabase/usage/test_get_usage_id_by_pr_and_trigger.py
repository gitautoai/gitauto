from unittest.mock import Mock, patch

from services.supabase.usage.get_usage_id_by_pr_and_trigger import (
    get_usage_id_by_pr_and_trigger,
)


def _build_chain(execute_data):
    mock_supabase = Mock()
    mock_table = Mock()
    mock_select = Mock()
    mock_eq1 = Mock()
    mock_eq2 = Mock()
    mock_eq3 = Mock()
    mock_eq4 = Mock()
    mock_eq5 = Mock()
    mock_limit = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.eq.return_value = mock_eq3
    mock_eq3.eq.return_value = mock_eq4
    mock_eq4.eq.return_value = mock_eq5
    mock_eq5.limit.return_value = mock_limit
    mock_limit.execute.return_value = Mock(data=execute_data)

    return (
        mock_supabase,
        mock_table,
        mock_select,
        mock_eq1,
        mock_eq2,
        mock_eq3,
        mock_eq4,
        mock_eq5,
        mock_limit,
    )


def test_get_usage_id_by_pr_and_trigger_returns_id_when_row_exists():
    chain = _build_chain([{"id": 16084}])
    mock_supabase = chain[0]
    with patch(
        "services.supabase.usage.get_usage_id_by_pr_and_trigger.supabase",
        mock_supabase,
    ):
        result = get_usage_id_by_pr_and_trigger(
            platform="github",
            installation_id=80763246,
            repo_id=279688027,
            pr_number=1159,
            trigger="schedule",
        )

    assert result == 16084
    mock_supabase.table.assert_called_once_with(table_name="usage")
    chain[1].select.assert_called_once_with("id")
    chain[2].eq.assert_called_once_with(column="platform", value="github")
    chain[3].eq.assert_called_once_with(column="installation_id", value=80763246)
    chain[4].eq.assert_called_once_with(column="repo_id", value=279688027)
    chain[5].eq.assert_called_once_with(column="pr_number", value=1159)
    chain[6].eq.assert_called_once_with(column="trigger", value="schedule")
    chain[7].limit.assert_called_once_with(size=1)


def test_get_usage_id_by_pr_and_trigger_returns_none_when_no_row():
    chain = _build_chain([])
    mock_supabase = chain[0]
    with patch(
        "services.supabase.usage.get_usage_id_by_pr_and_trigger.supabase",
        mock_supabase,
    ):
        result = get_usage_id_by_pr_and_trigger(
            platform="github",
            installation_id=1,
            repo_id=2,
            pr_number=3,
            trigger="dashboard",
        )

    assert result is None


def test_get_usage_id_by_pr_and_trigger_returns_int_not_str():
    chain = _build_chain([{"id": "16084"}])
    mock_supabase = chain[0]
    with patch(
        "services.supabase.usage.get_usage_id_by_pr_and_trigger.supabase",
        mock_supabase,
    ):
        result = get_usage_id_by_pr_and_trigger(
            platform="github",
            installation_id=1,
            repo_id=2,
            pr_number=3,
            trigger="schedule",
        )

    assert result == 16084
    assert isinstance(result, int)


def test_get_usage_id_by_pr_and_trigger_swallows_exception():
    with patch(
        "services.supabase.usage.get_usage_id_by_pr_and_trigger.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = RuntimeError("supabase down")

        result = get_usage_id_by_pr_and_trigger(
            platform="github",
            installation_id=1,
            repo_id=2,
            pr_number=3,
            trigger="schedule",
        )

    assert result is None
