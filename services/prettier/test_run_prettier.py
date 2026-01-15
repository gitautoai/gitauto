import subprocess
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from services.prettier.run_prettier import run_prettier


@pytest.mark.asyncio
async def test_run_prettier_success():
    with patch(
        "services.prettier.run_prettier.is_efs_install_ready", new_callable=AsyncMock
    ) as mock_efs:
        mock_efs.return_value = True
        with patch("services.prettier.run_prettier.os.makedirs"):
            with patch("builtins.open", mock_open()):
                with patch("services.prettier.run_prettier.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    with patch(
                        "builtins.open",
                        mock_open(read_data="const x = 1;\n"),
                    ):
                        coro = run_prettier(
                            owner="test-owner",
                            repo="test-repo",
                            clone_dir="/tmp/test-clone",
                            file_path="src/index.ts",
                            file_content="const x=1",
                        )
                        assert coro is not None
                        result = await coro

                        assert result == "const x = 1;\n"
                        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_run_prettier_empty_content():
    coro = run_prettier(
        owner="test-owner",
        repo="test-repo",
        clone_dir="/tmp/test-clone",
        file_path="src/index.ts",
        file_content="",
    )
    assert coro is not None
    result = await coro

    assert result is None


@pytest.mark.asyncio
async def test_run_prettier_whitespace_only():
    coro = run_prettier(
        owner="test-owner",
        repo="test-repo",
        clone_dir="/tmp/test-clone",
        file_path="src/index.ts",
        file_content="   \n\t  ",
    )
    assert coro is not None
    result = await coro

    assert result is None


@pytest.mark.asyncio
async def test_run_prettier_unsupported_file():
    coro = run_prettier(
        owner="test-owner",
        repo="test-repo",
        clone_dir="/tmp/test-clone",
        file_path="src/main.py",
        file_content="def foo(): pass",
    )
    assert coro is not None
    result = await coro

    assert result is None


@pytest.mark.asyncio
async def test_run_prettier_subprocess_failure():
    with patch(
        "services.prettier.run_prettier.is_efs_install_ready", new_callable=AsyncMock
    ) as mock_efs:
        mock_efs.return_value = True
        with patch("services.prettier.run_prettier.os.makedirs"):
            with patch("builtins.open", mock_open()):
                with patch("services.prettier.run_prettier.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=1, stderr="Prettier failed"
                    )

                    coro = run_prettier(
                        owner="test-owner",
                        repo="test-repo",
                        clone_dir="/tmp/test-clone",
                        file_path="src/index.ts",
                        file_content="const x=1",
                    )
                    assert coro is not None
                    result = await coro

                    assert result is None


@pytest.mark.asyncio
async def test_run_prettier_timeout():
    with patch(
        "services.prettier.run_prettier.is_efs_install_ready", new_callable=AsyncMock
    ) as mock_efs:
        mock_efs.return_value = True
        with patch("services.prettier.run_prettier.os.makedirs"):
            with patch("builtins.open", mock_open()):
                with patch("services.prettier.run_prettier.subprocess.run") as mock_run:
                    mock_run.side_effect = subprocess.TimeoutExpired(
                        cmd="npx prettier", timeout=30
                    )

                    coro = run_prettier(
                        owner="test-owner",
                        repo="test-repo",
                        clone_dir="/tmp/test-clone",
                        file_path="src/index.ts",
                        file_content="const x=1",
                    )
                    assert coro is not None
                    result = await coro

                    assert result is None


@pytest.mark.parametrize(
    "file_path",
    [
        "src/index.js",
        "src/app.jsx",
        "src/main.ts",
        "src/component.tsx",
        "config.json",
        "styles.css",
        "theme.scss",
        "README.md",
        "config.yaml",
        "settings.yml",
    ],
)
@pytest.mark.asyncio
async def test_run_prettier_supported_extensions(file_path):
    with patch(
        "services.prettier.run_prettier.is_efs_install_ready", new_callable=AsyncMock
    ) as mock_efs:
        mock_efs.return_value = True
        with patch("services.prettier.run_prettier.os.makedirs"):
            with patch("builtins.open", mock_open(read_data="formatted")):
                with patch("services.prettier.run_prettier.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    coro = run_prettier(
                        owner="test-owner",
                        repo="test-repo",
                        clone_dir="/tmp/test-clone",
                        file_path=file_path,
                        file_content="content",
                    )
                    assert coro is not None
                    result = await coro

                    mock_run.assert_called_once()
                    assert "npx" in mock_run.call_args[0][0]
                    assert "prettier" in mock_run.call_args[0][0]
                    assert result == "formatted"
