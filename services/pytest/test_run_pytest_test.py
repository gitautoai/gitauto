# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch, MagicMock

import pytest

from services.pytest.run_pytest_test import run_pytest_test


@pytest.mark.asyncio
@patch("services.pytest.run_pytest_test.subprocess.run")
@patch("services.pytest.run_pytest_test.os.path.exists")
async def test_run_pytest_test_success(
    mock_exists, mock_subprocess, create_test_base_args
):
    mock_exists.return_value = True  # venv/bin/pytest exists
    mock_subprocess.return_value = MagicMock(
        returncode=0, stdout="2 passed in 0.5s", stderr=""
    )

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_pytest_test(
        base_args=base_args,
        test_file_paths=["tests/test_utils.py", "tests/test_client.py"],
    )
    assert result.success is True
    assert result.errors == []
    assert result.error_files == set()


@pytest.mark.asyncio
async def test_run_pytest_test_no_test_files(create_test_base_args):
    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_pytest_test(
        base_args=base_args,
        test_file_paths=["src/main.py", "README.md"],
    )
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_run_pytest_test_no_clone_dir(create_test_base_args):
    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="",
    )
    result = await run_pytest_test(
        base_args=base_args,
        test_file_paths=["tests/test_utils.py"],
    )
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.pytest.run_pytest_test.shutil.which", return_value=None)
@patch("services.pytest.run_pytest_test.os.path.exists", return_value=False)
async def test_run_pytest_test_no_binary(
    mock_exists, mock_which, create_test_base_args
):
    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_pytest_test(
        base_args=base_args,
        test_file_paths=["tests/test_utils.py"],
    )
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.pytest.run_pytest_test.subprocess.run")
@patch("services.pytest.run_pytest_test.os.path.exists")
async def test_run_pytest_test_with_failures(
    mock_exists, mock_subprocess, create_test_base_args
):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="FAILED tests/test_utils.py::test_something - AssertionError\n1 failed",
        stderr="",
    )

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_pytest_test(
        base_args=base_args,
        test_file_paths=["tests/test_utils.py"],
    )
    assert result.success is False
    assert len(result.errors) > 0
    assert "tests/test_utils.py" in result.error_files


@pytest.mark.asyncio
@patch("services.pytest.run_pytest_test.subprocess.run")
@patch("services.pytest.run_pytest_test.os.path.exists")
async def test_run_pytest_test_exit_code_5_no_tests(
    mock_exists, mock_subprocess, create_test_base_args
):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=5,
        stdout="no tests ran in 0.01s",
        stderr="",
    )

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_pytest_test(
        base_args=base_args,
        test_file_paths=["tests/test_removed.py"],
    )
    assert result.success is True
    assert result.errors == []
    assert result.error_files == set()


@pytest.mark.asyncio
async def test_run_pytest_test_filters_non_python_files(create_test_base_args):
    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_pytest_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts", "README.md", "config.json"],
    )
    assert result.success is True
    assert result.errors == []
