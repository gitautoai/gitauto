from unittest.mock import Mock, patch

from services.supabase.repositories.insert_repository import insert_repository


def test_insert_repository_success():
    """Test insert_repository successfully inserts repository data."""
    mock_result = Mock()
    mock_result.data = [
        {
            "id": 1,
            "owner_id": 789,
            "repo_id": 123456,
            "repo_name": "test-repo",
            "file_count": 100,
            "blank_lines": 50,
            "comment_lines": 30,
            "code_lines": 200,
            "created_by": "123:testuser",
            "updated_by": "123:testuser",
            "structured_rules": {"rule1": "value1"},
        }
    ]

    with patch(
        "services.supabase.repositories.insert_repository.supabase"
    ) as mock_supabase, patch(
        "services.supabase.repositories.insert_repository.get_default_structured_rules"
    ) as mock_get_rules:
        mock_get_rules.return_value = {"rule1": "value1"}
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            mock_result
        )

        result = insert_repository(
            owner_id=789,
            repo_id=123456,
            repo_name="test-repo",
            user_id=123,
            user_name="testuser",
            file_count=100,
            blank_lines=50,
            comment_lines=30,
            code_lines=200,
        )

        assert result is not None
        assert isinstance(result, dict)
        assert result["repo_id"] == 123456
        assert result["repo_name"] == "test-repo"
        assert result["owner_id"] == 789
        assert result["file_count"] == 100
        assert result["blank_lines"] == 50
        assert result["comment_lines"] == 30
        assert result["code_lines"] == 200
        assert result["created_by"] == "123:testuser"
        assert result["updated_by"] == "123:testuser"
        assert result["structured_rules"] == {"rule1": "value1"}

        mock_supabase.table.assert_called_once_with("repositories")
        mock_supabase.table.return_value.insert.assert_called_once()
        mock_get_rules.assert_called_once()


def test_insert_repository_empty_data():
    """Test insert_repository returns None when no data is returned."""
    mock_result = Mock()
    mock_result.data = []

    with patch(
        "services.supabase.repositories.insert_repository.supabase"
    ) as mock_supabase, patch(
        "services.supabase.repositories.insert_repository.get_default_structured_rules"
    ) as mock_get_rules:
        mock_get_rules.return_value = {"rule1": "value1"}
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            mock_result
        )

        result = insert_repository(
            owner_id=789,
            repo_id=123456,
            repo_name="test-repo",
            user_id=123,
            user_name="testuser",
        )

        assert result is None
        mock_supabase.table.assert_called_once_with("repositories")


def test_insert_repository_none_data():
    """Test insert_repository returns None when data is None."""
    mock_result = Mock()
    mock_result.data = None

    with patch(
        "services.supabase.repositories.insert_repository.supabase"
    ) as mock_supabase, patch(
        "services.supabase.repositories.insert_repository.get_default_structured_rules"
    ) as mock_get_rules:
        mock_get_rules.return_value = {"rule1": "value1"}
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            mock_result
        )

        result = insert_repository(
            owner_id=789,
            repo_id=123456,
            repo_name="test-repo",
            user_id=123,
            user_name="testuser",
        )

        assert result is None
        mock_supabase.table.assert_called_once_with("repositories")


def test_insert_repository_exception_handling():
    """Test insert_repository handles exceptions and returns None due to decorator."""
    with patch(
        "services.supabase.repositories.insert_repository.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database connection error")

        result = insert_repository(
            owner_id=789,
            repo_id=123456,
            repo_name="test-repo",
            user_id=123,
            user_name="testuser",
        )

        assert result is None


def test_insert_repository_with_zero_values():
    """Test insert_repository handles zero values correctly."""
    mock_result = Mock()
    mock_result.data = [
        {
            "owner_id": 0,
            "repo_id": 0,
            "file_count": 0,
            "blank_lines": 0,
            "comment_lines": 0,
            "code_lines": 0,
        }
    ]

    with patch(
        "services.supabase.repositories.insert_repository.supabase"
    ) as mock_supabase, patch(
        "services.supabase.repositories.insert_repository.get_default_structured_rules"
    ) as mock_get_rules:
        mock_get_rules.return_value = {"rule1": "value1"}
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            mock_result
        )

        result = insert_repository(
            owner_id=0,
            repo_id=0,
            repo_name="test-repo",
            user_id=0,
            user_name="testuser",
            file_count=0,
            blank_lines=0,
            comment_lines=0,
            code_lines=0,
        )

        assert result is not None
        assert result["owner_id"] == 0
        assert result["repo_id"] == 0
        assert result["file_count"] == 0
        assert result["blank_lines"] == 0
        assert result["comment_lines"] == 0
        assert result["code_lines"] == 0


def test_insert_repository_structured_rules_error():
    """Test insert_repository handles error in getting structured rules."""
    with patch(
        "services.supabase.repositories.insert_repository.get_default_structured_rules"
    ) as mock_get_rules:
        mock_get_rules.side_effect = Exception("Failed to get rules")

        result = insert_repository(
            owner_id=789,
            repo_id=123456,
            repo_name="test-repo",
            user_id=123,
            user_name="testuser",
        )

        assert result is None
        mock_get_rules.assert_called_once()


def test_insert_repository_attribute_error():
    """Test insert_repository handles AttributeError and returns None."""
    with patch(
        "services.supabase.repositories.insert_repository.supabase"
    ) as mock_supabase:
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = (
            AttributeError("'NoneType' object has no attribute 'execute'")
        )

        result = insert_repository(
            owner_id=789,
            repo_id=123456,
            repo_name="test-repo",
            user_id=123,
            user_name="testuser",
        )

        assert result is None
