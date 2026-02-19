# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch, MagicMock

import pytest

from services.github.types.github_types import BaseArgs
from services.tsc.run_tsc_check import run_tsc_check


@pytest.mark.asyncio
@patch("services.tsc.run_tsc_check.subprocess.run")
@patch("services.tsc.run_tsc_check.os.path.exists")
async def test_run_tsc_check_success(mock_exists, mock_subprocess):
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
    result = await run_tsc_check(base_args=base_args, file_paths=["src/index.ts"])
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_run_tsc_check_no_ts_files():
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_tsc_check(
        base_args=base_args, file_paths=["src/index.js", "README.md"]
    )
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_run_tsc_check_no_clone_dir():
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "",
        },
    )
    result = await run_tsc_check(base_args=base_args, file_paths=["src/index.ts"])
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.tsc.run_tsc_check.os.path.exists")
async def test_run_tsc_check_no_tsconfig(mock_exists):
    mock_exists.return_value = False

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_tsc_check(base_args=base_args, file_paths=["src/index.ts"])
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.tsc.run_tsc_check.subprocess.run")
@patch("services.tsc.run_tsc_check.os.path.exists")
async def test_run_tsc_check_with_errors(mock_exists, mock_subprocess):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="src/index.ts(10,5): error TS2322: Type 'string' is not assignable to type 'number'.",
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
    result = await run_tsc_check(base_args=base_args, file_paths=["src/index.ts"])
    assert result.success is False
    assert len(result.errors) == 1
    assert "TS2322" in result.errors[0]
    assert result.error_files == {"src/index.ts"}


@pytest.mark.asyncio
@patch("services.tsc.run_tsc_check.subprocess.run")
@patch("services.tsc.run_tsc_check.os.path.exists")
async def test_run_tsc_check_errors_in_node_modules_excluded(
    mock_exists, mock_subprocess
):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="node_modules/some-lib/index.d.ts(10,5): error TS2322: Type error.",
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
    result = await run_tsc_check(base_args=base_args, file_paths=["src/index.ts"])
    # Errors in node_modules still cause failure but excluded from error_files
    assert result.success is False
    assert len(result.errors) == 1
    assert result.error_files == set()


@pytest.mark.asyncio
@patch("services.tsc.run_tsc_check.os.path.exists")
async def test_run_tsc_check_no_tsc_binary(mock_exists):
    def exists_side_effect(path):
        # tsconfig exists but tsc binary does not
        if "node_modules" in path:
            return False
        return "tsconfig.json" in path

    mock_exists.side_effect = exists_side_effect

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_tsc_check(base_args=base_args, file_paths=["src/index.ts"])
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.tsc.run_tsc_check.subprocess.run")
@patch("services.tsc.run_tsc_check.os.path.exists")
async def test_run_tsc_check_with_empty_lines_in_output(mock_exists, mock_subprocess):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="src/index.ts(1,5): error TS2322: Type error.\n\n\nsrc/other.ts(2,3): error TS1234: Another error.",
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
    result = await run_tsc_check(base_args=base_args, file_paths=["src/index.ts"])
    assert result.success is False
    # Empty lines should be skipped, only 2 errors
    assert len(result.errors) == 2
    assert result.error_files == {"src/index.ts", "src/other.ts"}


@pytest.mark.asyncio
@patch("services.tsc.run_tsc_check.subprocess.run")
@patch("services.tsc.run_tsc_check.os.path.exists")
async def test_run_tsc_check_disables_incremental(mock_exists, mock_subprocess):
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
    await run_tsc_check(base_args=base_args, file_paths=["src/index.ts"])

    # Verify --incremental false is passed to avoid stale .tsbuildinfo cache errors
    cmd = mock_subprocess.call_args[0][0]
    assert "--incremental" in cmd
    assert "false" in cmd


@pytest.mark.asyncio
@patch("services.tsc.run_tsc_check.subprocess.run")
@patch("services.tsc.run_tsc_check.os.path.exists")
async def test_run_tsc_check_uses_test_config_when_only_one(
    mock_exists, mock_subprocess
):
    def exists_side_effect(path):
        # Only tsconfig.test.json exists
        return "tsconfig.test.json" in path or "node_modules" in path

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
    await run_tsc_check(base_args=base_args, file_paths=["src/index.ts"])

    # Verify tsconfig.test.json was used
    cmd = mock_subprocess.call_args[0][0]
    assert "-p" in cmd
    assert "tsconfig.test.json" in cmd


@pytest.mark.asyncio
@patch("services.tsc.run_tsc_check.subprocess.run")
@patch("services.tsc.run_tsc_check.os.path.exists")
async def test_run_tsc_check_uses_base_config_when_multiple_test_configs(
    mock_exists, mock_subprocess
):
    def exists_side_effect(path):
        # Multiple test configs exist, plus base config
        return (
            "tsconfig.test.json" in path
            or "tsconfig.spec.json" in path
            or "tsconfig.json" in path
            or "node_modules" in path
        )

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
    await run_tsc_check(base_args=base_args, file_paths=["src/index.ts"])

    # Verify tsconfig.json was used (fallback when multiple test configs)
    cmd = mock_subprocess.call_args[0][0]
    assert "-p" in cmd
    assert "tsconfig.json" in cmd
