"""Unit tests for process_repositories.py"""

# Standard imports
import tempfile
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
from services.webhook.process_repositories import process_repositories


@pytest.fixture
def mock_clone_repo():
    """Mock clone_repo function."""
    with patch("services.webhook.process_repositories.clone_repo") as mock:
        yield mock


@pytest.fixture
def mock_get_repository_stats():
    """Mock get_repository_stats function."""
    with patch("services.webhook.process_repositories.get_repository_stats") as mock:
        yield mock


@pytest.fixture
def mock_upsert_repository():
    """Mock upsert_repository function."""
    with patch("services.webhook.process_repositories.upsert_repository") as mock:
        yield mock


@pytest.fixture
def mock_tempfile():
    """Mock tempfile.mkdtemp function."""
    with patch("services.webhook.process_repositories.tempfile.mkdtemp") as mock:
        mock.return_value = "/tmp/test_repo_12345"
        yield mock


@pytest.fixture
def mock_shutil():
    """Mock shutil.rmtree function."""
    with patch("services.webhook.process_repositories.shutil.rmtree") as mock:
        yield mock


@pytest.fixture
def sample_repositories():
    """Sample repository data for testing."""
    return [
        {"id": 111, "name": "test-repo-1"},
        {"id": 222, "name": "test-repo-2"},
    ]


@pytest.fixture
def sample_stats():
    """Sample repository stats for testing."""
    return {
        "file_count": 25,
        "blank_lines": 150,
        "comment_lines": 75,
        "code_lines": 500,
    }


class TestProcessRepositories:
    """Test cases for process_repositories function."""

    def test_process_repositories_success(
        self,
        sample_repositories,
        sample_stats,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test successful processing of repositories."""
        # Setup
        mock_get_repository_stats.return_value = sample_stats

        # Execute
        process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )

        # Verify tempfile operations
        assert mock_tempfile.call_count == 2
        assert mock_shutil.call_count == 2
        mock_shutil.assert_called_with("/tmp/test_repo_12345", ignore_errors=True)

        # Verify clone operations
        assert mock_clone_repo.call_count == 2
        mock_clone_repo.assert_any_call(
            owner="test-owner",
            repo="test-repo-1",
            token="ghs_test_token",
            target_dir="/tmp/test_repo_12345",
        )
        mock_clone_repo.assert_any_call(
            owner="test-owner",
            repo="test-repo-2",
            token="ghs_test_token",
            target_dir="/tmp/test_repo_12345",
        )

        # Verify stats operations
        assert mock_get_repository_stats.call_count == 2
        mock_get_repository_stats.assert_called_with(local_path="/tmp/test_repo_12345")

        # Verify upsert operations
        assert mock_upsert_repository.call_count == 2
        mock_upsert_repository.assert_any_call(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=111,
            repo_name="test-repo-1",
            user_id=67890,
            user_name="test-user",
            file_count=25,
            blank_lines=150,
            comment_lines=75,
            code_lines=500,
        )
        mock_upsert_repository.assert_any_call(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=222,
            repo_name="test-repo-2",
            user_id=67890,
            user_name="test-user",
            file_count=25,
            blank_lines=150,
            comment_lines=75,
            code_lines=500,
        )

    def test_process_repositories_empty_list(
        self,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test processing with empty repository list."""
        # Execute
        process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=[],
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )

        # Verify no operations were performed
        mock_tempfile.assert_not_called()
        mock_shutil.assert_not_called()
        mock_clone_repo.assert_not_called()
        mock_get_repository_stats.assert_not_called()
        mock_upsert_repository.assert_not_called()

    def test_process_repositories_single_repository(
        self,
        sample_stats,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test processing with single repository."""
        # Setup
        single_repo = [{"id": 333, "name": "single-repo"}]
        mock_get_repository_stats.return_value = sample_stats

        # Execute
        process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=single_repo,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )

        # Verify single operations
        mock_tempfile.assert_called_once()
        mock_shutil.assert_called_once()
        mock_clone_repo.assert_called_once_with(
            owner="test-owner",
            repo="single-repo",
            token="ghs_test_token",
            target_dir="/tmp/test_repo_12345",
        )
        mock_get_repository_stats.assert_called_once()
        mock_upsert_repository.assert_called_once_with(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=333,
            repo_name="single-repo",
            user_id=67890,
            user_name="test-user",
            file_count=25,
            blank_lines=150,
            comment_lines=75,
            code_lines=500,
        )

    def test_process_repositories_clone_failure(
        self,
        sample_repositories,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test processing when clone_repo fails."""
        # Setup
        mock_clone_repo.side_effect = Exception("Clone failed")

        # Execute
        process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )

        # Verify cleanup still happens and upsert is called with default stats
        assert mock_tempfile.call_count == 2
        assert mock_shutil.call_count == 2
        assert mock_clone_repo.call_count == 2
        mock_get_repository_stats.assert_not_called()
        assert mock_upsert_repository.call_count == 2
        
        # Verify default stats are used
        mock_upsert_repository.assert_any_call(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=111,
            repo_name="test-repo-1",
            user_id=67890,
            user_name="test-user",
            file_count=0,
            blank_lines=0,
            comment_lines=0,
            code_lines=0,
        )

    def test_process_repositories_stats_failure(
        self,
        sample_repositories,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test processing when get_repository_stats fails."""
        # Setup
        mock_get_repository_stats.side_effect = Exception("Stats failed")

        # Execute
        process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )

        # Verify operations continue with default stats
        assert mock_tempfile.call_count == 2
        assert mock_shutil.call_count == 2
        assert mock_clone_repo.call_count == 2
        assert mock_get_repository_stats.call_count == 2
        assert mock_upsert_repository.call_count == 2
        
        # Verify default stats are used when stats fail
        mock_upsert_repository.assert_any_call(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=111,
            repo_name="test-repo-1",
            user_id=67890,
            user_name="test-user",
            file_count=0,
            blank_lines=0,
            comment_lines=0,
            code_lines=0,
        )

    def test_process_repositories_cleanup_on_exception(
        self,
        sample_repositories,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test that cleanup happens even when exceptions occur."""
        # Setup - make clone fail
        mock_clone_repo.side_effect = Exception("Clone failed")

        # Execute
        process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )

        # Verify cleanup still happens
        assert mock_shutil.call_count == 2
        mock_shutil.assert_called_with("/tmp/test_repo_12345", ignore_errors=True)

    def test_process_repositories_with_none_token(
        self,
        sample_repositories,
        sample_stats,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test processing with None token."""
        # Setup
        mock_get_repository_stats.return_value = sample_stats

        # Execute
        process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token=None,
            user_id=67890,
            user_name="test-user",
        )

        # Verify clone is called with None token
        mock_clone_repo.assert_any_call(
            owner="test-owner",
            repo="test-repo-1",
            token=None,
            target_dir="/tmp/test_repo_12345",
        )

    def test_process_repositories_with_empty_token(
        self,
        sample_repositories,
        sample_stats,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test processing with empty token."""
        # Setup
        mock_get_repository_stats.return_value = sample_stats

        # Execute
        process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="",
            user_id=67890,
            user_name="test-user",
        )

        # Verify clone is called with empty token
        mock_clone_repo.assert_any_call(
            owner="test-owner",
            repo="test-repo-1",
            token="",
            target_dir="/tmp/test_repo_12345",
        )

    def test_process_repositories_with_special_characters(
        self,
        sample_stats,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test processing with special characters in names."""
        # Setup
        special_repos = [{"id": 444, "name": "repo-with-special-chars@#$"}]
        mock_get_repository_stats.return_value = sample_stats

        # Execute
        process_repositories(
            owner_id=12345,
            owner_name="owner-with-special@chars",
            repositories=special_repos,
            token="ghs_test_token",
            user_id=67890,
            user_name="user-with-special@chars",
        )

        # Verify operations work with special characters
        mock_clone_repo.assert_called_once_with(
            owner="owner-with-special@chars",
            repo="repo-with-special-chars@#$",
            token="ghs_test_token",
            target_dir="/tmp/test_repo_12345",
        )
        mock_upsert_repository.assert_called_once_with(
            owner_id=12345,
            owner_name="owner-with-special@chars",
            repo_id=444,
            repo_name="repo-with-special-chars@#$",
            user_id=67890,
            user_name="user-with-special@chars",
            file_count=25,
            blank_lines=150,
            comment_lines=75,
            code_lines=500,
        )

    def test_process_repositories_with_zero_stats(
        self,
        sample_repositories,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test processing when stats return zero values."""
        # Setup
        zero_stats = {"file_count": 0, "blank_lines": 0, "comment_lines": 0, "code_lines": 0}
        mock_get_repository_stats.return_value = zero_stats

        # Execute
        process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )

        # Verify zero stats are passed correctly
        mock_upsert_repository.assert_any_call(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=111,
            repo_name="test-repo-1",
            user_id=67890,
            user_name="test-user",
            file_count=0,
            blank_lines=0,
            comment_lines=0,
            code_lines=0,
        )

    def test_process_repositories_decorator_behavior(
        self,
        sample_repositories,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test that the handle_exceptions decorator works correctly."""
        # Setup - make upsert fail to test decorator
        mock_upsert_repository.side_effect = Exception("Database error")

        # Execute - should not raise exception due to decorator
        result = process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )

        # Verify function returns None (default_return_value from decorator)
        assert result is None
        # Verify cleanup still happens
        assert mock_shutil.call_count == 2
