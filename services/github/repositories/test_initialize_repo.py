# Standard imports
import os
from unittest.mock import patch, mock_open, MagicMock, call

# Third-party imports
import pytest

# Local imports
from services.github.repositories.initialize_repo import initialize_repo


class TestInitializeRepo:
    """Test cases for initialize_repo function."""

    @pytest.fixture
    def mock_config_constants(self):
        """Mock configuration constants."""
        with patch.multiple(
            "services.github.repositories.initialize_repo",
            PRODUCT_NAME="GitAuto",
            UTF8="utf-8",
            GITHUB_APP_USER_NAME="gitauto-ai[bot]",
            GITHUB_APP_USER_ID=161652217,
            GITHUB_NOREPLY_EMAIL_DOMAIN="users.noreply.github.com",
        ):
            yield

    @pytest.fixture
    def mock_url_constants(self):
        """Mock URL constants."""
        with patch.multiple(
            "services.github.repositories.initialize_repo",
            BLOG_URL="https://gitauto.ai/blog",
            PRODUCT_DEMO_URL="https://www.youtube.com/watch?v=demo",
            PRODUCT_LINKEDIN_URL="https://www.linkedin.com/company/gitauto/",
            PRODUCT_TWITTER_URL="https://x.com/gitautoai",
            PRODUCT_URL="https://gitauto.ai",
            PRODUCT_YOUTUBE_URL="https://youtube.com/@gitauto",
        ):
            yield

    @pytest.fixture
    def test_repo_path(self):
        """Provide a test repository path."""
        return "/tmp/test-repo"

    @pytest.fixture
    def test_remote_url(self):
        """Provide a test remote URL."""
        return "https://github.com/test-owner/test-repo.git"

    @pytest.fixture
    def test_token(self):
        """Provide a test token."""
        return "ghp_test_token_123"

    def test_initialize_repo_success(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test successful repository initialization."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ) as mock_file, patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command:

            result = initialize_repo(test_repo_path, test_remote_url, test_token)

            # Verify function returns None (successful execution)
            assert result is None

            # Verify README.md was created with correct content
            expected_readme_path = os.path.join(test_repo_path, "README.md")
            mock_file.assert_called_once_with(
                expected_readme_path, "w", encoding="utf-8"
            )

            # Verify README content contains expected elements
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            assert "## GitAuto resources" in written_content
            assert "https://gitauto.ai" in written_content
            assert "https://www.youtube.com/watch?v=demo" in written_content

            # Verify git commands were executed in correct order
            expected_calls = [
                call(command="git init -b main", cwd=test_repo_path),
                call(
                    command='git config user.name "gitauto-ai[bot]"',
                    cwd=test_repo_path,
                ),
                call(
                    command='git config user.email "161652217+gitauto-ai[bot]@users.noreply.github.com"',
                    cwd=test_repo_path,
                ),
                call(command="git add README.md", cwd=test_repo_path),
                call(
                    command='git commit -m "Initial commit with README"',
                    cwd=test_repo_path,
                ),
                call(
                    command=f"git remote add origin https://x-access-token:{test_token}@github.com/test-owner/test-repo.git",
                    cwd=test_repo_path,
                ),
                call(command="git push -u origin main", cwd=test_repo_path),
            ]
            mock_run_command.assert_has_calls(expected_calls)

    def test_initialize_repo_creates_directory_when_not_exists(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that directory is created when it doesn't exist."""
        with patch("os.path.exists", return_value=False), patch(
            "os.makedirs"
        ) as mock_makedirs, patch("builtins.open", mock_open()), patch(
            "services.github.repositories.initialize_repo.run_command"
        ):

            initialize_repo(test_repo_path, test_remote_url, test_token)

            mock_makedirs.assert_called_once_with(name=test_repo_path)

    def test_initialize_repo_remote_add_fails_uses_set_url(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that remote set-url is used when remote add fails."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command, patch(
            "builtins.print"
        ) as mock_print:

            # Make remote add command fail
            def side_effect(command, cwd):
                if "git remote add origin" in command:
                    raise Exception("Remote already exists")
                return MagicMock()

            mock_run_command.side_effect = side_effect

            initialize_repo(test_repo_path, test_remote_url, test_token)

            # Verify that set-url command was called after add failed
            set_url_call = call(
                command=f"git remote set-url origin https://x-access-token:{test_token}@github.com/test-owner/test-repo.git",
                cwd=test_repo_path,
            )
            assert set_url_call in mock_run_command.call_args_list

            # Verify print statements for failed remote add and successful set-url
            expected_print_calls = [
                call(f"Adding remote: {test_remote_url}"),
                call(f"Setting remote: {test_remote_url}"),
                call("Remote set successfully"),
            ]
            mock_print.assert_has_calls(expected_print_calls)

    def test_initialize_repo_file_write_error_handled(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that file write errors are handled gracefully."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", side_effect=IOError("Permission denied")
        ):

            # Should return None due to exception handling decorator
            result = initialize_repo(test_repo_path, test_remote_url, test_token)
            assert result is None

    def test_initialize_repo_git_command_error_handled(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that git command errors are handled gracefully."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command",
            side_effect=ValueError("Git command failed"),
        ):

            # Should return None due to exception handling decorator
            result = initialize_repo(test_repo_path, test_remote_url, test_token)
            assert result is None

    def test_initialize_repo_os_makedirs_error_handled(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that os.makedirs errors are handled gracefully."""
        with patch("os.path.exists", return_value=False), patch(
            "os.makedirs", side_effect=OSError("Permission denied")
        ):

            # Should return None due to exception handling decorator
            result = initialize_repo(test_repo_path, test_remote_url, test_token)
            assert result is None

    def test_initialize_repo_readme_content_format(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that README.md content is formatted correctly."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ) as mock_file, patch(
            "services.github.repositories.initialize_repo.run_command"
        ):

            initialize_repo(test_repo_path, test_remote_url, test_token)

            # Get the written content
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )

            # Verify README structure and content
            assert written_content.startswith("## GitAuto resources")
            assert "Here are GitAuto resources." in written_content
            assert "- [GitAuto homepage](https://gitauto.ai)" in written_content
            assert (
                "- [GitAuto demo](https://www.youtube.com/watch?v=demo)"
                in written_content
            )
            assert "- [GitAuto use cases](https://gitauto.ai/blog)" in written_content
            assert (
                "- [GitAuto LinkedIn](https://www.linkedin.com/company/gitauto/)"
                in written_content
            )
            assert "- [GitAuto Twitter](https://x.com/gitautoai)" in written_content
            assert (
                "- [GitAuto YouTube](https://youtube.com/@gitauto)" in written_content
            )

    def test_initialize_repo_git_config_commands(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that git config commands use correct user information."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command:

            initialize_repo(test_repo_path, test_remote_url, test_token)

            # Verify git config commands
            config_name_call = call(
                command='git config user.name "gitauto-ai[bot]"',
                cwd=test_repo_path,
            )
            config_email_call = call(
                command='git config user.email "161652217+gitauto-ai[bot]@users.noreply.github.com"',
                cwd=test_repo_path,
            )

            assert config_name_call in mock_run_command.call_args_list
            assert config_email_call in mock_run_command.call_args_list

    @pytest.mark.parametrize(
        "remote_url,expected_auth_url",
        [
            (
                "https://github.com/owner/repo.git",
                "https://x-access-token:token123@github.com/owner/repo.git",
            ),
            (
                "https://github.com/owner/repo",
                "https://x-access-token:token123@github.com/owner/repo",
            ),
            (
                "https://github.com/org-name/repo-name.git",
                "https://x-access-token:token123@github.com/org-name/repo-name.git",
            ),
            (
                "https://custom-domain.com/owner/repo.git",
                "https://x-access-token:token123@custom-domain.com/owner/repo.git",
            ),
        ],
    )
    def test_initialize_repo_token_injection_parametrized(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        remote_url,
        expected_auth_url,
    ):
        """Test token injection with various URL formats."""
        token = "token123"

        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command:

            initialize_repo(test_repo_path, remote_url, token)

            # Verify the token was correctly injected
            remote_add_call = call(
                command=f"git remote add origin {expected_auth_url}",
                cwd=test_repo_path,
            )
            assert remote_add_call in mock_run_command.call_args_list

    def test_initialize_repo_handle_exceptions_decorator_behavior(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that the handle_exceptions decorator works correctly."""
        with patch("os.path.exists", side_effect=Exception("Unexpected error")):

            # Should not raise exception due to handle_exceptions decorator
            result = initialize_repo(test_repo_path, test_remote_url, test_token)

            # Should return default_return_value (None) and not raise exception
            assert result is None
