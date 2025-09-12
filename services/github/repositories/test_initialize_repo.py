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
            mock_file.assert_called_once_with(expected_readme_path, "w", encoding="utf-8")

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
        ) as mock_run_command, patch("builtins.print") as mock_print:

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

    def test_initialize_repo_with_different_remote_url_formats(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_token,
    ):
        """Test initialization with different remote URL formats."""
        test_cases = [
            "https://github.com/owner/repo.git",
            "https://github.com/owner/repo",
            "https://github.com/org-name/repo-name.git",
        ]

        for remote_url in test_cases:
            with patch("os.path.exists", return_value=True), patch(
                "builtins.open", mock_open()
            ), patch(
                "services.github.repositories.initialize_repo.run_command"
            ) as mock_run_command:

                initialize_repo(test_repo_path, remote_url, test_token)

                # Verify the token was correctly inserted into the URL
                expected_auth_url = remote_url.replace(
                    "https://", f"https://x-access-token:{test_token}@"
                )
                
                # Check that the authenticated URL was used in git commands
                remote_add_call = call(
                    command=f"git remote add origin {expected_auth_url}",
                    cwd=test_repo_path,
                )
                assert remote_add_call in mock_run_command.call_args_list

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
            assert "- [GitAuto demo](https://www.youtube.com/watch?v=demo)" in written_content
            assert "- [GitAuto use cases](https://gitauto.ai/blog)" in written_content
            assert "- [GitAuto LinkedIn](https://www.linkedin.com/company/gitauto/)" in written_content
            assert "- [GitAuto Twitter](https://x.com/gitautoai)" in written_content
            assert "- [GitAuto YouTube](https://youtube.com/@gitauto)" in written_content

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

    def test_initialize_repo_with_empty_parameters(
        self,
        mock_config_constants,
        mock_url_constants,
    ):
        """Test initialization with empty parameters."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ):

            # Test with empty strings
            result = initialize_repo("", "", "")
            assert result is None

    def test_initialize_repo_token_injection_security(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_token,
    ):
        """Test that token injection works correctly and securely."""
        malicious_url = "https://evil.com/repo.git"
        
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command:

            initialize_repo(test_repo_path, malicious_url, test_token)

            # Verify token is correctly injected into any URL
            expected_auth_url = f"https://x-access-token:{test_token}@evil.com/repo.git"
            remote_add_call = call(
                command=f"git remote add origin {expected_auth_url}",
                cwd=test_repo_path,
            )
            assert remote_add_call in mock_run_command.call_args_list

    def test_initialize_repo_print_statements_success(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that print statements are called correctly for successful remote add."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ), patch("builtins.print") as mock_print:

            initialize_repo(test_repo_path, test_remote_url, test_token)

            # Verify print statements for successful remote add
            expected_calls = [
                call(f"Adding remote: {test_remote_url}"),
                call("Remote added successfully"),
            ]
            mock_print.assert_has_calls(expected_calls)

    def test_initialize_repo_directory_already_exists(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that no directory creation occurs when directory already exists."""
        with patch("os.path.exists", return_value=True), patch(
            "os.makedirs"
        ) as mock_makedirs, patch("builtins.open", mock_open()), patch(
            "services.github.repositories.initialize_repo.run_command"
        ):

            initialize_repo(test_repo_path, test_remote_url, test_token)

            # Verify makedirs was not called since directory exists
            mock_makedirs.assert_not_called()

    def test_initialize_repo_git_init_command_format(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that git init command uses main branch."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command:

            initialize_repo(test_repo_path, test_remote_url, test_token)

            # Verify git init command uses main branch
            init_call = call(command="git init -b main", cwd=test_repo_path)
            assert init_call in mock_run_command.call_args_list

    def test_initialize_repo_commit_message_format(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that commit message is correctly formatted."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command:

            initialize_repo(test_repo_path, test_remote_url, test_token)

            # Verify commit command with correct message
            commit_call = call(
                command='git commit -m "Initial commit with README"',
                cwd=test_repo_path,
            )
            assert commit_call in mock_run_command.call_args_list

    def test_initialize_repo_push_command_format(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that push command uses correct format."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command:

            initialize_repo(test_repo_path, test_remote_url, test_token)

            # Verify push command format
            push_call = call(command="git push -u origin main", cwd=test_repo_path)
            assert push_call in mock_run_command.call_args_list

    def test_initialize_repo_exception_in_remote_add_fallback(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test exception handling in remote add with fallback to set-url."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command:

            # Make only the remote add command fail
            def side_effect(command, cwd):
                if "git remote add origin" in command:
                    raise ValueError("Remote add failed")
                return MagicMock()

            mock_run_command.side_effect = side_effect

            result = initialize_repo(test_repo_path, test_remote_url, test_token)

            # Should still return None (successful execution with fallback)
            assert result is None

            # Verify both remote add and set-url were attempted
            add_call = call(
                command=f"git remote add origin https://x-access-token:{test_token}@github.com/test-owner/test-repo.git",
                cwd=test_repo_path,
            )
            set_url_call = call(
                command=f"git remote set-url origin https://x-access-token:{test_token}@github.com/test-owner/test-repo.git",
                cwd=test_repo_path,
            )

            assert add_call in mock_run_command.call_args_list
            assert set_url_call in mock_run_command.call_args_list

    def test_initialize_repo_readme_file_path_construction(
        self,
        mock_config_constants,
        mock_url_constants,
        test_remote_url,
        test_token,
    ):
        """Test that README.md file path is constructed correctly."""
        custom_path = "/custom/path/to/repo"
        
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ) as mock_file, patch(
            "services.github.repositories.initialize_repo.run_command"
        ):

            initialize_repo(custom_path, test_remote_url, test_token)

            # Verify README.md path construction
            expected_readme_path = os.path.join(custom_path, "README.md")
            mock_file.assert_called_once_with(expected_readme_path, "w", encoding="utf-8")

    def test_initialize_repo_all_git_commands_use_correct_cwd(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that all git commands use the correct working directory."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command:

            initialize_repo(test_repo_path, test_remote_url, test_token)

            # Verify all git commands use the correct cwd
            for call_args in mock_run_command.call_args_list:
                assert call_args[1]["cwd"] == test_repo_path

    def test_initialize_repo_with_special_characters_in_path(
        self,
        mock_config_constants,
        mock_url_constants,
        test_remote_url,
        test_token,
    ):
        """Test initialization with special characters in path."""
        special_path = "/tmp/test-repo with spaces & symbols"
        
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ) as mock_file, patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command:

            initialize_repo(special_path, test_remote_url, test_token)

            # Verify README.md path construction with special characters
            expected_readme_path = os.path.join(special_path, "README.md")
            mock_file.assert_called_once_with(expected_readme_path, "w", encoding="utf-8")

            # Verify all git commands use the special path
            for call_args in mock_run_command.call_args_list:
                assert call_args[1]["cwd"] == special_path

    def test_initialize_repo_with_special_characters_in_token(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
    ):
        """Test initialization with special characters in token."""
        special_token = "ghp_token_with_special_chars!@#$%^&*()"
        
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command:

            initialize_repo(test_repo_path, test_remote_url, special_token)

            # Verify token is correctly injected even with special characters
            expected_auth_url = f"https://x-access-token:{special_token}@github.com/test-owner/test-repo.git"
            remote_add_call = call(
                command=f"git remote add origin {expected_auth_url}",
                cwd=test_repo_path,
            )
            assert remote_add_call in mock_run_command.call_args_list

    def test_initialize_repo_command_execution_order(
        self,
        mock_config_constants,
        mock_url_constants,
        test_repo_path,
        test_remote_url,
        test_token,
    ):
        """Test that git commands are executed in the correct order."""
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open()
        ), patch(
            "services.github.repositories.initialize_repo.run_command"
        ) as mock_run_command:

            initialize_repo(test_repo_path, test_remote_url, test_token)

            # Verify the exact order of git commands
            call_commands = [call.args[1]["command"] for call in mock_run_command.call_args_list]
