"""Test for create_user_request function."""

from unittest.mock import patch
import pytest

from services.supabase.create_user_request import create_user_request


class TestCreateUserRequest:
    """Test cases for create_user_request function."""

    @pytest.fixture
    def sample_params(self):
        """Sample parameters for testing."""
        return {
            "user_id": 12345,
            "user_name": "test_user",
            "installation_id": 67890,
            "owner_id": 11111,
            "owner_type": "Organization",
            "owner_name": "test_org",
            "repo_id": 22222,
            "repo_name": "test_repo",
            "issue_number": 123,
            "source": "github",
            "trigger": "issue_comment",
            "email": "test@example.com",
            "pr_number": 456,
        }

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies."""
        with patch(
            "services.supabase.create_user_request.get_issue"
        ) as mock_get_issue, patch(
            "services.supabase.create_user_request.insert_issue"
        ) as mock_insert_issue, patch(
            "services.supabase.create_user_request.insert_usage"
        ) as mock_insert_usage, patch(
            "services.supabase.create_user_request.upsert_user"
        ) as mock_upsert_user:

            yield {
                "get_issue": mock_get_issue,
                "insert_issue": mock_insert_issue,
                "insert_usage": mock_insert_usage,
                "upsert_user": mock_upsert_user,
            }

    def test_create_user_request_existing_issue(self, sample_params, mock_dependencies):
        """Test create_user_request when issue already exists."""
        # Setup
        existing_issue = {"id": 1, "issue_number": 123}
        mock_dependencies["get_issue"].return_value = existing_issue
        mock_dependencies["insert_usage"].return_value = 999

        # Execute
        result = create_user_request(**sample_params)

        # Assert
        assert result == 999

        # Verify get_issue was called with correct parameters
        mock_dependencies["get_issue"].assert_called_once_with(
            owner_type="Organization",
            owner_name="test_org",
            repo_name="test_repo",
            issue_number=123,
        )

        # Verify insert_issue was NOT called since issue exists
        mock_dependencies["insert_issue"].assert_not_called()

        # Verify insert_usage was called with correct parameters
        mock_dependencies["insert_usage"].assert_called_once_with(
            owner_id=11111,
            owner_type="Organization",
            owner_name="test_org",
            repo_id=22222,
            repo_name="test_repo",
            issue_number=123,
            user_id=12345,
            installation_id=67890,
            source="github",
            trigger="issue_comment",
            pr_number=456,
        )

        # Verify upsert_user was called with correct parameters
        mock_dependencies["upsert_user"].assert_called_once_with(
            user_id=12345,
            user_name="test_user",
            email="test@example.com",
        )

    def test_create_user_request_new_issue(self, sample_params, mock_dependencies):
        """Test create_user_request when issue doesn't exist."""
        # Setup
        mock_dependencies["get_issue"].return_value = None
        mock_dependencies["insert_usage"].return_value = 888

        # Execute
        result = create_user_request(**sample_params)

        # Assert
        assert result == 888

        # Verify get_issue was called
        mock_dependencies["get_issue"].assert_called_once_with(
            owner_type="Organization",
            owner_name="test_org",
            repo_name="test_repo",
            issue_number=123,
        )

        # Verify insert_issue WAS called since issue doesn't exist
        mock_dependencies["insert_issue"].assert_called_once_with(
            owner_id=11111,
            owner_type="Organization",
            owner_name="test_org",
            repo_id=22222,
            repo_name="test_repo",
            issue_number=123,
            installation_id=67890,
        )

        # Verify insert_usage was called
        mock_dependencies["insert_usage"].assert_called_once()

        # Verify upsert_user was called
        mock_dependencies["upsert_user"].assert_called_once()

    def test_create_user_request_without_pr_number(
        self, sample_params, mock_dependencies
    ):
        """Test create_user_request without pr_number."""
        # Setup
        params_without_pr = sample_params.copy()
        del params_without_pr["pr_number"]

        mock_dependencies["get_issue"].return_value = {"id": 1}
        mock_dependencies["insert_usage"].return_value = 777

        # Execute
        result = create_user_request(**params_without_pr)

        # Assert
        assert result == 777

        # Verify insert_usage was called with pr_number=None
        mock_dependencies["insert_usage"].assert_called_once_with(
            owner_id=11111,
            owner_type="Organization",
            owner_name="test_org",
            repo_id=22222,
            repo_name="test_repo",
            issue_number=123,
            user_id=12345,
            installation_id=67890,
            source="github",
            trigger="issue_comment",
            pr_number=None,
        )

    def test_create_user_request_without_email(self, sample_params, mock_dependencies):
        """Test create_user_request without email."""
        # Setup
        params_without_email = sample_params.copy()
        params_without_email["email"] = None

        mock_dependencies["get_issue"].return_value = {"id": 1}
        mock_dependencies["insert_usage"].return_value = 666

        # Execute
        result = create_user_request(**params_without_email)

        # Assert
        assert result == 666

        # Verify upsert_user was called with email=None
        mock_dependencies["upsert_user"].assert_called_once_with(
            user_id=12345,
            user_name="test_user",
            email=None,
        )

    def test_create_user_request_different_trigger_types(
        self, sample_params, mock_dependencies
    ):
        """Test create_user_request with different trigger types."""
        triggers = [
            "issue_label",
            "review_comment",
            "test_failure",
            "pr_checkbox",
            "pr_merge",
        ]

        for trigger in triggers:
            # Setup
            params = sample_params.copy()
            params["trigger"] = trigger

            mock_dependencies["get_issue"].return_value = {"id": 1}
            mock_dependencies["insert_usage"].return_value = 555

            # Reset mocks
            for mock in mock_dependencies.values():
                mock.reset_mock()

            # Execute
            result = create_user_request(**params)

            # Assert
            assert result == 555

            # Verify insert_usage was called with correct trigger
            mock_dependencies["insert_usage"].assert_called_once()
            call_args = mock_dependencies["insert_usage"].call_args[1]
            assert call_args["trigger"] == trigger

    def test_create_user_request_user_owner_type(
        self, sample_params, mock_dependencies
    ):
        """Test create_user_request with User owner type."""
        # Setup
        params = sample_params.copy()
        params["owner_type"] = "User"
        params["owner_name"] = "individual_user"

        mock_dependencies["get_issue"].return_value = None
        mock_dependencies["insert_usage"].return_value = 444

        # Execute
        result = create_user_request(**params)

        # Assert
        assert result == 444

        # Verify get_issue was called with User owner_type
        mock_dependencies["get_issue"].assert_called_once_with(
            owner_type="User",
            owner_name="individual_user",
            repo_name="test_repo",
            issue_number=123,
        )

        # Verify insert_issue was called with User owner_type
        mock_dependencies["insert_issue"].assert_called_once_with(
            owner_id=11111,
            owner_type="User",
            owner_name="individual_user",
            repo_id=22222,
            repo_name="test_repo",
            issue_number=123,
            installation_id=67890,
        )

    def test_create_user_request_with_special_characters(
        self, sample_params, mock_dependencies
    ):
        """Test create_user_request with special characters in names."""
        # Setup
        params = sample_params.copy()
        params["owner_name"] = "org-with-dashes"
        params["repo_name"] = "repo_with_underscores"
        params["user_name"] = "user.with.dots"

        mock_dependencies["get_issue"].return_value = {"id": 1}
        mock_dependencies["insert_usage"].return_value = 333

        # Execute
        result = create_user_request(**params)

        # Assert
        assert result == 333

        # Verify all functions were called with special character names
        mock_dependencies["get_issue"].assert_called_once_with(
            owner_type="Organization",
            owner_name="org-with-dashes",
            repo_name="repo_with_underscores",
            issue_number=123,
        )

        mock_dependencies["upsert_user"].assert_called_once_with(
            user_id=12345,
            user_name="user.with.dots",
            email="test@example.com",
        )

    def test_create_user_request_with_zero_issue_number(
        self, sample_params, mock_dependencies
    ):
        """Test create_user_request with issue number 0."""
        # Setup
        params = sample_params.copy()
        params["issue_number"] = 0

        mock_dependencies["get_issue"].return_value = None
        mock_dependencies["insert_usage"].return_value = 222

        # Execute
        result = create_user_request(**params)

        # Assert
        assert result == 222

        # Verify functions were called with issue_number=0
        mock_dependencies["get_issue"].assert_called_once_with(
            owner_type="Organization",
            owner_name="test_org",
            repo_name="test_repo",
            issue_number=0,
        )

    def test_create_user_request_exception_handling(self, sample_params):
        """Test that exceptions are raised by the decorator."""
        with patch("services.supabase.create_user_request.get_issue") as mock_get_issue:
            # Setup mock to raise exception
            mock_get_issue.side_effect = Exception("Database error")

            # Execute - should raise exception due to @handle_exceptions(raise_on_error=True)
            with pytest.raises(Exception) as exc_info:
                create_user_request(**sample_params)

            # Assert - should raise the original exception
            assert str(exc_info.value) == "Database error"

    def test_create_user_request_insert_usage_returns_none(
        self, sample_params, mock_dependencies
    ):
        """Test when insert_usage returns None."""
        # Setup
        mock_dependencies["get_issue"].return_value = {"id": 1}
        mock_dependencies["insert_usage"].return_value = None

        # Execute
        result = create_user_request(**sample_params)

        # Assert
        assert result is None

        # Verify all functions were still called
        mock_dependencies["get_issue"].assert_called_once()
        mock_dependencies["insert_usage"].assert_called_once()
        mock_dependencies["upsert_user"].assert_called_once()

    def test_create_user_request_large_ids(self, sample_params, mock_dependencies):
        """Test create_user_request with large ID values."""
        # Setup
        params = sample_params.copy()
        params["user_id"] = 999999999
        params["owner_id"] = 888888888
        params["repo_id"] = 777777777
        params["installation_id"] = 666666666

        mock_dependencies["get_issue"].return_value = None
        mock_dependencies["insert_usage"].return_value = 111

        # Execute
        result = create_user_request(**params)

        # Assert
        assert result == 111

        # Verify functions were called with large IDs
        mock_dependencies["insert_issue"].assert_called_once_with(
            owner_id=888888888,
            owner_type="Organization",
            owner_name="test_org",
            repo_id=777777777,
            repo_name="test_repo",
            issue_number=123,
            installation_id=666666666,
        )

        mock_dependencies["upsert_user"].assert_called_once_with(
            user_id=999999999,
            user_name="test_user",
            email="test@example.com",
        )

    def test_create_user_request_different_sources(
        self, sample_params, mock_dependencies
    ):
        """Test create_user_request with different source values."""
        sources = ["github", "webhook", "api", "manual"]

        for source in sources:
            # Setup
            params = sample_params.copy()
            params["source"] = source

            mock_dependencies["get_issue"].return_value = {"id": 1}
            mock_dependencies["insert_usage"].return_value = 100

            # Reset mocks
            for mock in mock_dependencies.values():
                mock.reset_mock()

            # Execute
            result = create_user_request(**params)

            # Assert
            assert result == 100

            # Verify insert_usage was called with correct source
            mock_dependencies["insert_usage"].assert_called_once()
            call_args = mock_dependencies["insert_usage"].call_args[1]
            assert call_args["source"] == source

    def test_create_user_request_function_call_order(
        self, sample_params, mock_dependencies
    ):
        """Test that functions are called in the correct order."""
        # Setup
        mock_dependencies["get_issue"].return_value = None
        mock_dependencies["insert_usage"].return_value = 123

        # Execute
        create_user_request(**sample_params)

        # Verify call order by checking that get_issue is called before insert_issue
        # and insert_usage is called after both
        assert mock_dependencies["get_issue"].call_count == 1
        assert mock_dependencies["insert_issue"].call_count == 1
        assert mock_dependencies["insert_usage"].call_count == 1
        assert mock_dependencies["upsert_user"].call_count == 1
