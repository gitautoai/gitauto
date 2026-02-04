# pylint: disable=unused-argument
import subprocess
from typing import cast
from unittest.mock import MagicMock, mock_open, patch

import pytest

from constants.aws import EFS_TIMEOUT_SECONDS
from services.github.types.github_types import BaseArgs
from services.prettier.run_prettier_fix import run_prettier_fix


@pytest.fixture
def base_args():
    return cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "token": "test-token",
            "base_branch": "main",
            "clone_dir": "/tmp/test-clone",
        },
    )


@pytest.mark.asyncio
async def test_run_prettier_fix_success(base_args):
    with patch(
        "services.prettier.run_prettier_fix.get_prettier_config",
        return_value={"filename": ".prettierrc", "content": "{}"},
    ):
        with patch(
            "services.prettier.run_prettier_fix.get_efs_dir",
            return_value="/mnt/efs/test",
        ):
            with patch("services.prettier.run_prettier_fix.extract_dependencies"):
                with patch("services.prettier.run_prettier_fix.os.makedirs"):
                    with patch("builtins.open", mock_open()):
                        with patch(
                            "services.prettier.run_prettier_fix.subprocess.run"
                        ) as mock_run:
                            mock_run.return_value = MagicMock(returncode=0)

                            with patch(
                                "builtins.open",
                                mock_open(read_data="const x = 1;\n"),
                            ):
                                coro = run_prettier_fix(
                                    base_args=base_args,
                                    file_path="src/index.ts",
                                    file_content="const x=1",
                                )
                                assert coro is not None
                                result = await coro

                                assert result.content == "const x = 1;\n"
                                mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_run_prettier_fix_sets_npm_cache_env_on_lambda(base_args):
    def mock_set_npm_cache_env(env):
        env["npm_config_cache"] = "/tmp/.npm"

    with patch(
        "services.prettier.run_prettier_fix.get_prettier_config",
        return_value={"filename": ".prettierrc", "content": "{}"},
    ):
        with patch(
            "services.prettier.run_prettier_fix.set_npm_cache_env",
            side_effect=mock_set_npm_cache_env,
        ):
            with patch(
                "services.prettier.run_prettier_fix.get_efs_dir",
                return_value="/mnt/efs/test",
            ):
                with patch("services.prettier.run_prettier_fix.extract_dependencies"):
                    with patch("services.prettier.run_prettier_fix.os.makedirs"):
                        with patch("builtins.open", mock_open(read_data="formatted")):
                            with patch(
                                "services.prettier.run_prettier_fix.subprocess.run"
                            ) as mock_run:
                                mock_run.return_value = MagicMock(returncode=0)

                                coro = run_prettier_fix(
                                    base_args=base_args,
                                    file_path="src/index.ts",
                                    file_content="const x=1",
                                )
                                assert coro is not None
                                await coro

                                mock_run.assert_called_once()
                                call_kwargs = mock_run.call_args[1]
                                assert "env" in call_kwargs
                                assert (
                                    call_kwargs["env"]["npm_config_cache"]
                                    == "/tmp/.npm"
                                )


@pytest.mark.asyncio
async def test_run_prettier_fix_empty_content(base_args):
    coro = run_prettier_fix(
        base_args=base_args,
        file_path="src/index.ts",
        file_content="",
    )
    assert coro is not None
    result = await coro

    assert result.content is None


@pytest.mark.asyncio
async def test_run_prettier_fix_whitespace_only(base_args):
    coro = run_prettier_fix(
        base_args=base_args,
        file_path="src/index.ts",
        file_content="   \n\t  ",
    )
    assert coro is not None
    result = await coro

    assert result.content is None


@pytest.mark.asyncio
async def test_run_prettier_fix_unsupported_file(base_args):
    coro = run_prettier_fix(
        base_args=base_args,
        file_path="src/main.py",
        file_content="def foo(): pass",
    )
    assert coro is not None
    result = await coro

    assert result.content is None


@pytest.mark.asyncio
async def test_run_prettier_fix_skips_when_no_config(base_args):
    with patch(
        "services.prettier.run_prettier_fix.get_prettier_config", return_value=None
    ):
        coro = run_prettier_fix(
            base_args=base_args,
            file_path="src/index.ts",
            file_content="const x = 1;",
        )
        assert coro is not None
        result = await coro
        assert result.content is None


@pytest.mark.asyncio
async def test_run_prettier_fix_subprocess_failure(base_args):
    with patch(
        "services.prettier.run_prettier_fix.get_prettier_config",
        return_value={"filename": ".prettierrc", "content": "{}"},
    ):
        with patch(
            "services.prettier.run_prettier_fix.get_efs_dir",
            return_value="/mnt/efs/test",
        ):
            with patch("services.prettier.run_prettier_fix.extract_dependencies"):
                with patch("services.prettier.run_prettier_fix.os.makedirs"):
                    with patch("builtins.open", mock_open()):
                        with patch(
                            "services.prettier.run_prettier_fix.subprocess.run"
                        ) as mock_run:
                            mock_run.return_value = MagicMock(
                                returncode=1, stderr="Prettier failed"
                            )

                            coro = run_prettier_fix(
                                base_args=base_args,
                                file_path="src/index.ts",
                                file_content="const x=1",
                            )
                            assert coro is not None
                            result = await coro

                            assert result.content is None


@pytest.mark.asyncio
async def test_run_prettier_fix_timeout(base_args):
    with patch(
        "services.prettier.run_prettier_fix.get_prettier_config",
        return_value={"filename": ".prettierrc", "content": "{}"},
    ):
        with patch(
            "services.prettier.run_prettier_fix.get_efs_dir",
            return_value="/mnt/efs/test",
        ):
            with patch("services.prettier.run_prettier_fix.extract_dependencies"):
                with patch("services.prettier.run_prettier_fix.os.makedirs"):
                    with patch("builtins.open", mock_open()):
                        with patch(
                            "services.prettier.run_prettier_fix.subprocess.run"
                        ) as mock_run:
                            mock_run.side_effect = subprocess.TimeoutExpired(
                                cmd="npx prettier", timeout=EFS_TIMEOUT_SECONDS
                            )

                            coro = run_prettier_fix(
                                base_args=base_args,
                                file_path="src/index.ts",
                                file_content="const x=1",
                            )
                            assert coro is not None
                            result = await coro

                            assert result.content is None


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
async def test_run_prettier_fix_supported_extensions(base_args, file_path):
    with patch(
        "services.prettier.run_prettier_fix.get_prettier_config",
        return_value={"filename": ".prettierrc", "content": "{}"},
    ):
        with patch(
            "services.prettier.run_prettier_fix.get_efs_dir",
            return_value="/mnt/efs/test",
        ):
            with patch("services.prettier.run_prettier_fix.extract_dependencies"):
                with patch("services.prettier.run_prettier_fix.os.makedirs"):
                    with patch("builtins.open", mock_open(read_data="formatted")):
                        with patch(
                            "services.prettier.run_prettier_fix.subprocess.run"
                        ) as mock_run:
                            mock_run.return_value = MagicMock(returncode=0)

                            coro = run_prettier_fix(
                                base_args=base_args,
                                file_path=file_path,
                                file_content="content",
                            )
                            assert coro is not None
                            result = await coro

                            mock_run.assert_called_once()
                            assert "npx" in mock_run.call_args[0][0]
                            assert "prettier" in mock_run.call_args[0][0]
                            assert result.content == "formatted"
