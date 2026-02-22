# pylint: disable=unused-argument
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
            "pr_number": 123,
            "source": "github",
            "trigger": "dashboard",
            "email": "test@example.com",
        }

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies."""
        with patch(
            "services.supabase.create_user_request.insert_usage"
        ) as mock_insert_usage, patch(
            "services.supabase.create_user_request.upsert_user"
        ) as mock_upsert_user:

            yield {
                "insert_usage": mock_insert_usage,
                "upsert_user": mock_upsert_user,
            }

    def test_create_user_request_returns_usage_id(
        self, sample_params, mock_dependencies
    ):
        """Test create_user_request returns usage_id from insert_usage."""
        mock_dependencies["insert_usage"].return_value = 999

        result = create_user_request(**sample_params)

        assert result == 999

        mock_dependencies["insert_usage"].assert_called_once_with(
            owner_id=11111,
            owner_type="Organization",
            owner_name="test_org",
            repo_id=22222,
            repo_name="test_repo",
            pr_number=123,
            user_id=12345,
            installation_id=67890,
            source="github",
            trigger="dashboard",
            lambda_log_group=None,
            lambda_log_stream=None,
            lambda_request_id=None,
        )

        mock_dependencies["upsert_user"].assert_called_once_with(
            user_id=12345,
            user_name="test_user",
            email="test@example.com",
        )

    def test_create_user_request_without_pr_number(
        self, sample_params, mock_dependencies
    ):
        """Test create_user_request without pr_number raises TypeError."""
        params_without_pr = sample_params.copy()
        del params_without_pr["pr_number"]

        with pytest.raises(TypeError):
            create_user_request(**params_without_pr)

    def test_create_user_request_without_email(self, sample_params, mock_dependencies):
        """Test create_user_request without email."""
        params_without_email = sample_params.copy()
        params_without_email["email"] = None

        mock_dependencies["insert_usage"].return_value = 666

        result = create_user_request(**params_without_email)

        assert result == 666

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
            "dashboard",
            "review_comment",
            "test_failure",
            "schedule",
        ]

        for trigger in triggers:
            params = sample_params.copy()
            params["trigger"] = trigger

            mock_dependencies["insert_usage"].return_value = 555

            for mock in mock_dependencies.values():
                mock.reset_mock()

            result = create_user_request(**params)

            assert result == 555

            mock_dependencies["insert_usage"].assert_called_once()
            call_args = mock_dependencies["insert_usage"].call_args[1]
            assert call_args["trigger"] == trigger

    def test_create_user_request_exception_handling(self, sample_params):
        """Test that exceptions are raised by the decorator."""
        with patch(
            "services.supabase.create_user_request.insert_usage"
        ) as mock_insert_usage:
            mock_insert_usage.side_effect = Exception("Database error")

            with pytest.raises(Exception) as exc_info:
                create_user_request(**sample_params)

            assert str(exc_info.value) == "Database error"

    def test_create_user_request_insert_usage_returns_none(
        self, sample_params, mock_dependencies
    ):
        """Test when insert_usage returns None."""
        mock_dependencies["insert_usage"].return_value = None

        result = create_user_request(**sample_params)

        assert result is None

        mock_dependencies["insert_usage"].assert_called_once()
        mock_dependencies["upsert_user"].assert_called_once()

    def test_create_user_request_with_lambda_info(
        self, sample_params, mock_dependencies
    ):
        """Test create_user_request with lambda_info provided."""
        params = sample_params.copy()
        params["lambda_info"] = {
            "log_group": "/aws/lambda/test",
            "log_stream": "2026/01/01/[$LATEST]abc123",
            "request_id": "req-123",
        }

        mock_dependencies["insert_usage"].return_value = 777

        result = create_user_request(**params)

        assert result == 777

        call_args = mock_dependencies["insert_usage"].call_args[1]
        assert call_args["lambda_log_group"] == "/aws/lambda/test"
        assert call_args["lambda_log_stream"] == "2026/01/01/[$LATEST]abc123"
        assert call_args["lambda_request_id"] == "req-123"

    def test_create_user_request_different_sources(
        self, sample_params, mock_dependencies
    ):
        """Test create_user_request with different source values."""
        sources = ["github", "webhook", "api", "manual"]

        for source in sources:
            params = sample_params.copy()
            params["source"] = source

            mock_dependencies["insert_usage"].return_value = 100

            for mock in mock_dependencies.values():
                mock.reset_mock()

            result = create_user_request(**params)

            assert result == 100

            mock_dependencies["insert_usage"].assert_called_once()
            call_args = mock_dependencies["insert_usage"].call_args[1]
            assert call_args["source"] == source
