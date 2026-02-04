# pylint: disable=unused-argument
import json
import subprocess
from typing import cast
from unittest.mock import MagicMock, mock_open, patch

import pytest

from constants.aws import EFS_TIMEOUT_SECONDS
from services.eslint.run_eslint_fix import run_eslint_fix
from services.github.types.github_types import BaseArgs


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
async def test_run_eslint_fix_skips_non_js_files(base_args):
    coro = run_eslint_fix(
        base_args=base_args,
        file_path="test.py",
        file_content="def foo(): pass",
    )
    assert coro is not None
    result = await coro
    assert result.content is None


@pytest.mark.asyncio
async def test_run_eslint_fix_skips_empty_content(base_args):
    coro = run_eslint_fix(
        base_args=base_args,
        file_path="test.ts",
        file_content="",
    )
    assert coro is not None
    result = await coro
    assert result.content is None


@pytest.mark.asyncio
async def test_run_eslint_fix_skips_whitespace_only(base_args):
    coro = run_eslint_fix(
        base_args=base_args,
        file_path="test.ts",
        file_content="   \n\t  ",
    )
    assert coro is not None
    result = await coro
    assert result.content is None


@pytest.mark.asyncio
async def test_run_eslint_fix_skips_when_no_config(base_args):
    with patch("services.eslint.run_eslint_fix.get_eslint_config", return_value=None):
        coro = run_eslint_fix(
            base_args=base_args,
            file_path="test.ts",
            file_content="const x = 1;",
        )
        assert coro is not None
        result = await coro
        assert result.content is None


@pytest.mark.asyncio
async def test_run_eslint_fix_sets_npm_cache_env_on_lambda(base_args):
    eslint_output = json.dumps([{"filePath": "test.ts", "messages": []}])

    def mock_set_npm_cache_env(env):
        env["npm_config_cache"] = "/tmp/.npm"

    with patch(
        "services.eslint.run_eslint_fix.get_eslint_config",
        return_value={"filename": ".eslintrc.json", "content": "{}"},
    ):
        with patch(
            "services.eslint.run_eslint_fix.set_npm_cache_env",
            side_effect=mock_set_npm_cache_env,
        ):
            with patch("services.eslint.run_eslint_fix.os.makedirs"):
                with patch("builtins.open", mock_open(read_data="formatted")):
                    with patch(
                        "services.eslint.run_eslint_fix.subprocess.run"
                    ) as mock_run:
                        mock_run.return_value = MagicMock(
                            returncode=0, stdout=eslint_output
                        )

                        coro = run_eslint_fix(
                            base_args=base_args,
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
async def test_run_eslint_fix_returns_fixed_content(base_args):
    fixed_content = "export const foo = 'fixed';\n"
    eslint_output = json.dumps([{"filePath": "test.js", "messages": []}])

    with patch(
        "services.eslint.run_eslint_fix.get_eslint_config",
        return_value={"filename": ".eslintrc.json", "content": "{}"},
    ):
        with patch("services.eslint.run_eslint_fix.os.makedirs"):
            with patch("builtins.open", mock_open(read_data=fixed_content)):
                with patch("services.eslint.run_eslint_fix.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0, stdout=eslint_output, stderr=""
                    )

                    coro = run_eslint_fix(
                        base_args=base_args,
                        file_path="test.js",
                        file_content="export const foo = 'bar';\n",
                    )
                    assert coro is not None
                    result = await coro

    assert result.content == fixed_content


@pytest.mark.asyncio
async def test_run_eslint_fix_with_unfixable_errors(base_args):
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
        "services.eslint.run_eslint_fix.get_eslint_config",
        return_value={"filename": ".eslintrc.json", "content": "{}"},
    ):
        with patch("services.eslint.run_eslint_fix.os.makedirs"):
            with patch("builtins.open", mock_open(read_data=file_content)):
                with patch("services.eslint.run_eslint_fix.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=1, stdout=eslint_output, stderr=""
                    )

                    with patch(
                        "services.eslint.run_eslint_fix.sentry_sdk.capture_message"
                    ):
                        coro = run_eslint_fix(
                            base_args=base_args,
                            file_path="test.js",
                            file_content=file_content,
                        )
                        assert coro is not None
                        result = await coro

    assert result.content == file_content


@pytest.mark.asyncio
async def test_run_eslint_fix_with_json_decode_error(base_args):
    file_content = "export const foo = 'bar';\n"

    with patch(
        "services.eslint.run_eslint_fix.get_eslint_config",
        return_value={"filename": ".eslintrc.json", "content": "{}"},
    ):
        with patch("services.eslint.run_eslint_fix.os.makedirs"):
            with patch("builtins.open", mock_open(read_data=file_content)):
                with patch("services.eslint.run_eslint_fix.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0, stdout="not json output", stderr=""
                    )

                    with patch(
                        "services.eslint.run_eslint_fix.sentry_sdk.capture_exception"
                    ):
                        coro = run_eslint_fix(
                            base_args=base_args,
                            file_path="test.js",
                            file_content=file_content,
                        )
                        assert coro is not None
                        result = await coro

    assert result.content == file_content


@pytest.mark.asyncio
async def test_run_eslint_fix_fatal_error_returns_none(base_args):
    with patch(
        "services.eslint.run_eslint_fix.get_eslint_config",
        return_value={"filename": ".eslintrc.json", "content": "{}"},
    ):
        with patch("services.eslint.run_eslint_fix.os.makedirs"):
            with patch("builtins.open", mock_open()):
                with patch("services.eslint.run_eslint_fix.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=2, stdout="", stderr="Fatal error"
                    )

                    coro = run_eslint_fix(
                        base_args=base_args,
                        file_path="test.js",
                        file_content="const x = 1;",
                    )
                    assert coro is not None
                    result = await coro

    assert result.content is None


@pytest.mark.asyncio
async def test_run_eslint_fix_timeout_returns_none(base_args):
    with patch(
        "services.eslint.run_eslint_fix.get_eslint_config",
        return_value={"filename": ".eslintrc.json", "content": "{}"},
    ):
        with patch("services.eslint.run_eslint_fix.os.makedirs"):
            with patch("builtins.open", mock_open()):
                with patch("services.eslint.run_eslint_fix.subprocess.run") as mock_run:
                    mock_run.side_effect = subprocess.TimeoutExpired(
                        cmd="npx eslint", timeout=EFS_TIMEOUT_SECONDS
                    )

                    coro = run_eslint_fix(
                        base_args=base_args,
                        file_path="test.js",
                        file_content="const x = 1;",
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
    ],
)
@pytest.mark.asyncio
async def test_run_eslint_fix_supported_extensions(base_args, file_path):
    eslint_output = json.dumps([{"filePath": file_path, "messages": []}])

    with patch(
        "services.eslint.run_eslint_fix.get_eslint_config",
        return_value={"filename": ".eslintrc.json", "content": "{}"},
    ):
        with patch("services.eslint.run_eslint_fix.os.makedirs"):
            with patch("builtins.open", mock_open(read_data="formatted")):
                with patch("services.eslint.run_eslint_fix.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0, stdout=eslint_output, stderr=""
                    )

                    coro = run_eslint_fix(
                        base_args=base_args,
                        file_path=file_path,
                        file_content="content",
                    )
                    assert coro is not None
                    result = await coro

                    mock_run.assert_called_once()
                    assert "npx" in mock_run.call_args[0][0]
                    assert "eslint" in mock_run.call_args[0][0]
                    assert result.content == "formatted"


@pytest.mark.asyncio
async def test_run_eslint_fix_creates_directories(base_args):
    file_content = "const x = 1;"
    eslint_output = json.dumps(
        [{"filePath": "src/deep/nested/test.js", "messages": []}]
    )

    with patch(
        "services.eslint.run_eslint_fix.get_eslint_config",
        return_value={"filename": ".eslintrc.json", "content": "{}"},
    ):
        with patch("services.eslint.run_eslint_fix.os.makedirs") as mock_makedirs:
            with patch("builtins.open", mock_open(read_data=file_content)):
                with patch("services.eslint.run_eslint_fix.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0, stdout=eslint_output, stderr=""
                    )

                    coro = run_eslint_fix(
                        base_args=base_args,
                        file_path="src/deep/nested/test.js",
                        file_content=file_content,
                    )
                    assert coro is not None
                    await coro

                    mock_makedirs.assert_called_once()


@pytest.mark.asyncio
async def test_run_eslint_fix_sets_flat_config_false_for_legacy_config(base_args):
    eslint_output = json.dumps([{"filePath": "test.ts", "messages": []}])

    with patch(
        "services.eslint.run_eslint_fix.get_eslint_config",
        return_value={"filename": ".eslintrc.json", "content": "{}"},
    ):
        with patch("services.eslint.run_eslint_fix.os.makedirs"):
            with patch("builtins.open", mock_open(read_data="formatted")):
                with patch("services.eslint.run_eslint_fix.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0, stdout=eslint_output
                    )

                    coro = run_eslint_fix(
                        base_args=base_args,
                        file_path="test.ts",
                        file_content="const x=1",
                    )
                    assert coro is not None
                    await coro

                    mock_run.assert_called_once()
                    call_kwargs = mock_run.call_args[1]
                    assert "env" in call_kwargs
                    assert call_kwargs["env"]["ESLINT_USE_FLAT_CONFIG"] == "false"


@pytest.mark.asyncio
async def test_run_eslint_fix_does_not_set_flat_config_for_new_config(base_args):
    eslint_output = json.dumps([{"filePath": "test.ts", "messages": []}])

    with patch(
        "services.eslint.run_eslint_fix.get_eslint_config",
        return_value={"filename": "eslint.config.js", "content": "export default {};"},
    ):
        with patch("services.eslint.run_eslint_fix.os.makedirs"):
            with patch("builtins.open", mock_open(read_data="formatted")):
                with patch("services.eslint.run_eslint_fix.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0, stdout=eslint_output
                    )

                    coro = run_eslint_fix(
                        base_args=base_args,
                        file_path="test.ts",
                        file_content="const x=1",
                    )
                    assert coro is not None
                    await coro

                    mock_run.assert_called_once()
                    call_kwargs = mock_run.call_args[1]
                    assert "env" in call_kwargs
                    assert "ESLINT_USE_FLAT_CONFIG" not in call_kwargs["env"]


@pytest.mark.parametrize(
    "config_filename",
    [
        ".eslintrc",
        ".eslintrc.json",
        ".eslintrc.js",
        ".eslintrc.yml",
        ".eslintrc.yaml",
    ],
)
@pytest.mark.asyncio
async def test_run_eslint_fix_legacy_config_variants(base_args, config_filename):
    eslint_output = json.dumps([{"filePath": "test.ts", "messages": []}])

    with patch(
        "services.eslint.run_eslint_fix.get_eslint_config",
        return_value={"filename": config_filename, "content": "{}"},
    ):
        with patch("services.eslint.run_eslint_fix.os.makedirs"):
            with patch("builtins.open", mock_open(read_data="formatted")):
                with patch("services.eslint.run_eslint_fix.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0, stdout=eslint_output
                    )

                    coro = run_eslint_fix(
                        base_args=base_args,
                        file_path="test.ts",
                        file_content="const x=1",
                    )
                    assert coro is not None
                    await coro

                    mock_run.assert_called_once()
                    call_kwargs = mock_run.call_args[1]
                    assert call_kwargs["env"]["ESLINT_USE_FLAT_CONFIG"] == "false"
