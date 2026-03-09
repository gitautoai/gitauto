import tempfile
from unittest.mock import MagicMock, patch

import pytest

from utils.command.run_subprocess import run_subprocess


def test_run_subprocess_success():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_subprocess(["echo", "hello"], temp_dir)
        assert result.returncode == 0
        assert "hello" in result.stdout


def test_run_subprocess_failure_raises_value_error():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError) as exc_info:
            run_subprocess(["nonexistent_command_xyz"], temp_dir)
        assert "Command failed:" in str(exc_info.value)


def test_run_subprocess_with_stderr_output():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError) as exc_info:
            run_subprocess(["sh", "-c", "echo error >&2; exit 1"], temp_dir)
        assert "Command failed:" in str(exc_info.value)


def test_run_subprocess_nonzero_returncode_raises():
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "some error"

    with patch("utils.command.run_subprocess.subprocess.run", return_value=mock_result):
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError) as exc_info:
                run_subprocess(["test_command"], temp_dir)
            assert "Command failed: some error" in str(exc_info.value)


@patch("utils.command.run_subprocess.subprocess.run")
def test_run_subprocess_subprocess_parameters(mock_run):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_subprocess(["git", "status"], temp_dir)

        mock_run.assert_called_once_with(
            args=["git", "status"],
            capture_output=True,
            check=False,
            cwd=temp_dir,
            text=True,
            shell=False,
        )
        assert result is mock_result


def test_run_subprocess_empty_command():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError):
            run_subprocess([], temp_dir)
