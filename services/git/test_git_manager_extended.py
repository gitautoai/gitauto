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


class TestIntegrationScenarios:
    """Integration-style test scenarios for git_manager functions"""

    @patch("subprocess.run")
    def test_fetch_and_switch_workflow(self, mock_run, mock_subprocess_run):
        """Test typical workflow of fetching and switching to a branch"""
        mock_run.return_value = mock_subprocess_run
        
        pull_number = 123
        branch_name = "pr-123"
        repo_dir = "/repo"
        
        # First fetch the branch
        fetch_branch(pull_number, branch_name, repo_dir)
        
        # Then switch to it
        switch_to_branch(branch_name, repo_dir)
        
        # Verify both commands were called
        assert mock_run.call_count == 2
        
        # Verify the commands
        calls = mock_run.call_args_list
        fetch_call = calls[0]
        switch_call = calls[1]
        
        assert fetch_call[0][0] == f"git fetch origin pull/{pull_number}/head:{branch_name}"
        assert switch_call[0][0] == f"git switch {branch_name}"

    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_complete_development_workflow(self, mock_popen, mock_run, mock_subprocess_run, mock_subprocess_popen):
        """Test complete workflow: fetch, switch, get current branch, start server"""
        mock_run.return_value = mock_subprocess_run
        mock_popen.return_value = mock_subprocess_popen
        
        repo_dir = "/repo"
        
        # Fetch branch
        fetch_branch(123, "feature", repo_dir)
        
        # Switch to branch
        switch_to_branch("feature", repo_dir)
        
        # Get current branch
        get_current_branch(repo_dir)
        
        # Start server
        server_process = start_local_server(repo_dir)
        
        # Verify all operations
        assert mock_run.call_count == 3  # fetch, switch, get_current_branch
        assert mock_popen.call_count == 1  # start_local_server
        assert server_process is mock_subprocess_popen


class TestErrorHandlingBehavior:
    """Test error handling behavior with handle_exceptions decorator"""

    @patch("subprocess.run")
    def test_functions_with_raise_on_error_true(self, mock_run):
        """Test that functions with raise_on_error=True actually raise exceptions"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git command")
        
        # These functions should raise exceptions
        with pytest.raises(subprocess.CalledProcessError):
            fetch_branch(123, "branch", "/repo")
            
        with pytest.raises(subprocess.CalledProcessError):
            switch_to_branch("branch", "/repo")

    @patch("subprocess.Popen")
    def test_start_local_server_with_raise_on_error_true(self, mock_popen):
        """Test that start_local_server raises exceptions when Popen fails"""
        mock_popen.side_effect = FileNotFoundError("python not found")
        
        with pytest.raises(FileNotFoundError):
            start_local_server("/repo")

    @patch("subprocess.run")
    def test_get_current_branch_with_raise_on_error_false(self, mock_run):
        """Test that get_current_branch returns None on error instead of raising"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git branch")
        
        # This function should return None instead of raising
        result = get_current_branch("/repo")
        assert result is None


class TestParameterValidation:
    """Test parameter handling and edge cases"""

    @patch("subprocess.run")
    def test_functions_with_empty_strings(self, mock_run, mock_subprocess_run):
        """Test functions with empty string parameters"""
        mock_run.return_value = mock_subprocess_run
        
        # Test with empty strings (should still work as they're valid parameters)
        fetch_branch(0, "", "")
        switch_to_branch("", "")
        get_current_branch("")
        
        assert mock_run.call_count == 3

    @patch("subprocess.Popen")
    def test_start_local_server_with_empty_repo_dir(self, mock_popen, mock_subprocess_popen):
        """Test start_local_server with empty repo directory"""
        mock_popen.return_value = mock_subprocess_popen
        
        result = start_local_server("")
        
        mock_popen.assert_called_once_with(
            args="python -m http.server 8080",
            shell=True,
            cwd="",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert result is mock_subprocess_popen

    @patch("subprocess.run")
    def test_fetch_branch_with_zero_pull_number(self, mock_run, mock_subprocess_run):
        """Test fetch_branch with pull number 0"""
        mock_run.return_value = mock_subprocess_run
        
        fetch_branch(0, "branch", "/repo")
        
        expected_cmd = "git fetch origin pull/0/head:branch"
        mock_run.assert_called_once_with(
            expected_cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd="/repo"
        )
