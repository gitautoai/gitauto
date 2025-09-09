import subprocess
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from services.git.git_manager import (
    fetch_branch,
    get_current_branch,
    start_local_server,
    switch_to_branch,
)


class TestFetchBranch:
    """Test cases for fetch_branch function."""

    def test_fetch_branch_success(self):
        """Test successful branch fetching."""
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Call the function
            fetch_branch(123, "feature-branch", "/tmp/repo")

            # Verify subprocess.run was called with correct arguments
            expected_cmd = "git fetch origin pull/123/head:feature-branch"
            mock_run.assert_called_once_with(
                expected_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                cwd="/tmp/repo",
            )

    def test_fetch_branch_subprocess_error(self):
        """Test error handling when subprocess.run fails."""
        with patch("subprocess.run") as mock_run:
            # Create a subprocess error
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd="git fetch",
                output="",
                stderr="fatal: couldn't find remote ref",
            )

            # The function should raise an exception due to raise_on_error=True
            with pytest.raises(subprocess.CalledProcessError):
                fetch_branch(999, "non-existent-branch", "/tmp/repo")

    def test_fetch_branch_with_different_parameters(self):
        """Test fetch_branch with various parameter combinations."""
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Test with different pull number and branch name
            fetch_branch(456, "hotfix/urgent-fix", "/path/to/repo")

            expected_cmd = "git fetch origin pull/456/head:hotfix/urgent-fix"
            mock_run.assert_called_once_with(
                expected_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                cwd="/path/to/repo",
            )


class TestGetCurrentBranch:
    """Test cases for get_current_branch function."""

    def test_get_current_branch_success(self, capsys):
        """Test successful current branch retrieval."""
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "main\n"
            mock_run.return_value = mock_process

            # Call the function
            get_current_branch("/tmp/repo")

            # Verify subprocess.run was called with correct arguments
            expected_cmd = "git branch --show-current"
            mock_run.assert_called_once_with(
                expected_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                cwd="/tmp/repo",
            )

            # Verify the print output
            captured = capsys.readouterr()
            assert "Current branch: `main`" in captured.out

    def test_get_current_branch_with_whitespace(self, capsys):
        """Test current branch retrieval with whitespace in output."""
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "  feature/test-branch  \n"
            mock_run.return_value = mock_process

            # Call the function
            get_current_branch("/tmp/repo")

            # Verify the print output strips whitespace
            captured = capsys.readouterr()
            assert "Current branch: `feature/test-branch`" in captured.out

    def test_get_current_branch_subprocess_error(self):
        """Test error handling when subprocess.run fails."""
        with patch("subprocess.run") as mock_run:
            # Create a subprocess error
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=128,
                cmd="git branch --show-current",
                output="",
                stderr="fatal: not a git repository",
            )

            # The function should return None due to raise_on_error=False
            result = get_current_branch("/not/a/repo")
            assert result is None

    def test_get_current_branch_empty_output(self, capsys):
        """Test current branch retrieval with empty output."""
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = ""
            mock_run.return_value = mock_process

            # Call the function
            get_current_branch("/tmp/repo")

            # Verify the print output handles empty string
            captured = capsys.readouterr()
            assert "Current branch: ``" in captured.out


class TestStartLocalServer:
    """Test cases for start_local_server function."""

    def test_start_local_server_success(self):
        """Test successful local server start."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            # Call the function
            result = start_local_server("/tmp/repo")

            # Verify subprocess.Popen was called with correct arguments
            expected_command = "python -m http.server 8080"
            mock_popen.assert_called_once_with(
                args=expected_command,
                shell=True,
                cwd="/tmp/repo",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Verify the function returns the process
            assert result == mock_process

    def test_start_local_server_with_different_repo_dir(self):
        """Test start_local_server with different repository directory."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            # Call the function with different repo directory
            result = start_local_server("/path/to/project")

            # Verify subprocess.Popen was called with correct cwd
            mock_popen.assert_called_once_with(
                args="python -m http.server 8080",
                shell=True,
                cwd="/path/to/project",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            assert result == mock_process

    def test_start_local_server_popen_error(self):
        """Test error handling when subprocess.Popen fails."""
        with patch("subprocess.Popen") as mock_popen:
            # Create a subprocess error
            mock_popen.side_effect = OSError("Permission denied")

            # The function should raise an exception due to raise_on_error=True
            with pytest.raises(OSError):
                start_local_server("/tmp/repo")


class TestSwitchToBranch:
    """Test cases for switch_to_branch function."""

    def test_switch_to_branch_success(self):
        """Test successful branch switching."""
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Call the function
            switch_to_branch("feature-branch", "/tmp/repo")

            # Verify subprocess.run was called with correct arguments
            expected_cmd = "git switch feature-branch"
            mock_run.assert_called_once_with(
                expected_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                cwd="/tmp/repo",
            )

    def test_switch_to_branch_subprocess_error(self):
        """Test error handling when subprocess.run fails."""
        with patch("subprocess.run") as mock_run:
            # Create a subprocess error
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd="git switch",
                output="",
                stderr="fatal: invalid reference: non-existent-branch",
            )

            # The function should raise an exception due to raise_on_error=True
            with pytest.raises(subprocess.CalledProcessError):
                switch_to_branch("non-existent-branch", "/tmp/repo")

    def test_switch_to_branch_with_special_characters(self):
        """Test switch_to_branch with branch names containing special characters."""
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Test with branch name containing special characters
            switch_to_branch("feature/fix-issue-#123", "/tmp/repo")

            expected_cmd = "git switch feature/fix-issue-#123"
            mock_run.assert_called_once_with(
                expected_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                cwd="/tmp/repo",
            )

    def test_switch_to_branch_with_different_repo_paths(self):
        """Test switch_to_branch with various repository paths."""
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Test with absolute path
            switch_to_branch("main", "/home/user/projects/repo")

            expected_cmd = "git switch main"
            mock_run.assert_called_once_with(
                expected_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                cwd="/home/user/projects/repo",
            )


class TestIntegrationScenarios:
    """Integration test scenarios combining multiple functions."""

    def test_typical_workflow_scenario(self):
        """Test a typical workflow: fetch branch, switch to it, get current branch."""
        with patch("subprocess.run") as mock_run, patch("subprocess.Popen") as mock_popen:
            # Setup mocks for successful operations
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "feature-branch\n"
            mock_run.return_value = mock_process

            mock_server_process = MagicMock()
            mock_popen.return_value = mock_server_process

            repo_dir = "/tmp/test-repo"

            # Execute typical workflow
            fetch_branch(123, "feature-branch", repo_dir)
            switch_to_branch("feature-branch", repo_dir)
            get_current_branch(repo_dir)
            server_process = start_local_server(repo_dir)

            # Verify all operations were called
            assert mock_run.call_count == 3
            mock_popen.assert_called_once()
            assert server_process == mock_server_process

    def test_error_recovery_scenario(self):
        """Test error scenarios and recovery patterns."""
        with patch("subprocess.run") as mock_run:
            # First call fails, second succeeds
            mock_run.side_effect = [
                subprocess.CalledProcessError(1, "git fetch", "", "network error"),
                MagicMock(returncode=0),
            ]

            # First fetch should fail
            with pytest.raises(subprocess.CalledProcessError):
                fetch_branch(123, "feature-branch", "/tmp/repo")

            # Second operation should succeed
            switch_to_branch("main", "/tmp/repo")

            assert mock_run.call_count == 2


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_parameters(self):
        """Test functions with empty string parameters."""
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Test with empty branch name (should still work as git command)
            switch_to_branch("", "/tmp/repo")

            expected_cmd = "git switch "
            mock_run.assert_called_once_with(
                expected_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                cwd="/tmp/repo",
            )

    def test_zero_pull_number(self):
        """Test fetch_branch with zero pull number."""
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Test with pull number 0
            fetch_branch(0, "branch", "/tmp/repo")

            expected_cmd = "git fetch origin pull/0/head:branch"
            mock_run.assert_called_once_with(
                expected_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                cwd="/tmp/repo",
            )

    def test_large_pull_number(self):
        """Test fetch_branch with large pull number."""
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Test with large pull number
            large_pr_number = 999999
            fetch_branch(large_pr_number, "branch", "/tmp/repo")

            expected_cmd = f"git fetch origin pull/{large_pr_number}/head:branch"
            mock_run.assert_called_once_with(
                expected_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                cwd="/tmp/repo",
            )

    def test_unicode_branch_names(self):
        """Test functions with unicode characters in branch names."""
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Test with unicode branch name
            unicode_branch = "feature/测试-branch-🚀"
            switch_to_branch(unicode_branch, "/tmp/repo")

            expected_cmd = f"git switch {unicode_branch}"
            mock_run.assert_called_once_with(
                expected_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                cwd="/tmp/repo",
            )