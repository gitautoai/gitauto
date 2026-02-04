# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch, MagicMock

import pytest

from services.github.types.github_types import BaseArgs
from services.jest.run_jest_test import run_jest_test


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_success(mock_exists, mock_subprocess):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is True
    assert result.errors == []
    assert result.error_files == set()


@pytest.mark.asyncio
async def test_run_jest_test_no_test_files():
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(
        base_args=base_args, file_paths=["src/index.ts", "README.md"]
    )
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_run_jest_test_no_clone_dir():
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "",
        },
    )
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_no_runner(mock_exists):
    mock_exists.return_value = False

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_with_failures(mock_exists, mock_subprocess):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="FAIL src/index.test.ts\n● Test suite failed to run\nError: Cannot find module",
        stderr="",
    )

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is False
    assert len(result.errors) > 0
    assert "src/index.test.ts" in result.error_files


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_uses_vitest_when_no_jest(mock_exists, mock_subprocess):
    def exists_side_effect(path):
        # Jest doesn't exist, but vitest does
        if "jest" in path:
            return False
        return "vitest" in path or "node_modules" in path

    mock_exists.side_effect = exists_side_effect
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is True

    # Verify vitest was called
    cmd = mock_subprocess.call_args[0][0]
    assert "vitest" in cmd[0]


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_spec_files(mock_exists, mock_subprocess):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(
        base_args=base_args,
        file_paths=["src/utils.spec.ts", "src/helper.spec.jsx"],
    )
    assert result.success is True

    # Verify both spec files were passed to the runner
    cmd = mock_subprocess.call_args[0][0]
    assert "src/utils.spec.ts" in cmd
    assert "src/helper.spec.jsx" in cmd


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_multiple_failures(mock_exists, mock_subprocess):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="FAIL src/a.test.ts\nFAIL src/b.test.ts\n● Error in test",
        stderr="",
    )

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(
        base_args=base_args, file_paths=["src/a.test.ts", "src/b.test.ts"]
    )
    assert result.success is False
    assert "src/a.test.ts" in result.error_files
    assert "src/b.test.ts" in result.error_files


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_type_error_in_output(mock_exists, mock_subprocess):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="TypeError: Cannot read property 'foo' of undefined",
        stderr="",
    )

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is False
    assert any("TypeError" in e for e in result.errors)
