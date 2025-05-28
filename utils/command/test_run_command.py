import subprocess
import tempfile
import os
from unittest.mock import patch, MagicMock
import pytest
from utils.command.run_command import run_command


def test_run_command_success_with_shell():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_command("echo hello", temp_dir, use_shell=True)
        assert result.returncode == 0
        assert "hello" in result.stdout


def test_run_command_success_without_shell():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_command("echo hello", temp_dir, use_shell=False)
        assert result.returncode == 0
        assert "hello" in result.stdout


def test_run_command_with_custom_env():
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_env = os.environ.copy()
        custom_env["TEST_VAR"] = "test_value"
        
        if os.name == 'nt':
            command = "echo %TEST_VAR%"
        else:
            command = "echo $TEST_VAR"
        
        result = run_command(command, temp_dir, use_shell=True, env=custom_env)
        assert result.returncode == 0
        assert "test_value" in result.stdout


def test_run_command_with_none_env():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_command("echo hello", temp_dir, use_shell=True, env=None)
        assert result.returncode == 0
        assert "hello" in result.stdout


def test_run_command_command_split_without_shell():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_command("echo hello world", temp_dir, use_shell=False)
        assert result.returncode == 0
        assert "hello world" in result.stdout


def test_run_command_complex_command_without_shell():
    with tempfile.TemporaryDirectory() as temp_dir:
        if os.name == 'nt':
            result = run_command("cmd /c echo test", temp_dir, use_shell=False)
        else:
            result = run_command("sh -c echo test", temp_dir, use_shell=False)
        assert result.returncode == 0


def test_run_command_failure_raises_value_error():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError) as exc_info:
            run_command("nonexistent_command_xyz", temp_dir, use_shell=True)
        assert "Command failed:" in str(exc_info.value)


def test_run_command_failure_without_shell():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError) as exc_info:
            run_command("nonexistent_command_xyz", temp_dir, use_shell=False)
        assert "Command failed:" in str(exc_info.value)


def test_run_command_with_stderr_output():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError) as exc_info:
            if os.name == 'nt':
                run_command("cmd /c exit 1", temp_dir, use_shell=True)
            else:
                run_command("sh -c 'echo error >&2; exit 1'", temp_dir, use_shell=True)
        assert "Command failed:" in str(exc_info.value)


@patch('subprocess.run')
def test_run_command_called_process_error_with_stderr(mock_run):
    mock_error = subprocess.CalledProcessError(1, "test_command")
    mock_error.stderr = "test error message"
    mock_run.side_effect = mock_error
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError) as exc_info:
            run_command("test_command", temp_dir)
        
        assert "Command failed: test error message" in str(exc_info.value)
        assert exc_info.value.__cause__ is mock_error


@patch('subprocess.run')
def test_run_command_called_process_error_without_stderr(mock_run):
    mock_error = subprocess.CalledProcessError(1, "test_command")
    mock_error.stderr = None
    mock_run.side_effect = mock_error
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError) as exc_info:
            run_command("test_command", temp_dir)
        
        assert "Command failed: None" in str(exc_info.value)
        assert exc_info.value.__cause__ is mock_error


@patch('subprocess.run')
def test_run_command_subprocess_parameters(mock_run):
    mock_result = MagicMock()
    mock_run.return_value = mock_result
    
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_env = {"TEST": "value"}
        result = run_command("test command", temp_dir, use_shell=False, env=custom_env)
        
        mock_run.assert_called_once_with(
            args=["test", "command"],
            capture_output=True,
            check=True,
            cwd=temp_dir,
            text=True,
            shell=False,
            env=custom_env,
        )
        assert result is mock_result


def test_run_command_empty_command_without_shell():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError) as exc_info:
            run_command("", temp_dir, use_shell=False)
        assert "Command cannot be empty when use_shell is False" in str(exc_info.value)
