import json
import subprocess
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from services.eslint.run_eslint import run_eslint


@pytest.mark.asyncio
async def test_run_eslint_skips_non_js_files():
    coro = run_eslint(
        owner="test-owner",
        repo="test-repo",
        clone_dir="/tmp/test-clone",
        file_path="test.py",
        file_content="def foo(): pass",
    )
    assert coro is not None
    result = await coro

    assert result is None


@pytest.mark.asyncio
async def test_run_eslint_skips_empty_content():
    coro = run_eslint(
        owner="test-owner",
        repo="test-repo",
        clone_dir="/tmp/test-clone",
        file_path="test.ts",
        file_content="",
    )
    assert coro is not None
    result = await coro

    assert result is None


@pytest.mark.asyncio
async def test_run_eslint_skips_whitespace_only():
    coro = run_eslint(
        owner="test-owner",
        repo="test-repo",
        clone_dir="/tmp/test-clone",
        file_path="test.ts",
        file_content="   \n\t  ",
    )
    assert coro is not None
    result = await coro

    assert result is None


@pytest.mark.asyncio
async def test_run_eslint_sets_npm_cache_env_on_lambda():
    eslint_output = json.dumps([{"filePath": "test.ts", "messages": []}])

    def mock_set_npm_cache_env(env):
        env["npm_config_cache"] = "/tmp/.npm"

    with patch(
        "services.eslint.run_eslint.set_npm_cache_env",
        side_effect=mock_set_npm_cache_env,
    ):
        with patch(
            "services.eslint.run_eslint.is_efs_install_ready", new_callable=AsyncMock
        ) as mock_efs:
            mock_efs.return_value = True
            with patch("services.eslint.run_eslint.os.makedirs"):
                with patch("builtins.open", mock_open(read_data="formatted")):
                    with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                        mock_run.return_value = MagicMock(
                            returncode=0, stdout=eslint_output
                        )

                        coro = run_eslint(
                            owner="test-owner",
                            repo="test-repo",
                            clone_dir="/tmp/test-clone",
                            file_path="src/index.ts",
                            file_content="const x=1",
                        )
                        assert coro is not None
                        await coro

                        mock_run.assert_called_once()
                        call_kwargs = mock_run.call_args[1]
                        assert "env" in call_kwargs
                        assert call_kwargs["env"]["npm_config_cache"] == "/tmp/.npm"


@pytest.mark.asyncio
async def test_run_eslint_returns_fixed_content():
    fixed_content = "export const foo = 'fixed';\n"
    eslint_output = json.dumps([{"filePath": "test.js", "messages": []}])

    with patch(
        "services.eslint.run_eslint.is_efs_install_ready", new_callable=AsyncMock
    ) as mock_efs:
        mock_efs.return_value = True
        with patch("services.eslint.run_eslint.os.makedirs"):
            with patch("builtins.open", mock_open(read_data=fixed_content)):
                with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0, stdout=eslint_output, stderr=""
                    )

                    coro = run_eslint(
                        owner="test-owner",
                        repo="test-repo",
                        clone_dir="/tmp/test-clone",
                        file_path="test.js",
                        file_content="export const foo = 'bar';\n",
                    )
                    assert coro is not None
                    result = await coro

    assert result == fixed_content


@pytest.mark.asyncio
async def test_run_eslint_with_unfixable_errors():
    file_content = "export const foo = 'bar';\n"
    eslint_output = json.dumps(
        [
            {
                "filePath": "test.js",
                "messages": [
                    {
                        "line": 1,
                        "column": 1,
                        "message": "Unexpected var",
                        "ruleId": "no-var",
                        "severity": 2,
                    }
                ],
            }
        ]
    )

    with patch(
        "services.eslint.run_eslint.is_efs_install_ready", new_callable=AsyncMock
    ) as mock_efs:
        mock_efs.return_value = True
        with patch("services.eslint.run_eslint.os.makedirs"):
            with patch("builtins.open", mock_open(read_data=file_content)):
                with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=1, stdout=eslint_output, stderr=""
                    )

                    with patch("services.eslint.run_eslint.sentry_sdk.capture_message"):
                        coro = run_eslint(
                            owner="test-owner",
                            repo="test-repo",
                            clone_dir="/tmp/test-clone",
                            file_path="test.js",
                            file_content=file_content,
                        )
                        assert coro is not None
                        result = await coro

    assert result == file_content


@pytest.mark.asyncio
async def test_run_eslint_with_json_decode_error():
    file_content = "export const foo = 'bar';\n"

    with patch(
        "services.eslint.run_eslint.is_efs_install_ready", new_callable=AsyncMock
    ) as mock_efs:
        mock_efs.return_value = True
        with patch("services.eslint.run_eslint.os.makedirs"):
            with patch("builtins.open", mock_open(read_data=file_content)):
                with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0, stdout="not json output", stderr=""
                    )

                    with patch(
                        "services.eslint.run_eslint.sentry_sdk.capture_exception"
                    ):
                        coro = run_eslint(
                            owner="test-owner",
                            repo="test-repo",
                            clone_dir="/tmp/test-clone",
                            file_path="test.js",
                            file_content=file_content,
                        )
                        assert coro is not None
                        result = await coro

    assert result == file_content


@pytest.mark.asyncio
async def test_run_eslint_fatal_error_returns_none():
    with patch(
        "services.eslint.run_eslint.is_efs_install_ready", new_callable=AsyncMock
    ) as mock_efs:
        mock_efs.return_value = True
        with patch("services.eslint.run_eslint.os.makedirs"):
            with patch("builtins.open", mock_open()):
                with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=2, stdout="", stderr="Fatal error"
                    )

                    coro = run_eslint(
                        owner="test-owner",
                        repo="test-repo",
                        clone_dir="/tmp/test-clone",
                        file_path="test.js",
                        file_content="const x = 1;",
                    )
                    assert coro is not None
                    result = await coro

    assert result is None


@pytest.mark.asyncio
async def test_run_eslint_timeout_returns_none():
    with patch(
        "services.eslint.run_eslint.is_efs_install_ready", new_callable=AsyncMock
    ) as mock_efs:
        mock_efs.return_value = True
        with patch("services.eslint.run_eslint.os.makedirs"):
            with patch("builtins.open", mock_open()):
                with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                    mock_run.side_effect = subprocess.TimeoutExpired(
                        cmd="npx eslint", timeout=30
                    )

                    coro = run_eslint(
                        owner="test-owner",
                        repo="test-repo",
                        clone_dir="/tmp/test-clone",
                        file_path="test.js",
                        file_content="const x = 1;",
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
    ],
)
@pytest.mark.asyncio
async def test_run_eslint_supported_extensions(file_path):
    eslint_output = json.dumps([{"filePath": file_path, "messages": []}])

    with patch(
        "services.eslint.run_eslint.is_efs_install_ready", new_callable=AsyncMock
    ) as mock_efs:
        mock_efs.return_value = True
        with patch("services.eslint.run_eslint.os.makedirs"):
            with patch("builtins.open", mock_open(read_data="formatted")):
                with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0, stdout=eslint_output, stderr=""
                    )

                    coro = run_eslint(
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
                    assert "eslint" in mock_run.call_args[0][0]
                    assert result == "formatted"


@pytest.mark.asyncio
async def test_run_eslint_creates_directories():
    file_content = "const x = 1;"
    eslint_output = json.dumps(
        [{"filePath": "src/deep/nested/test.js", "messages": []}]
    )

    with patch(
        "services.eslint.run_eslint.is_efs_install_ready", new_callable=AsyncMock
    ) as mock_efs:
        mock_efs.return_value = True
        with patch("services.eslint.run_eslint.os.makedirs") as mock_makedirs:
            with patch("builtins.open", mock_open(read_data=file_content)):
                with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0, stdout=eslint_output, stderr=""
                    )

                    coro = run_eslint(
                        owner="test-owner",
                        repo="test-repo",
                        clone_dir="/tmp/test-clone",
                        file_path="src/deep/nested/test.js",
                        file_content=file_content,
                    )
                    assert coro is not None
                    await coro

                    mock_makedirs.assert_called_once()
