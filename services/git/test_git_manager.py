import subprocess
from unittest.mock import MagicMock, patch
import pytest
from services.git.git_manager import (
    fetch_branch,
    get_current_branch,
    start_local_server,
    switch_to_branch,
)


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run with successful result"""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "main\n"
    mock_result.stderr = ""
    return mock_result


@pytest.fixture
def mock_subprocess_popen():
    """Mock subprocess.Popen for server process"""
    mock_process = MagicMock()
    mock_process.pid = 12345
    return mock_process


class TestFetchBranch:
    """Test cases for fetch_branch function"""

    @patch("subprocess.run")
    def test_fetch_branch_success(self, mock_run, mock_subprocess_run):
        """Test successful branch fetch"""
        mock_run.return_value = mock_subprocess_run
        
        # Test parameters
        pull_number = 123
        branch_name = "feature-branch"
        repo_dir = "/path/to/repo"
        
        # Call function
        fetch_branch(pull_number, branch_name, repo_dir)
        
        # Verify subprocess.run was called with correct parameters
        expected_cmd = f"git fetch origin pull/{pull_number}/head:{branch_name}"
        mock_run.assert_called_once_with(
            expected_cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_dir
        )

    @patch("subprocess.run")
    def test_fetch_branch_with_different_parameters(self, mock_run, mock_subprocess_run):
        """Test fetch_branch with different parameter values"""
        mock_run.return_value = mock_subprocess_run
        
        # Test with different parameters
        pull_number = 456
        branch_name = "bugfix-issue-789"
        repo_dir = "/different/repo/path"
        
        fetch_branch(pull_number, branch_name, repo_dir)
        
        expected_cmd = f"git fetch origin pull/{pull_number}/head:{branch_name}"
        mock_run.assert_called_once_with(
            expected_cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_dir
        )

    @patch("subprocess.run")
    def test_fetch_branch_subprocess_error_raises(self, mock_run):
        """Test that subprocess errors are raised due to handle_exceptions(raise_on_error=True)"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git fetch")
        
        with pytest.raises(subprocess.CalledProcessError):
            fetch_branch(123, "test-branch", "/repo")

    @patch("subprocess.run")
    def test_fetch_branch_with_special_characters(self, mock_run, mock_subprocess_run):
        """Test fetch_branch with branch names containing special characters"""
        mock_run.return_value = mock_subprocess_run
        
        pull_number = 789
        branch_name = "feature/user-auth-2024"
        repo_dir = "/path/to/repo"
        
        fetch_branch(pull_number, branch_name, repo_dir)
        
        expected_cmd = f"git fetch origin pull/{pull_number}/head:{branch_name}"
        mock_run.assert_called_once_with(
            expected_cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_dir
        )


class TestGetCurrentBranch:
    """Test cases for get_current_branch function"""

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_current_branch_success(self, mock_print, mock_run):
        """Test successful current branch retrieval"""
        mock_result = MagicMock()
        mock_result.stdout = "main\n"
        mock_run.return_value = mock_result
        
        repo_dir = "/path/to/repo"
        
        # Call function
        result = get_current_branch(repo_dir)
        
        # Verify subprocess.run was called correctly
        mock_run.assert_called_once_with(
            "git branch --show-current",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_dir
        )
        
        # Verify print was called with correct message
        mock_print.assert_called_once_with("Current branch: `main`")
        
        # Function should return None due to no explicit return
        assert result is None

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_current_branch_with_different_branch(self, mock_print, mock_run):
        """Test get_current_branch with different branch name"""
        mock_result = MagicMock()
        mock_result.stdout = "feature-branch\n"
        mock_run.return_value = mock_result
        
        repo_dir = "/different/path"
        
        get_current_branch(repo_dir)
        
        mock_run.assert_called_once_with(
            "git branch --show-current",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_dir
        )
        
        mock_print.assert_called_once_with("Current branch: `feature-branch`")

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_current_branch_with_whitespace(self, mock_print, mock_run):
        """Test get_current_branch strips whitespace from output"""
        mock_result = MagicMock()
        mock_result.stdout = "  develop  \n"
        mock_run.return_value = mock_result
        
        get_current_branch("/repo")
        
        # Verify whitespace is stripped
        mock_print.assert_called_once_with("Current branch: `develop`")

    @patch("subprocess.run")
    def test_get_current_branch_subprocess_error_returns_none(self, mock_run):
        """Test that subprocess errors return None due to handle_exceptions(raise_on_error=False)"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git branch")
        
        result = get_current_branch("/repo")
        
        # Should return default_return_value=None when error occurs
        assert result is None

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_current_branch_empty_output(self, mock_print, mock_run):
        """Test get_current_branch with empty stdout"""
        mock_result = MagicMock()
        mock_result.stdout = "\n"
        mock_run.return_value = mock_result
        
        get_current_branch("/repo")
        
        mock_print.assert_called_once_with("Current branch: ``")


class TestStartLocalServer:
    """Test cases for start_local_server function"""

    @patch("subprocess.Popen")
    def test_start_local_server_success(self, mock_popen, mock_subprocess_popen):
        """Test successful server start"""
        mock_popen.return_value = mock_subprocess_popen
        
        repo_dir = "/path/to/repo"
        
        # Call function
        result = start_local_server(repo_dir)
        
        # Verify subprocess.Popen was called with correct parameters
        mock_popen.assert_called_once_with(
            args="python -m http.server 8080",
            shell=True,
            cwd=repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # Verify the process object is returned
        assert result is mock_subprocess_popen

    @patch("subprocess.Popen")
    def test_start_local_server_with_different_repo_dir(self, mock_popen, mock_subprocess_popen):
        """Test start_local_server with different repository directory"""
        mock_popen.return_value = mock_subprocess_popen
        
        repo_dir = "/different/repo/path"
        
        result = start_local_server(repo_dir)
        
        mock_popen.assert_called_once_with(
            args="python -m http.server 8080",
            shell=True,
            cwd=repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        assert result is mock_subprocess_popen

    @patch("subprocess.Popen")
    def test_start_local_server_popen_error_raises(self, mock_popen):
        """Test that Popen errors are raised due to handle_exceptions(raise_on_error=True)"""
        mock_popen.side_effect = OSError("Failed to start process")
        
        with pytest.raises(OSError):
            start_local_server("/repo")

    @patch("subprocess.Popen")
    def test_start_local_server_command_consistency(self, mock_popen, mock_subprocess_popen):
        """Test that the server command is consistent"""
        mock_popen.return_value = mock_subprocess_popen
        
        start_local_server("/repo")
        
        # Verify the exact command used
        call_args = mock_popen.call_args
        assert call_args[1]["args"] == "python -m http.server 8080"
        assert call_args[1]["shell"] is True
        assert call_args[1]["stdout"] == subprocess.PIPE
        assert call_args[1]["stderr"] == subprocess.PIPE


class TestSwitchToBranch:
    """Test cases for switch_to_branch function"""

    @patch("subprocess.run")
    def test_switch_to_branch_success(self, mock_run, mock_subprocess_run):
        """Test successful branch switch"""
        mock_run.return_value = mock_subprocess_run
        
        branch_name = "feature-branch"
        repo_dir = "/path/to/repo"
        
        # Call function
        switch_to_branch(branch_name, repo_dir)
        
        # Verify subprocess.run was called with correct parameters
        expected_cmd = f"git switch {branch_name}"
        mock_run.assert_called_once_with(
            expected_cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_dir
        )

    @patch("subprocess.run")
    def test_switch_to_branch_with_different_parameters(self, mock_run, mock_subprocess_run):
        """Test switch_to_branch with different parameter values"""
        mock_run.return_value = mock_subprocess_run
        
        branch_name = "main"
        repo_dir = "/different/repo/path"
        
        switch_to_branch(branch_name, repo_dir)
        
        expected_cmd = f"git switch {branch_name}"
        mock_run.assert_called_once_with(
            expected_cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_dir
        )

    @patch("subprocess.run")
    def test_switch_to_branch_subprocess_error_raises(self, mock_run):
        """Test that subprocess errors are raised due to handle_exceptions(raise_on_error=True)"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git switch")
        
        with pytest.raises(subprocess.CalledProcessError):
            switch_to_branch("nonexistent-branch", "/repo")

    @patch("subprocess.run")
    def test_switch_to_branch_with_special_characters(self, mock_run, mock_subprocess_run):
        """Test switch_to_branch with branch names containing special characters"""
        mock_run.return_value = mock_subprocess_run
        
        branch_name = "feature/user-auth-2024"
        repo_dir = "/path/to/repo"
        
        switch_to_branch(branch_name, repo_dir)
        
        expected_cmd = f"git switch {branch_name}"
        mock_run.assert_called_once_with(
            expected_cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_dir
        )

    @patch("subprocess.run")
    def test_switch_to_branch_with_remote_branch(self, mock_run, mock_subprocess_run):
        """Test switch_to_branch with remote branch reference"""
        mock_run.return_value = mock_subprocess_run
        
        branch_name = "origin/feature-branch"
        repo_dir = "/repo"
        
        switch_to_branch(branch_name, repo_dir)
        
        expected_cmd = f"git switch {branch_name}"
        mock_run.assert_called_once_with(
            expected_cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_dir
        )
