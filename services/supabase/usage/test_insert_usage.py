from unittest.mock import Mock, patch
import pytest
from services.supabase.usage.insert_usage import insert_usage, Trigger
from tests.constants import INSTALLATION_ID


@patch("services.supabase.usage.insert_usage.supabase")
@patch("services.supabase.usage.insert_usage.UsageInsert")
def test_insert_usage_success_with_pr_number(mock_usage_insert, mock_supabase):
    mock_usage_data = Mock()
    mock_usage_data.model_dump.return_value = {"test": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    mock_execute.return_value = (None, [{"id": 123}])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table
    
    result = insert_usage(
        owner_id=456,
        owner_type="Organization",
        owner_name="test-owner",
        repo_id=789,
        repo_name="test-repo",
        issue_number=1,
        user_id=101,
        installation_id=INSTALLATION_ID,
        source="github",
        trigger="issue_comment",
        pr_number=42
    )
    
    assert result == 123
    mock_usage_insert.assert_called_once_with(
        owner_id=456,
        owner_type="Organization",
        owner_name="test-owner",
        repo_id=789,
        repo_name="test-repo",
        issue_number=1,
        user_id=101,
        installation_id=INSTALLATION_ID,
        source="github",
        trigger="issue_comment",
        pr_number=42
    )
    mock_usage_data.model_dump.assert_called_once_with(exclude_none=True)
    mock_supabase.table.assert_called_once_with(table_name="usage")
    mock_table.insert.assert_called_once_with(json={"test": "data"})
    mock_insert.execute.assert_called_once()


@patch("services.supabase.usage.insert_usage.supabase")
@patch("services.supabase.usage.insert_usage.UsageInsert")
def test_insert_usage_success_without_pr_number(mock_usage_insert, mock_supabase):
    mock_usage_data = Mock()
    mock_usage_data.model_dump.return_value = {"test": "data", "pr_number": None}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    mock_execute.return_value = (None, [{"id": 456}])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table
    
    result = insert_usage(
        owner_id=123,
        owner_type="User",
        owner_name="individual-user",
        repo_id=456,
        repo_name="personal-repo",
        issue_number=5,
        user_id=789,
        installation_id=INSTALLATION_ID,
        source="webhook",
        trigger="issue_label"
    )
    
    assert result == 456
    mock_usage_insert.assert_called_once_with(
        owner_id=123,
        owner_type="User",
        owner_name="individual-user",
        repo_id=456,
        repo_name="personal-repo",
        issue_number=5,
        user_id=789,
        installation_id=INSTALLATION_ID,
        source="webhook",
        trigger="issue_label",
        pr_number=None
    )
    mock_usage_data.model_dump.assert_called_once_with(exclude_none=True)
    mock_supabase.table.assert_called_once_with(table_name="usage")
    mock_table.insert.assert_called_once_with(json={"test": "data", "pr_number": None})
    mock_insert.execute.assert_called_once()


@patch("services.supabase.usage.insert_usage.supabase")
@patch("services.supabase.usage.insert_usage.UsageInsert")
def test_insert_usage_all_trigger_types(mock_usage_insert, mock_supabase):
    mock_usage_data = Mock()
    mock_usage_data.model_dump.return_value = {"trigger": "test"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    mock_execute.return_value = (None, [{"id": 999}])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table
    
    triggers = ["issue_label", "issue_comment", "review_comment", "test_failure", "pr_checkbox", "pr_merge"]
    
    for trigger in triggers:
        result = insert_usage(
            owner_id=1,
            owner_type="Organization",
            owner_name="test",
            repo_id=1,
            repo_name="test",
            issue_number=1,
            user_id=1,
            installation_id=INSTALLATION_ID,
            source="test",
            trigger=trigger,
            pr_number=1
        )
        assert result == 999


@patch("services.supabase.usage.insert_usage.supabase")
@patch("services.supabase.usage.insert_usage.UsageInsert")
def test_insert_usage_with_zero_values(mock_usage_insert, mock_supabase):
    mock_usage_data = Mock()
    mock_usage_data.model_dump.return_value = {"id": 0}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    mock_execute.return_value = (None, [{"id": 0}])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table
    
    result = insert_usage(
        owner_id=0,
        owner_type="",
        owner_name="",
        repo_id=0,
        repo_name="",
        issue_number=0,
        user_id=0,
        installation_id=0,
        source="",
        trigger="issue_comment",
        pr_number=0
    )
    
    assert result == 0


@patch("services.supabase.usage.insert_usage.supabase")
@patch("services.supabase.usage.insert_usage.UsageInsert")
def test_insert_usage_supabase_error_raises_exception(mock_usage_insert, mock_supabase):
    mock_usage_data = Mock()
    mock_usage_data.model_dump.return_value = {"test": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = Mock()
    mock_insert = Mock()
    mock_insert.execute.side_effect = Exception("Database connection failed")
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table
    
    with pytest.raises(Exception, match="Database connection failed"):
        insert_usage(
            owner_id=1,
            owner_type="Organization",
            owner_name="test",
            repo_id=1,
            repo_name="test",
            issue_number=1,
            user_id=1,
            installation_id=INSTALLATION_ID,
            source="test",
            trigger="issue_comment"
        )


@patch("services.supabase.usage.insert_usage.supabase")
@patch("services.supabase.usage.insert_usage.UsageInsert")
def test_insert_usage_usage_insert_error_raises_exception(mock_usage_insert, mock_supabase):
    mock_usage_insert.side_effect = ValueError("Invalid usage data")
    
    with pytest.raises(ValueError, match="Invalid usage data"):
        insert_usage(
            owner_id=1,
            owner_type="Organization",
            owner_name="test",
            repo_id=1,
            repo_name="test",
            issue_number=1,
            user_id=1,
            installation_id=INSTALLATION_ID,
            source="test",
            trigger="issue_comment"
        )


@patch("services.supabase.usage.insert_usage.supabase")
@patch("services.supabase.usage.insert_usage.UsageInsert")
def test_insert_usage_model_dump_error_raises_exception(mock_usage_insert, mock_supabase):
    mock_usage_data = Mock()
    mock_usage_data.model_dump.side_effect = AttributeError("model_dump failed")
    mock_usage_insert.return_value = mock_usage_data
    
    with pytest.raises(AttributeError, match="model_dump failed"):
        insert_usage(
            owner_id=1,
            owner_type="Organization",
            owner_name="test",
            repo_id=1,
            repo_name="test",
            issue_number=1,
            user_id=1,
            installation_id=INSTALLATION_ID,
            source="test",
            trigger="issue_comment"
        )


@patch("services.supabase.usage.insert_usage.supabase")
@patch("services.supabase.usage.insert_usage.UsageInsert")
def test_insert_usage_cast_error_raises_exception(mock_usage_insert, mock_supabase):
    mock_usage_data = Mock()
    mock_usage_data.model_dump.return_value = {"test": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    mock_execute.return_value = (None, [{}])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table
    
    with pytest.raises(KeyError):
        insert_usage(
            owner_id=1,
            owner_type="Organization",
            owner_name="test",
            repo_id=1,
            repo_name="test",
            issue_number=1,
            user_id=1,
            installation_id=INSTALLATION_ID,
            source="test",
            trigger="issue_comment"
        )


@patch("services.supabase.usage.insert_usage.supabase")
@patch("services.supabase.usage.insert_usage.UsageInsert")
def test_insert_usage_empty_response_data_raises_exception(mock_usage_insert, mock_supabase):
    mock_usage_data = Mock()
    mock_usage_data.model_dump.return_value = {"test": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    mock_execute.return_value = (None, [])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table
    
    with pytest.raises(IndexError):
        insert_usage(
            owner_id=1,
            owner_type="Organization",
            owner_name="test",
            repo_id=1,
            repo_name="test",
            issue_number=1,
            user_id=1,
            installation_id=INSTALLATION_ID,
            source="test",
            trigger="issue_comment"
        )


@patch("services.supabase.usage.insert_usage.supabase")
@patch("services.supabase.usage.insert_usage.UsageInsert")
def test_insert_usage_large_values(mock_usage_insert, mock_supabase):
    mock_usage_data = Mock()
    mock_usage_data.model_dump.return_value = {"large": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()
    mock_execute.return_value = (None, [{"id": 2147483647}])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table
    
    result = insert_usage(
        owner_id=2147483647,
        owner_type="Organization" * 100,
        owner_name="test-owner" * 100,
        repo_id=2147483647,
        repo_name="test-repo" * 100,
        issue_number=2147483647,
        user_id=2147483647,
        installation_id=2147483647,
        source="github" * 100,
        trigger="issue_comment",
        pr_number=2147483647
    )
    
    assert result == 2147483647
