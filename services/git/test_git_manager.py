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
        result = fetch_branch(pull_number, branch_name, repo_dir)

        # Assertions
        assert result is None  # Function doesn't return anything on success
        mock_run.assert_called_once_with(
            "git fetch origin pull/123/head:feature-branch",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd="/path/to/repo",
        )

    @patch("subprocess.run")
    def test_fetch_branch_with_different_parameters(
        self, mock_run, mock_subprocess_run
    ):
        """Test fetch_branch with different parameter values"""
        mock_run.return_value = mock_subprocess_run

        # Test with different parameters
        pull_number = 456
        branch_name = "bugfix-branch"
        repo_dir = "/different/path"

        fetch_branch(pull_number, branch_name, repo_dir)

        mock_run.assert_called_once_with(
            "git fetch origin pull/456/head:bugfix-branch",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd="/different/path",
        )

    @patch("subprocess.run")
    def test_fetch_branch_subprocess_error_raises(self, mock_run):
        """Test that subprocess errors are raised due to handle_exceptions(raise_on_error=True)"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git fetch")

        with pytest.raises(subprocess.CalledProcessError):
            fetch_branch(123, "feature-branch", "/path/to/repo")

    @patch("subprocess.run")
    def test_fetch_branch_with_special_characters(self, mock_run, mock_subprocess_run):
        """Test fetch_branch with branch names containing special characters"""
        mock_run.return_value = mock_subprocess_run

        # Test with branch name containing special characters
        pull_number = 789
        branch_name = "feature/user-auth-fix"
        repo_dir = "/path/to/repo"

        fetch_branch(pull_number, branch_name, repo_dir)

        mock_run.assert_called_once_with(
            "git fetch origin pull/789/head:feature/user-auth-fix",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd="/path/to/repo",
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

        # Assertions
        assert result is None  # Function doesn't return anything
        mock_run.assert_called_once_with(
            "git branch --show-current",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd="/path/to/repo",
        )
        mock_print.assert_called_once_with("Current branch: `main`")

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_current_branch_with_different_branch(self, mock_print, mock_run):
        """Test current branch retrieval with different branch name"""
        mock_result = MagicMock()
        mock_result.stdout = "feature-branch\n"
        mock_run.return_value = mock_result

        get_current_branch("/different/path")

        mock_print.assert_called_once_with("Current branch: `feature-branch`")

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_current_branch_with_whitespace(self, mock_print, mock_run):
        """Test current branch retrieval with extra whitespace"""
        mock_result = MagicMock()
        mock_result.stdout = "  develop  \n"
        mock_run.return_value = mock_result

        get_current_branch("/path/to/repo")

        mock_print.assert_called_once_with("Current branch: `develop`")

    @patch("subprocess.run")
    def test_get_current_branch_subprocess_error_returns_none(self, mock_run):
        """Test that subprocess errors return None due to handle_exceptions(raise_on_error=False)"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git branch")

        result = get_current_branch("/path/to/repo")

        assert result is None

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_current_branch_with_non_ascii_characters(self, mock_print, mock_run):
        """Test current branch retrieval with non-ASCII characters in branch name"""
        mock_result = MagicMock()
        mock_result.stdout = "feature/café-auth-fix\n"
        mock_run.return_value = mock_result

        repo_dir = "/path/to/repo"
        get_current_branch(repo_dir)

        mock_print.assert_called_once_with("Current branch: `feature/café-auth-fix`")


class TestStartLocalServer:
    """Test cases for start_local_server function"""

    @patch("subprocess.Popen")
    def test_start_local_server_success(self, mock_popen, mock_subprocess_popen):
        """Test successful local server start"""
        mock_popen.return_value = mock_subprocess_popen

        repo_dir = "/path/to/repo"

        # Call function
        result = start_local_server(repo_dir)

        # Assertions
        assert result is mock_subprocess_popen
        mock_popen.assert_called_once_with(
            args="python -m http.server 8080",
            shell=True,
            cwd="/path/to/repo",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @patch("subprocess.Popen")
    def test_start_local_server_with_different_path(
        self, mock_popen, mock_subprocess_popen
    ):
        """Test server start with different repository path"""
        mock_popen.return_value = mock_subprocess_popen

        start_local_server("/different/repo/path")

        mock_popen.assert_called_once_with(
            args="python -m http.server 8080",
            shell=True,
            cwd="/different/repo/path",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @patch("subprocess.Popen")
    def test_start_local_server_popen_error_raises(self, mock_popen):
        """Test that Popen errors are raised due to handle_exceptions(raise_on_error=True)"""
        mock_popen.side_effect = OSError("Failed to start process")

        with pytest.raises(OSError):
            start_local_server("/path/to/repo")

    @patch("subprocess.Popen")
    def test_start_local_server_with_npm_command(self, mock_popen, mock_subprocess_popen):
        """Test server start with npm command (commented out in the code)"""
        # Create a modified version of the start_local_server function with npm command
        from services.git.git_manager import start_local_server
        
        # Store original function to restore later
        original_function = start_local_server
        
        # Create a patched version of the function
        def patched_start_local_server(repo_dir):
            command = "npm run dev"
            return subprocess.Popen(
                args=command, shell=True, cwd=repo_dir, 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        
        mock_popen.return_value = mock_subprocess_popen
        repo_dir = "/path/to/repo"

        # Skip this test as it's testing an implementation detail (commented code)
        pytest.skip("This test is for a commented-out code path that isn't currently used")


class TestSwitchToBranch:
    """Test cases for switch_to_branch function"""

    @patch("subprocess.run")
    def test_switch_to_branch_success(self, mock_run, mock_subprocess_run):
        """Test successful branch switch"""
        mock_run.return_value = mock_subprocess_run

        branch_name = "feature-branch"
        repo_dir = "/path/to/repo"

        # Call function
        result = switch_to_branch(branch_name, repo_dir)

        # Assertions
        assert result is None  # Function doesn't return anything on success
        mock_run.assert_called_once_with(
            "git switch feature-branch",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd="/path/to/repo",
        )

    @patch("subprocess.run")
    def test_switch_to_branch_with_special_characters(
        self, mock_run, mock_subprocess_run
    ):
        """Test branch switch with special characters in branch name"""
        mock_run.return_value = mock_subprocess_run

        switch_to_branch("feature/user-auth", "/path/to/repo")

        mock_run.assert_called_once_with(
            "git switch feature/user-auth",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd="/path/to/repo",
        )

    @patch("subprocess.run")
    def test_switch_to_branch_subprocess_error_raises(self, mock_run):
        """Test that subprocess errors are raised due to handle_exceptions(raise_on_error=True)"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git switch")

        with pytest.raises(subprocess.CalledProcessError):
            switch_to_branch("nonexistent-branch", "/path/to/repo")

    @patch("subprocess.run")
    def test_switch_to_branch_with_different_path(self, mock_run, mock_subprocess_run):
        """Test branch switch with different repository path"""
        mock_run.return_value = mock_subprocess_run

        switch_to_branch("develop", "/different/repo/path")

        mock_run.assert_called_once_with(
            "git switch develop",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd="/different/repo/path",
        )

    @patch("subprocess.run")
    def test_switch_to_branch_with_non_ascii_characters(self, mock_run, mock_subprocess_run):
        """Test branch switch with non-ASCII characters in branch name"""
        mock_run.return_value = mock_subprocess_run

        branch_name = "feature/café-auth"
        repo_dir = "/path/to/repo"

        switch_to_branch(branch_name, repo_dir)

        mock_run.assert_called_once_with(
            "git switch feature/café-auth",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd="/path/to/repo",
        )

    @patch("subprocess.run")
    def test_switch_to_branch_with_very_long_name(self, mock_run, mock_subprocess_run):
        """Test branch switch with a very long branch name"""
        mock_run.return_value = mock_subprocess_run

        long_branch_name = "feature/" + "x" * 100
        switch_to_branch(long_branch_name, "/path/to/repo")

        expected_cmd = f"git switch {long_branch_name}"
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == expected_cmd


class TestHandleExceptionsIntegration:
    """Test cases for handle_exceptions decorator integration"""

    @patch("subprocess.run")
    def test_fetch_branch_with_generic_exception_raises(self, mock_run):
        """Test that generic exceptions are raised due to handle_exceptions(raise_on_error=True)"""
        mock_run.side_effect = OSError("Permission denied")

        with pytest.raises(OSError):
            fetch_branch(123, "feature-branch", "/path/to/repo")

    @patch("subprocess.run")
    def test_get_current_branch_with_generic_exception_returns_none(self, mock_run):
        """Test that generic exceptions return None due to handle_exceptions(raise_on_error=False)"""
        mock_run.side_effect = OSError("Permission denied")

        result = get_current_branch("/path/to/repo")

        assert result is None

    @patch("subprocess.Popen")
    def test_start_local_server_with_generic_exception_raises(self, mock_popen):
        """Test that generic exceptions are raised due to handle_exceptions(raise_on_error=True)"""
        mock_popen.side_effect = PermissionError("Access denied")

        with pytest.raises(PermissionError):
            start_local_server("/path/to/repo")

    @patch("subprocess.run")
    def test_switch_to_branch_with_generic_exception_raises(self, mock_run):
        """Test that generic exceptions are raised due to handle_exceptions(raise_on_error=True)"""
        mock_run.side_effect = FileNotFoundError("Git not found")

        with pytest.raises(FileNotFoundError):
            switch_to_branch("feature-branch", "/path/to/repo")


class TestEdgeCases:
    """Test cases for edge cases and boundary conditions"""

    @patch("subprocess.run")
    def test_fetch_branch_with_zero_pull_number(self, mock_run, mock_subprocess_run):
        """Test fetch_branch with pull number 0"""
        mock_run.return_value = mock_subprocess_run

        fetch_branch(0, "branch", "/path")

        mock_run.assert_called_once_with(
            "git fetch origin pull/0/head:branch",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd="/path",
        )

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_get_current_branch_with_empty_output(self, mock_print, mock_run):
        """Test get_current_branch when git returns empty output"""
        mock_result = MagicMock()
        mock_result.stdout = "\n"
        mock_run.return_value = mock_result

        get_current_branch("/path/to/repo")

        mock_print.assert_called_once_with("Current branch: ``")

    @patch("subprocess.run")
    def test_switch_to_branch_with_empty_branch_name(
        self, mock_run, mock_subprocess_run
    ):
        """Test switch_to_branch with empty branch name"""
        mock_run.return_value = mock_subprocess_run

        switch_to_branch("", "/path/to/repo")

        mock_run.assert_called_once_with(
            "git switch ",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd="/path/to/repo",
        )

    @patch("subprocess.run")
    def test_fetch_branch_with_very_large_pull_number(self, mock_run, mock_subprocess_run):
        """Test fetch_branch with a very large pull number"""
        mock_run.return_value = mock_subprocess_run

        large_pull_number = 9999999999
        fetch_branch(large_pull_number, "branch", "/path")

        mock_run.assert_called_once_with(
            f"git fetch origin pull/{large_pull_number}/head:branch",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd="/path",
        )
