import os
import subprocess
import pytest
from unittest.mock import patch, MagicMock
from utils.command.run_command import run_command


def test_run_command_with_shell():
    """Test run_command with shell=True (default)."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "command output"
        mock_run.return_value = mock_result
        
        result = run_command("echo 'test'", cwd=".")
        
        mock_run.assert_called_once_with(
            args="echo 'test'",
            capture_output=True,
            check=True,
            cwd=".",
            text=True,
            shell=True,
            env=None,
        )
        assert result == mock_result


def test_run_command_without_shell():
    """Test run_command with shell=False."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_run.return_value = mock_result
        
        result = run_command("echo test", cwd=".", use_shell=False)
        
        mock_run.assert_called_once_with(
            args=["echo", "test"],
            capture_output=True,
            check=True,
            cwd=".",
            text=True,
            shell=False,
            env=None,
        )
        assert result == mock_result


def test_run_command_with_env():
    """Test run_command with custom environment variables."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_run.return_value = mock_result
        custom_env = {"TEST_VAR": "test_value"}
        
        result = run_command("echo $TEST_VAR", cwd=".", env=custom_env)
        
        mock_run.assert_called_once_with(
            args="echo $TEST_VAR",
            capture_output=True,
            check=True,
            cwd=".",
            text=True,
            shell=True,
            env=custom_env,
        )
        assert result == mock_result


def test_run_command_error_handling():
    """Test run_command error handling when command fails."""
    with patch('subprocess.run') as mock_run:
        # Create a CalledProcessError with stderr
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd="invalid_command",
        )
        error.stderr = "Command not found"
        mock_run.side_effect = error
        
        with pytest.raises(ValueError) as excinfo:
            run_command("invalid_command", cwd=".")
        assert "Command failed: Command not found" in str(excinfo.value)


def test_run_command_integration():
    """Integration test for run_command with a real command."""
    # Test with shell=True
    result = run_command("echo 'integration test'", cwd=".")
    assert result.stdout.strip() == "integration test"
    
    # Test with shell=False
    result = run_command("echo integration test", cwd=".", use_shell=False)
    assert result.stdout.strip() == "integration test"


def test_run_command_integration_error():
    """Integration test for run_command with a failing command."""
    # Use a command that should fail on any system
    with pytest.raises(ValueError) as excinfo:
        run_command("command_that_does_not_exist_anywhere", cwd=".")
    
    # The exact error message might vary by OS, but it should contain
    # some indication of failure
    assert "Command failed:" in str(excinfo.value)


def test_run_command_edge_cases():
    """Test run_command with edge cases."""
    # Test with empty command
    with pytest.raises(ValueError):
        run_command("", cwd=".")
    
    # Test with complex command with quotes and special characters
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_run.return_value = mock_result
        
        complex_command = "grep -E 'pattern with \"quotes\"' | sort | uniq"
        result = run_command(complex_command, cwd=".")
        
        mock_run.assert_called_once()
        assert result == mock_result