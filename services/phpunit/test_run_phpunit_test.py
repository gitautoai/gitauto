# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch, MagicMock

import pytest

from services.phpunit.run_phpunit_test import run_phpunit_test
from services.types.base_args import BaseArgs


@pytest.mark.asyncio
@patch("services.phpunit.run_phpunit_test.subprocess.run")
@patch("services.phpunit.run_phpunit_test.os.path.exists")
async def test_run_phpunit_test_success(mock_exists, mock_subprocess):
    def exists_side_effect(path):
        if path == "/tmp/clone/vendor/bin/phpunit":
            return True
        if path.endswith("phpunit.xml") or path.endswith("phpunit.xml.dist"):
            return True
        return False

    mock_exists.side_effect = exists_side_effect
    mock_subprocess.return_value = MagicMock(
        returncode=0, stdout="OK (5 tests)", stderr=""
    )

    base_args = cast(
        BaseArgs, {"owner": "test", "repo": "test", "clone_dir": "/tmp/clone"}
    )
    result = await run_phpunit_test(
        base_args=base_args,
        test_file_paths=["tests/Unit/MyTest.php", "tests/Unit/FooTest.php"],
    )
    assert result.success is True
    assert result.errors == []
    assert result.error_files == set()


@pytest.mark.asyncio
async def test_run_phpunit_test_no_test_files():
    base_args = cast(
        BaseArgs, {"owner": "test", "repo": "test", "clone_dir": "/tmp/clone"}
    )
    result = await run_phpunit_test(
        base_args=base_args,
        test_file_paths=["src/Model.php", "README.md"],
    )
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_run_phpunit_test_no_clone_dir():
    base_args = cast(BaseArgs, {"owner": "test", "repo": "test", "clone_dir": ""})
    result = await run_phpunit_test(
        base_args=base_args,
        test_file_paths=["tests/Unit/MyTest.php"],
    )
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.phpunit.run_phpunit_test.os.path.exists", return_value=False)
async def test_run_phpunit_test_no_binary(mock_exists):
    base_args = cast(
        BaseArgs, {"owner": "test", "repo": "test", "clone_dir": "/tmp/clone"}
    )
    result = await run_phpunit_test(
        base_args=base_args,
        test_file_paths=["tests/Unit/MyTest.php"],
    )
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.phpunit.run_phpunit_test.subprocess.run")
@patch("services.phpunit.run_phpunit_test.os.path.exists")
async def test_run_phpunit_test_with_failures(mock_exists, mock_subprocess):
    def exists_side_effect(path):
        if path == "/tmp/clone/vendor/bin/phpunit":
            return True
        if path.endswith("phpunit.xml"):
            return True
        return False

    mock_exists.side_effect = exists_side_effect
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="FAILURES!\nTests: 3, Assertions: 5, Failures: 1.",
        stderr="",
    )

    base_args = cast(
        BaseArgs, {"owner": "test", "repo": "test", "clone_dir": "/tmp/clone"}
    )
    result = await run_phpunit_test(
        base_args=base_args,
        test_file_paths=["tests/Unit/MyTest.php"],
    )
    assert result.success is False
    assert len(result.errors) > 0
    assert "tests/Unit/MyTest.php" in result.error_files


@pytest.mark.asyncio
@patch("services.phpunit.run_phpunit_test.subprocess.run")
@patch("services.phpunit.run_phpunit_test.os.path.exists")
async def test_run_phpunit_test_exit_code_nonzero_but_ok(mock_exists, mock_subprocess):
    def exists_side_effect(path):
        if path == "/tmp/clone/vendor/bin/phpunit":
            return True
        if path.endswith("phpunit.xml"):
            return True
        return False

    mock_exists.side_effect = exists_side_effect
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="OK (10 tests, 25 assertions)\nDeprecation notices...",
        stderr="",
    )

    base_args = cast(
        BaseArgs, {"owner": "test", "repo": "test", "clone_dir": "/tmp/clone"}
    )
    result = await run_phpunit_test(
        base_args=base_args,
        test_file_paths=["tests/Unit/MyTest.php"],
    )
    assert result.success is True
    assert result.errors == []
    assert result.error_files == set()


@pytest.mark.asyncio
@patch("services.phpunit.run_phpunit_test.subprocess.run")
@patch("services.phpunit.run_phpunit_test.os.path.exists")
async def test_run_phpunit_test_multiple_failures(mock_exists, mock_subprocess):
    def exists_side_effect(path):
        if path == "/tmp/clone/vendor/bin/phpunit":
            return True
        if path.endswith("phpunit.xml"):
            return True
        return False

    mock_exists.side_effect = exists_side_effect
    # PHPUnit output mentions failing files
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="FAILURES!\ntests/Unit/ATest.php\ntests/Unit/BTest.php\nTests: 2, Assertions: 3, Failures: 2.",
        stderr="",
    )

    base_args = cast(
        BaseArgs, {"owner": "test", "repo": "test", "clone_dir": "/tmp/clone"}
    )
    result = await run_phpunit_test(
        base_args=base_args,
        test_file_paths=["tests/Unit/ATest.php", "tests/Unit/BTest.php"],
    )
    assert result.success is False
    assert "tests/Unit/ATest.php" in result.error_files
    assert "tests/Unit/BTest.php" in result.error_files


@pytest.mark.asyncio
@patch("services.phpunit.run_phpunit_test.subprocess.run")
@patch("services.phpunit.run_phpunit_test.os.path.exists")
async def test_run_phpunit_test_one_of_three_fails(mock_exists, mock_subprocess):
    def exists_side_effect(path):
        if path == "/tmp/clone/vendor/bin/phpunit":
            return True
        if path.endswith("phpunit.xml"):
            return True
        return False

    mock_exists.side_effect = exists_side_effect
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="FAILURES!\ntests/Unit/BTest.php failed\nTests: 3, Assertions: 5, Failures: 1.",
        stderr="",
    )

    base_args = cast(
        BaseArgs, {"owner": "test", "repo": "test", "clone_dir": "/tmp/clone"}
    )
    result = await run_phpunit_test(
        base_args=base_args,
        test_file_paths=[
            "tests/Unit/ATest.php",
            "tests/Unit/BTest.php",
            "tests/Unit/CTest.php",
        ],
    )
    assert result.success is False
    assert "tests/Unit/ATest.php" not in result.error_files
    assert "tests/Unit/BTest.php" in result.error_files
    assert "tests/Unit/CTest.php" not in result.error_files


@pytest.mark.asyncio
@patch("services.phpunit.run_phpunit_test.subprocess.run")
@patch("services.phpunit.run_phpunit_test.os.path.exists")
async def test_run_phpunit_test_all_three_fail(mock_exists, mock_subprocess):
    def exists_side_effect(path):
        if path == "/tmp/clone/vendor/bin/phpunit":
            return True
        if path.endswith("phpunit.xml"):
            return True
        return False

    mock_exists.side_effect = exists_side_effect
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="FAILURES!\ntests/Unit/ATest.php\ntests/Unit/BTest.php\ntests/Unit/CTest.php\nTests: 3, Assertions: 5, Failures: 3.",
        stderr="",
    )

    base_args = cast(
        BaseArgs, {"owner": "test", "repo": "test", "clone_dir": "/tmp/clone"}
    )
    result = await run_phpunit_test(
        base_args=base_args,
        test_file_paths=[
            "tests/Unit/ATest.php",
            "tests/Unit/BTest.php",
            "tests/Unit/CTest.php",
        ],
    )
    assert result.success is False
    assert "tests/Unit/ATest.php" in result.error_files
    assert "tests/Unit/BTest.php" in result.error_files
    assert "tests/Unit/CTest.php" in result.error_files


@pytest.mark.asyncio
@patch("services.phpunit.run_phpunit_test.subprocess.run")
@patch("services.phpunit.run_phpunit_test.os.path.exists")
async def test_run_phpunit_test_uses_bootstrap_when_no_config(
    mock_exists, mock_subprocess
):
    def exists_side_effect(path):
        if path == "/tmp/clone/vendor/bin/phpunit":
            return True
        if path == "/tmp/clone/vendor/autoload.php":
            return True
        # No phpunit.xml or phpunit.xml.dist
        return False

    mock_exists.side_effect = exists_side_effect
    mock_subprocess.return_value = MagicMock(
        returncode=0, stdout="OK (1 test)", stderr=""
    )

    base_args = cast(
        BaseArgs, {"owner": "test", "repo": "test", "clone_dir": "/tmp/clone"}
    )
    await run_phpunit_test(
        base_args=base_args,
        test_file_paths=["tests/Unit/MyTest.php"],
    )

    cmd = mock_subprocess.call_args[0][0]
    assert "--bootstrap" in cmd
    assert "/tmp/clone/vendor/autoload.php" in cmd


@pytest.mark.asyncio
@patch("services.phpunit.run_phpunit_test.subprocess.run")
@patch("services.phpunit.run_phpunit_test.os.path.exists")
async def test_run_phpunit_test_suppresses_deprecation_warnings(
    mock_exists, mock_subprocess
):
    def exists_side_effect(path):
        if path == "/tmp/clone/vendor/bin/phpunit":
            return True
        if path.endswith("phpunit.xml"):
            return True
        return False

    mock_exists.side_effect = exists_side_effect
    mock_subprocess.return_value = MagicMock(
        returncode=0, stdout="OK (1 test)", stderr=""
    )

    base_args = cast(
        BaseArgs, {"owner": "test", "repo": "test", "clone_dir": "/tmp/clone"}
    )
    await run_phpunit_test(
        base_args=base_args,
        test_file_paths=["tests/Unit/MyTest.php"],
    )

    cmd = mock_subprocess.call_args[0][0]
    assert "-d" in cmd
    assert "error_reporting=E_ALL&~E_DEPRECATED" in cmd


@pytest.mark.asyncio
async def test_run_phpunit_test_filters_non_php_files():
    base_args = cast(
        BaseArgs, {"owner": "test", "repo": "test", "clone_dir": "/tmp/clone"}
    )
    result = await run_phpunit_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts", "README.md", "config.json"],
    )
    assert result.success is True
    assert result.errors == []
