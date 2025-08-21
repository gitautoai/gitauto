from unittest.mock import patch, MagicMock
import pytest
from services.supabase.usage.insert_usage import insert_usage, Trigger
from config import TEST_OWNER_ID, TEST_OWNER_TYPE, TEST_OWNER_NAME, TEST_REPO_ID, TEST_REPO_NAME, TEST_ISSUE_NUMBER, TEST_USER_ID, TEST_INSTALLATION_ID


@pytest.fixture
def mock_supabase_client():
    with patch("services.supabase.usage.insert_usage.supabase") as mock:
        yield mock


@pytest.fixture
def mock_usage_insert():
    with patch("services.supabase.usage.insert_usage.UsageInsert") as mock:
        yield mock


def test_insert_usage_success_with_pr_number(mock_supabase_client, mock_usage_insert):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = {"test": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = [{"id": 123}]
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
    result = insert_usage(
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=TEST_REPO_ID,
        repo_name=TEST_REPO_NAME,
        issue_number=TEST_ISSUE_NUMBER,
        user_id=TEST_USER_ID,
        installation_id=TEST_INSTALLATION_ID,
        source="github",
        trigger="issue_comment",
        pr_number=42
    )
    
    assert result == 123
    mock_usage_insert.assert_called_once_with(
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=TEST_REPO_ID,
        repo_name=TEST_REPO_NAME,
        issue_number=TEST_ISSUE_NUMBER,
        user_id=TEST_USER_ID,
        installation_id=TEST_INSTALLATION_ID,
        source="github",
        trigger="issue_comment",
        pr_number=42
    )
    mock_usage_data.model_dump.assert_called_once_with(exclude_none=True)
    mock_supabase_client.table.assert_called_once_with(table_name="usage")
    mock_table.insert.assert_called_once_with(json={"test": "data"})
    mock_insert.execute.assert_called_once()


def test_insert_usage_success_without_pr_number(mock_supabase_client, mock_usage_insert):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = {"test": "data", "pr_number": None}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = [{"id": 456}]
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
    result = insert_usage(
        owner_id=TEST_OWNER_ID,
        owner_type="User",
        owner_name="individual-user",
        repo_id=TEST_REPO_ID,
        repo_name="personal-repo",
        issue_number=TEST_ISSUE_NUMBER,
        user_id=TEST_USER_ID,
        installation_id=TEST_INSTALLATION_ID,
        source="webhook",
        trigger="issue_label"
    )
    
    assert result == 456
    mock_usage_insert.assert_called_once_with(
        owner_id=TEST_OWNER_ID,
        owner_type="User",
        owner_name="individual-user",
        repo_id=TEST_REPO_ID,
        repo_name="personal-repo",
        issue_number=TEST_ISSUE_NUMBER,
        user_id=TEST_USER_ID,
        installation_id=TEST_INSTALLATION_ID,
        source="webhook",
        trigger="issue_label",
        pr_number=None
    )
    mock_usage_data.model_dump.assert_called_once_with(exclude_none=True)
    mock_supabase_client.table.assert_called_once_with(table_name="usage")
    mock_table.insert.assert_called_once_with(json={"test": "data", "pr_number": None})
    mock_insert.execute.assert_called_once()


@pytest.mark.parametrize(
    "trigger",
    ["issue_label", "issue_comment", "review_comment", "test_failure", "pr_checkbox", "pr_merge"]
)
def test_insert_usage_all_trigger_types(mock_supabase_client, mock_usage_insert, trigger):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = {"trigger": trigger}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = [{"id": 999}]
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
    result = insert_usage(
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=TEST_REPO_ID,
        repo_name=TEST_REPO_NAME,
        issue_number=TEST_ISSUE_NUMBER,
        user_id=TEST_USER_ID,
        installation_id=TEST_INSTALLATION_ID,
        source="test",
        trigger=trigger,
        pr_number=1
    )
    
    assert result == 999


def test_insert_usage_with_zero_values(mock_supabase_client, mock_usage_insert):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = {"id": 0}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = [{"id": 0}]
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
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


def test_insert_usage_supabase_error_raises_exception(mock_supabase_client, mock_usage_insert):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = {"test": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_insert.execute.side_effect = Exception("Database connection failed")
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
    with pytest.raises(Exception, match="Database connection failed"):
        insert_usage(
            owner_id=TEST_OWNER_ID,
            owner_type=TEST_OWNER_TYPE,
            owner_name=TEST_OWNER_NAME,
            repo_id=TEST_REPO_ID,
            repo_name=TEST_REPO_NAME,
            issue_number=TEST_ISSUE_NUMBER,
            user_id=TEST_USER_ID,
            installation_id=TEST_INSTALLATION_ID,
            source="test",
            trigger="issue_comment"
        )


def test_insert_usage_usage_insert_error_raises_exception(mock_supabase_client, mock_usage_insert):
    mock_usage_insert.side_effect = ValueError("Invalid usage data")
    
    with pytest.raises(ValueError, match="Invalid usage data"):
        insert_usage(
            owner_id=TEST_OWNER_ID,
            owner_type=TEST_OWNER_TYPE,
            owner_name=TEST_OWNER_NAME,
            repo_id=TEST_REPO_ID,
            repo_name=TEST_REPO_NAME,
            issue_number=TEST_ISSUE_NUMBER,
            user_id=TEST_USER_ID,
            installation_id=TEST_INSTALLATION_ID,
            source="test",
            trigger="issue_comment"
        )


def test_insert_usage_model_dump_error_raises_exception(mock_supabase_client, mock_usage_insert):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.side_effect = AttributeError("model_dump failed")
    mock_usage_insert.return_value = mock_usage_data
    
    with pytest.raises(AttributeError, match="model_dump failed"):
        insert_usage(
            owner_id=TEST_OWNER_ID,
            owner_type=TEST_OWNER_TYPE,
            owner_name=TEST_OWNER_NAME,
            repo_id=TEST_REPO_ID,
            repo_name=TEST_REPO_NAME,
            issue_number=TEST_ISSUE_NUMBER,
            user_id=TEST_USER_ID,
            installation_id=TEST_INSTALLATION_ID,
            source="test",
            trigger="issue_comment"
        )


def test_insert_usage_cast_error_raises_exception(mock_supabase_client, mock_usage_insert):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = {"test": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = [{}]
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
    with pytest.raises(KeyError):
        insert_usage(
            owner_id=TEST_OWNER_ID,
            owner_type=TEST_OWNER_TYPE,
            owner_name=TEST_OWNER_NAME,
            repo_id=TEST_REPO_ID,
            repo_name=TEST_REPO_NAME,
            issue_number=TEST_ISSUE_NUMBER,
            user_id=TEST_USER_ID,
            installation_id=TEST_INSTALLATION_ID,
            source="test",
            trigger="issue_comment"
        )


def test_insert_usage_empty_response_data_raises_exception(mock_supabase_client, mock_usage_insert):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = {"test": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = []
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
    with pytest.raises(IndexError):
        insert_usage(
            owner_id=TEST_OWNER_ID,
            owner_type=TEST_OWNER_TYPE,
            owner_name=TEST_OWNER_NAME,
            repo_id=TEST_REPO_ID,
            repo_name=TEST_REPO_NAME,
            issue_number=TEST_ISSUE_NUMBER,
            user_id=TEST_USER_ID,
            installation_id=TEST_INSTALLATION_ID,
            source="test",
            trigger="issue_comment"
        )


def test_insert_usage_large_values(mock_supabase_client, mock_usage_insert):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = {"large": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_execute.return_value = (None, [{"id": 2147483647}])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
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


def test_insert_usage_exclude_none_behavior(mock_supabase_client, mock_usage_insert):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = {"key": "value"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_execute.return_value = (None, [{"id": 100}])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
    insert_usage(
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=TEST_REPO_ID,
        repo_name=TEST_REPO_NAME,
        issue_number=TEST_ISSUE_NUMBER,
        user_id=TEST_USER_ID,
        installation_id=TEST_INSTALLATION_ID,
        source="test",
        trigger="issue_comment"
    )
    
    mock_usage_data.model_dump.assert_called_once_with(exclude_none=True)


def test_insert_usage_table_name_parameter(mock_supabase_client, mock_usage_insert):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = {"test": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_execute.return_value = (None, [{"id": 200}])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
    insert_usage(
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=TEST_REPO_ID,
        repo_name=TEST_REPO_NAME,
        issue_number=TEST_ISSUE_NUMBER,
        user_id=TEST_USER_ID,
        installation_id=TEST_INSTALLATION_ID,
        source="test",
        trigger="issue_comment"
    )
    
    mock_supabase_client.table.assert_called_once_with(table_name="usage")


def test_insert_usage_json_parameter(mock_supabase_client, mock_usage_insert):
    test_data = {"specific": "test_data"}
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = test_data
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_execute.return_value = (None, [{"id": 300}])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
    insert_usage(
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=TEST_REPO_ID,
        repo_name=TEST_REPO_NAME,
        issue_number=TEST_ISSUE_NUMBER,
        user_id=TEST_USER_ID,
        installation_id=TEST_INSTALLATION_ID,
        source="test",
        trigger="issue_comment"
    )
    
    mock_table.insert.assert_called_once_with(json=test_data)


def test_insert_usage_return_value_cast(mock_supabase_client, mock_usage_insert):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = {"test": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_execute.return_value = (None, [{"id": "400"}])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
    result = insert_usage(
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=TEST_REPO_ID,
        repo_name=TEST_REPO_NAME,
        issue_number=TEST_ISSUE_NUMBER,
        user_id=TEST_USER_ID,
        installation_id=TEST_INSTALLATION_ID,
        source="test",
        trigger="issue_comment"
    )
    
    assert result == "400"
    assert isinstance(result, str)


@pytest.mark.parametrize(
    "owner_id,owner_type,owner_name,repo_id,repo_name,issue_number,user_id,installation_id,source,trigger,pr_number,expected_id",
    [
        (1, "User", "user1", 10, "repo1", 100, 1000, 10000, "github", "issue_comment", None, 1),
        (2, "Organization", "org1", 20, "repo2", 200, 2000, 20000, "webhook", "issue_label", 50, 2),
        (3, "User", "user2", 30, "repo3", 300, 3000, 30000, "api", "review_comment", 60, 3),
        (4, "Organization", "org2", 40, "repo4", 400, 4000, 40000, "manual", "test_failure", None, 4),
        (5, "User", "user3", 50, "repo5", 500, 5000, 50000, "scheduled", "pr_checkbox", 70, 5),
        (6, "Organization", "org3", 60, "repo6", 600, 6000, 60000, "trigger", "pr_merge", 80, 6),
    ]
)
def test_insert_usage_with_various_parameters(
    mock_supabase_client, mock_usage_insert,
    owner_id, owner_type, owner_name, repo_id, repo_name, issue_number,
    user_id, installation_id, source, trigger, pr_number, expected_id
):
    mock_usage_data = MagicMock()
    mock_usage_data.model_dump.return_value = {"test": "data"}
    mock_usage_insert.return_value = mock_usage_data
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_execute.return_value = (None, [{"id": expected_id}])
    mock_insert.execute = mock_execute
    mock_table.insert.return_value = mock_insert
    mock_supabase_client.table.return_value = mock_table
    
    result = insert_usage(
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=repo_id,
        repo_name=repo_name,
        issue_number=issue_number,
        user_id=user_id,
        installation_id=installation_id,
        source=source,
        trigger=trigger,
        pr_number=pr_number
    )
    
    assert result == expected_id
    mock_usage_insert.assert_called_once_with(
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=repo_id,
        repo_name=repo_name,
        issue_number=issue_number,
        user_id=user_id,
        installation_id=installation_id,
        source=source,
        trigger=trigger,
        pr_number=pr_number
    )
