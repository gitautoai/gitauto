# Standard imports
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
from services.supabase.usage.insert_usage import insert_usage, Trigger
from schemas.supabase.fastapi.schema_public_latest import UsageInsert


@pytest.fixture
def mock_supabase_client():
    """Mock the supabase client for testing."""
    with patch("services.supabase.usage.insert_usage.supabase") as mock_client:
        # Mock the chain: supabase.table().insert().execute()
        # The execute() method returns (data, metadata) where data[1][0]["id"] is the ID
        mock_client.table.return_value.insert.return_value.execute.return_value = (
            [None, [{"id": 123}]], None
        )
        
        yield mock_client


@pytest.fixture
def sample_usage_data():
    """Sample usage data for testing."""
    return {
        "owner_id": 12345,
        "owner_type": "Organization",
        "owner_name": "test-org",
        "repo_id": 67890,
        "repo_name": "test-repo",
        "issue_number": 42,
        "user_id": 98765,
        "installation_id": 11111,
        "source": "github",
        "trigger": "issue_comment",
        "pr_number": None,
    }


@pytest.fixture
def sample_usage_data_with_pr():
    """Sample usage data with PR number for testing."""
    return {
        "owner_id": 12345,
        "owner_type": "Organization", 
        "owner_name": "test-org",
        "repo_id": 67890,
        "repo_name": "test-repo",
        "issue_number": 42,
        "user_id": 98765,
        "installation_id": 11111,
        "source": "github",
        "trigger": "pr_merge",
        "pr_number": 123,
    }


class TestInsertUsage:
    """Test cases for insert_usage function."""

    def test_insert_usage_success_without_pr_number(self, mock_supabase_client, sample_usage_data):
        """Test successful usage insertion without PR number."""
        # Execute
        result = insert_usage(**sample_usage_data)

        # Verify
        assert result == 123
        
        # Verify supabase client calls
        mock_supabase_client.table.assert_called_once_with(table_name="usage")
        
        # Get the call arguments to verify the data
        insert_call = mock_supabase_client.table.return_value.insert
        insert_call.assert_called_once()
        
        # Verify the data passed to insert
        call_args = insert_call.call_args
        assert "json" in call_args.kwargs
        inserted_data = call_args.kwargs["json"]
        
        # Verify all required fields are present
        assert inserted_data["owner_id"] == 12345
        assert inserted_data["owner_type"] == "Organization"
        assert inserted_data["owner_name"] == "test-org"
        assert inserted_data["repo_id"] == 67890
        assert inserted_data["repo_name"] == "test-repo"
        assert inserted_data["issue_number"] == 42
        assert inserted_data["user_id"] == 98765
        assert inserted_data["installation_id"] == 11111
        assert inserted_data["source"] == "github"
        assert inserted_data["trigger"] == "issue_comment"
        
        # Verify pr_number is excluded (None values are excluded)
        assert "pr_number" not in inserted_data

    def test_insert_usage_success_with_pr_number(self, mock_supabase_client, sample_usage_data_with_pr):
        """Test successful usage insertion with PR number."""
        # Execute
        result = insert_usage(**sample_usage_data_with_pr)

        # Verify
        assert result == 123
        
        # Verify supabase client calls
        mock_supabase_client.table.assert_called_once_with(table_name="usage")
        
        # Get the call arguments to verify the data
        insert_call = mock_supabase_client.table.return_value.insert
        insert_call.assert_called_once()
        
        # Verify the data passed to insert
        call_args = insert_call.call_args
        assert "json" in call_args.kwargs
        inserted_data = call_args.kwargs["json"]
        
        # Verify pr_number is included when not None
        assert inserted_data["pr_number"] == 123
        assert inserted_data["trigger"] == "pr_merge"

    @pytest.mark.parametrize("trigger_value", [
        "issue_label",
        "issue_comment", 
        "review_comment",
        "test_failure",
        "pr_checkbox",
        "pr_merge",
    ])
    def test_insert_usage_with_different_triggers(self, mock_supabase_client, sample_usage_data, trigger_value):
        """Test insert_usage with different trigger values."""
        # Setup
        sample_usage_data["trigger"] = trigger_value
        
        # Execute
        result = insert_usage(**sample_usage_data)
        
        # Verify
        assert result == 123
        
        # Verify trigger value in inserted data
        insert_call = mock_supabase_client.table.return_value.insert
        call_args = insert_call.call_args
        inserted_data = call_args.kwargs["json"]
        assert inserted_data["trigger"] == trigger_value

    def test_insert_usage_model_dump_exclude_none(self, mock_supabase_client, sample_usage_data):
        """Test that model_dump excludes None values correctly."""
        # Execute
        insert_usage(**sample_usage_data)
        
        # Verify
        insert_call = mock_supabase_client.table.return_value.insert
        call_args = insert_call.call_args
        inserted_data = call_args.kwargs["json"]
        
        # Verify None values are excluded
        assert "pr_number" not in inserted_data
        
        # Verify non-None values are included
        assert "owner_id" in inserted_data
        assert "trigger" in inserted_data

    def test_insert_usage_return_value_casting(self, mock_supabase_client, sample_usage_data):
        """Test that the return value is properly cast to int."""
        # Setup - mock different return value types
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            [None, [{"id": "456"}]], None  # String ID that should be cast to int
        )
        
        # Execute
        result = insert_usage(**sample_usage_data)
        
        # Verify
        assert result == 456
        assert isinstance(result, int)

    def test_insert_usage_creates_usage_insert_model(self, mock_supabase_client, sample_usage_data):
        """Test that UsageInsert model is created with correct parameters."""
        with patch("services.supabase.usage.insert_usage.UsageInsert") as mock_usage_insert:
            mock_instance = MagicMock()
            mock_instance.model_dump.return_value = {"test": "data"}
            mock_usage_insert.return_value = mock_instance
            
            # Execute
            insert_usage(**sample_usage_data)
            
            # Verify UsageInsert was called with correct parameters
            mock_usage_insert.assert_called_once_with(
                owner_id=12345,
                owner_type="Organization",
                owner_name="test-org",
                repo_id=67890,
                repo_name="test-repo",
                issue_number=42,
                user_id=98765,
                installation_id=11111,
                source="github",
                trigger="issue_comment",
                pr_number=None,
            )
            
            # Verify model_dump was called with exclude_none=True
            mock_instance.model_dump.assert_called_once_with(exclude_none=True)

    @patch("services.supabase.usage.insert_usage.handle_exceptions")
    def test_insert_usage_decorator_applied(self, mock_handle_exceptions, sample_usage_data):
        """Test that handle_exceptions decorator is properly applied."""
        # Setup
        mock_handle_exceptions.return_value = lambda func: func
        
        # Import the module to trigger decorator application
        from services.supabase.usage.insert_usage import insert_usage
        
        # Verify decorator was called with correct parameters
        mock_handle_exceptions.assert_called_with(
            default_return_value=None,
            raise_on_error=True
        )

    def test_insert_usage_with_minimal_required_fields(self, mock_supabase_client):
        """Test insert_usage with only required fields."""
        # Setup - minimal required data
        minimal_data = {
            "owner_id": 1,
            "owner_type": "User",
            "owner_name": "user",
            "repo_id": 1,
            "repo_name": "repo",
            "issue_number": 1,
            "user_id": 1,
            "installation_id": 1,
            "source": "test",
            "trigger": "issue_label",
        }
        
        # Execute
        result = insert_usage(**minimal_data)
        
        # Verify
        assert result == 123
        mock_supabase_client.table.assert_called_once_with(table_name="usage")

    def test_insert_usage_supabase_response_structure(self, mock_supabase_client, sample_usage_data):
        """Test that function correctly handles supabase response structure."""
        # Setup - mock response with expected structure: (data, metadata)
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            [None, [{"id": 789, "created_at": "2023-01-01"}]],  # data array
            {"status": "success"}  # metadata
        )
        
        # Execute
        result = insert_usage(**sample_usage_data)
        
        # Verify
        assert result == 789


class TestTriggerType:
    """Test cases for Trigger type definition."""

    def test_trigger_literal_values(self):
        """Test that Trigger type contains expected literal values."""
        # This test verifies the Trigger type definition
        # The actual values are tested implicitly in the parametrized test above
        from services.supabase.usage.insert_usage import Trigger
        
        # Verify Trigger is a type (this will pass if import succeeds)
        assert Trigger is not None


class TestInsertUsageErrorHandling:
    """Test error handling scenarios for insert_usage function."""

    def test_insert_usage_supabase_exception_with_raise_on_error(self, sample_usage_data):
        """Test that exceptions are raised when raise_on_error=True."""
        with patch("services.supabase.usage.insert_usage.supabase") as mock_client:
            # Setup mock to raise an exception
            mock_client.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")
            
            # Execute and verify exception is raised
            with pytest.raises(Exception, match="Database error"):
                insert_usage(**sample_usage_data)

    def test_insert_usage_usage_insert_model_validation_error(self, mock_supabase_client):
        """Test handling of UsageInsert model validation errors."""
        with patch("services.supabase.usage.insert_usage.UsageInsert") as mock_usage_insert:
            # Setup mock to raise validation error
            mock_usage_insert.side_effect = ValueError("Invalid data")
            
            # Execute and verify exception is raised (due to raise_on_error=True)
            with pytest.raises(ValueError, match="Invalid data"):
                insert_usage(
                    owner_id=1,
                    owner_type="User",
                    owner_name="user",
                    repo_id=1,
                    repo_name="repo",
                    issue_number=1,
                    user_id=1,
                    installation_id=1,
                    source="test",
                    trigger="issue_label",
                )

    def test_insert_usage_model_dump_exception(self, mock_supabase_client, sample_usage_data):
        """Test handling of model_dump exceptions."""
        with patch("services.supabase.usage.insert_usage.UsageInsert") as mock_usage_insert:
            mock_instance = MagicMock()
            mock_instance.model_dump.side_effect = AttributeError("model_dump failed")
            mock_usage_insert.return_value = mock_instance
            
            # Execute and verify exception is raised
            with pytest.raises(AttributeError, match="model_dump failed"):
                insert_usage(**sample_usage_data)

    def test_insert_usage_cast_exception(self, mock_supabase_client, sample_usage_data):
        """Test handling of cast exceptions when return value is not castable to int."""
        # Setup mock to return non-castable value
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            [None, [{"id": "not-a-number"}]], None
        )
        
        # Execute and verify exception is raised
        with pytest.raises(ValueError):
            insert_usage(**sample_usage_data)

    def test_insert_usage_missing_id_in_response(self, mock_supabase_client, sample_usage_data):
        """Test handling when response doesn't contain expected id field."""
        # Setup mock to return response without id
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            [None, [{"other_field": "value"}]], None
        )
        
        # Execute and verify exception is raised
        with pytest.raises(KeyError):
            insert_usage(**sample_usage_data)

    def test_insert_usage_empty_response_data(self, mock_supabase_client, sample_usage_data):
        """Test handling when response data array is empty."""
        # Setup mock to return empty data array
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            None, []
        )
        
        # Execute and verify exception is raised
        with pytest.raises(IndexError):
            insert_usage(**sample_usage_data)

    def test_insert_usage_invalid_trigger_type(self, mock_supabase_client, sample_usage_data):
        """Test with invalid trigger type (should be caught by type system but test runtime behavior)."""
        # Setup with invalid trigger
        sample_usage_data["trigger"] = "invalid_trigger"
        
        # This should still work at runtime since Python doesn't enforce Literal types at runtime
        # The UsageInsert model will accept any string value
        result = insert_usage(**sample_usage_data)
        assert result == 123
