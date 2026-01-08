# pylint: disable=unused-argument
"""Unit tests for process_repositories.py"""

# Standard imports
from unittest.mock import patch

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
    # Tests use minimal dicts; production receives full Repository objects
    repos = [
        {"id": 111, "name": "test-repo-1"},
        {"id": 222, "name": "test-repo-2"},
    ]
    return repos


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

        # Execute - tests use minimal dicts; production receives full Repository objects
        process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=single_repo,  # type: ignore[arg-type]
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
        """Test processing when clone_repo fails - function exits early due to @handle_exceptions decorator."""
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

        # Verify only first repository is processed before exception causes early exit
        assert mock_tempfile.call_count == 1
        assert mock_shutil.call_count == 1
        assert mock_clone_repo.call_count == 1
        mock_get_repository_stats.assert_not_called()
        mock_upsert_repository.assert_not_called()

    def test_process_repositories_stats_failure(
        self,
        sample_repositories,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test processing when get_repository_stats fails - function exits early due to @handle_exceptions decorator."""
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

        # Verify only first repository is processed before exception causes early exit
        assert mock_tempfile.call_count == 1
        assert mock_shutil.call_count == 1
        assert mock_clone_repo.call_count == 1
        assert mock_get_repository_stats.call_count == 1
        mock_upsert_repository.assert_not_called()

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

        # Verify cleanup still happens for the first repository before early exit
        assert mock_shutil.call_count == 1
        mock_shutil.assert_called_with("/tmp/test_repo_12345", ignore_errors=True)

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

        # Execute - tests use minimal dicts; production receives full Repository objects
        process_repositories(
            owner_id=12345,
            owner_name="owner-with-special@chars",
            repositories=special_repos,  # type: ignore[arg-type]
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
        zero_stats = {
            "file_count": 0,
            "blank_lines": 0,
            "comment_lines": 0,
            "code_lines": 0,
        }
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
        # Verify cleanup still happens for first repository before early exit
        assert mock_shutil.call_count == 1

    def test_process_repositories_with_large_repository_list(
        self,
        sample_stats,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test processing with a large number of repositories."""
        # Setup - create a large list of repositories
        large_repo_list = [{"id": i, "name": f"repo-{i}"} for i in range(50)]
        mock_get_repository_stats.return_value = sample_stats

        # Execute - tests use minimal dicts; production receives full Repository objects
        process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=large_repo_list,  # type: ignore[arg-type]
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )

        # Verify all repositories were processed
        assert mock_tempfile.call_count == 50
        assert mock_shutil.call_count == 50
        assert mock_clone_repo.call_count == 50
        assert mock_get_repository_stats.call_count == 50
        assert mock_upsert_repository.call_count == 50

    def test_process_repositories_tempfile_creation_failure(
        self,
        sample_repositories,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test processing when tempfile creation fails."""
        # Setup
        mock_tempfile.side_effect = OSError("Cannot create temp directory")

        # Execute - should handle OSError gracefully due to decorator
        result = process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )

        # Verify function returns None due to exception handling
        assert result is None

    @patch("builtins.print")
    def test_process_repositories_print_statements(
        self,
        mock_print,
        sample_repositories,
        sample_stats,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test that print statements are called correctly."""
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

        # Verify print statements were called
        expected_calls = [
            "Cloning repository test-repo-1 into /tmp/test_repo_12345",
            f"Repository test-repo-1 stats: {sample_stats}",
            "Cloning repository test-repo-2 into /tmp/test_repo_12345",
            f"Repository test-repo-2 stats: {sample_stats}",
        ]

        # Check that all expected print calls were made
        actual_calls = [call.args[0] for call in mock_print.call_args_list]
        for expected_call in expected_calls:
            assert expected_call in actual_calls

    def test_process_repositories_mixed_success_failure(
        self,
        sample_stats,
        mock_clone_repo,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_tempfile,
        mock_shutil,
    ):
        """Test processing when some repositories succeed and others fail - function exits early due to @handle_exceptions decorator."""
        # Setup
        repos = [
            {"id": 111, "name": "success-repo"},
            {"id": 222, "name": "fail-repo"},
            {"id": 333, "name": "another-success-repo"},
        ]

        # Make clone fail for the second repository only
        def clone_side_effect(owner, repo, token, target_dir):
            if repo == "fail-repo":
                raise Exception("Clone failed for fail-repo")  # pylint: disable=broad-exception-raised

        mock_clone_repo.side_effect = clone_side_effect
        mock_get_repository_stats.return_value = sample_stats

        # Execute - tests use minimal dicts; production receives full Repository objects
        process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=repos,  # type: ignore[arg-type]
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )

        # Verify processing stops at the first failure due to @handle_exceptions decorator
        # First repository succeeds, second fails and causes early exit
        assert (
            mock_tempfile.call_count == 2
        )  # First repo succeeds, second repo starts but fails
        assert mock_shutil.call_count == 2  # Cleanup happens for both
        assert mock_clone_repo.call_count == 2  # Both repos attempted
        assert mock_get_repository_stats.call_count == 1  # Only first repo gets stats
        assert mock_upsert_repository.call_count == 1  # Only first repo gets upserted
