import subprocess
import tempfile
import os
import pytest
from unittest.mock import patch, MagicMock
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


def test_run_command_with_env():
    with tempfile.TemporaryDirectory() as temp_dir:
        env = {"TEST_VAR": "test_value"}
        result = run_command("echo $TEST_VAR", temp_dir, use_shell=True, env=env)
        assert result.returncode == 0
        assert "test_value" in result.stdout


def test_run_command_with_none_env():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_command("echo hello", temp_dir, use_shell=True, env=None)
        assert result.returncode == 0
        assert "hello" in result.stdout


def test_run_command_failure():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError, match="Command failed:"):
            run_command("exit 1", temp_dir, use_shell=True)


def test_run_command_failure_with_stderr():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError, match="Command failed:"):
            run_command("echo error >&2; exit 1", temp_dir, use_shell=True)


def test_run_command_different_cwd():
    with tempfile.TemporaryDirectory() as temp_dir:
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)
        result = run_command("pwd", subdir, use_shell=True)
        assert result.returncode == 0
        assert subdir in result.stdout


@patch('subprocess.run')
def test_run_command_shell_true_args(mock_run):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    
    run_command("echo test", "/tmp", use_shell=True)
    
    mock_run.assert_called_once_with(
        args="echo test",
        capture_output=True,
        check=True,
        cwd="/tmp",
        text=True,
        shell=True,
        env=None,
    )


@patch('subprocess.run')
def test_run_command_shell_false_args(mock_run):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    
    run_command("echo test", "/tmp", use_shell=False)
    
    mock_run.assert_called_once_with(
        args=["echo", "test"],
        capture_output=True,
        check=True,
        cwd="/tmp",
        text=True,
        shell=False,
        env=None,
    )


@patch('subprocess.run')
def test_run_command_exception_handling(mock_run):
    mock_error = subprocess.CalledProcessError(1, "test_command")
    mock_error.stderr = "test error message"
    mock_run.side_effect = mock_error
    
    with pytest.raises(ValueError, match="Command failed: test error message"):
        run_command("test_command", "/tmp")


def test_run_command_complex_command_with_shell():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_command("echo 'hello world' | wc -w", temp_dir, use_shell=True)
        assert result.returncode == 0
        assert "2" in result.stdout.strip()


def test_run_command_multiword_without_shell():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_command("echo hello world", temp_dir, use_shell=False)
        assert result.returncode == 0
        assert "hello world" in result.stdout


def test_run_command_empty_command_with_shell():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_command("", temp_dir, use_shell=True)
        assert result.returncode == 0


def test_run_command_empty_command_without_shell():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError):
            run_command("", temp_dir, use_shell=False)


@patch('subprocess.run')
def test_run_command_with_custom_env(mock_run):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    
    custom_env = {"PATH": "/custom/path", "HOME": "/custom/home"}
    run_command("echo test", "/tmp", use_shell=True, env=custom_env)


def test_run_command_with_special_chars():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_command("echo 'special chars: !@#$%^&*()'", temp_dir, use_shell=True)
        assert result.returncode == 0
        assert "special chars: !@#$%^&*()" in result.stdout


def test_run_command_with_multiple_commands():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_command("echo 'first' && echo 'second'", temp_dir, use_shell=True)
        assert result.returncode == 0
        assert "first" in result.stdout
        assert "second" in result.stdout


@patch('subprocess.run')
def test_run_command_exception_with_empty_stderr(mock_run):
    mock_error = subprocess.CalledProcessError(1, "test_command")
    mock_error.stderr = ""
    mock_run.side_effect = mock_error
    
    with pytest.raises(ValueError, match="Command failed:"):
