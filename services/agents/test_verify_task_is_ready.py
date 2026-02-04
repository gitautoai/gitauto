# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch, AsyncMock

import pytest

from services.agents.verify_task_is_ready import verify_task_is_ready
from services.eslint.run_eslint_fix import ESLintResult
from services.github.types.github_types import BaseArgs
from services.jest.run_jest_test import JestResult
from services.prettier.run_prettier_fix import PrettierResult
from services.tsc.run_tsc_check import TscResult


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.replace_remote_file_content")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_valid_file_returns_success(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_replace
):
    mock_get_raw_content.return_value = "function foo() { return 1; }"
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(success=True, content=None, error=None)
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "token": "test",
            "base_branch": "main",
        },
    )
    result = await verify_task_is_ready(
        base_args=base_args, file_paths=["src/index.ts"]
    )
    assert result.success is True
    assert result.errors == []
    assert result.fixes_applied == []
    assert result.files_with_errors == set()
    mock_replace.assert_not_called()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.replace_remote_file_content")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_prettier_fails_returns_errors(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_replace
):
    mock_get_raw_content.return_value = "function foo() { return 1;"
    mock_prettier.return_value = PrettierResult(
        success=False, content=None, error="SyntaxError: Unexpected token"
    )
    mock_eslint.return_value = ESLintResult(success=True, content=None, error=None)
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "token": "test",
            "base_branch": "main",
        },
    )
    result = await verify_task_is_ready(
        base_args=base_args, file_paths=["src/broken.ts"]
    )
    assert result.success is False
    assert len(result.errors) == 1
    assert "SyntaxError" in result.errors[0]
    assert result.fixes_applied == []
    assert result.files_with_errors == {"src/broken.ts"}


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.replace_remote_file_content")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_eslint_fails_returns_errors(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_replace
):
    mock_get_raw_content.return_value = "function foo() { return 1; }"
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=False, content=None, error="Parsing error: Unexpected token"
    )
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "token": "test",
            "base_branch": "main",
        },
    )
    result = await verify_task_is_ready(
        base_args=base_args, file_paths=["src/broken.ts"]
    )
    assert result.success is False
    assert len(result.errors) == 1
    assert "Parsing error" in result.errors[0]
    assert result.fixes_applied == []
    assert result.files_with_errors == {"src/broken.ts"}


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_non_js_files_skipped(mock_get_raw_content):
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "token": "test",
            "base_branch": "main",
        },
    )
    result = await verify_task_is_ready(
        base_args=base_args, file_paths=["README.md", "config.json"]
    )
    assert result.success is True
    assert result.errors == []
    assert result.fixes_applied == []
    assert result.files_with_errors == set()
    mock_get_raw_content.assert_not_called()


@pytest.mark.asyncio
async def test_empty_file_list():
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "token": "test",
            "base_branch": "main",
        },
    )
    result = await verify_task_is_ready(base_args=base_args, file_paths=[])
    assert result.success is True
    assert result.errors == []
    assert result.fixes_applied == []
    assert result.files_with_errors == set()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.replace_remote_file_content")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_file_not_found_skipped(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_replace
):
    mock_get_raw_content.return_value = None
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "token": "test",
            "base_branch": "main",
        },
    )
    result = await verify_task_is_ready(
        base_args=base_args, file_paths=["src/missing.ts"]
    )
    assert result.success is True
    assert result.errors == []
    assert result.fixes_applied == []
    assert result.files_with_errors == set()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.replace_remote_file_content")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_fixes_applied_and_pushed(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_replace
):
    original = "function foo() { return 1; }"
    formatted = "function foo() {\n  return 1;\n}"
    mock_get_raw_content.return_value = original
    mock_prettier.return_value = PrettierResult(
        success=True, content=formatted, error=None
    )
    mock_eslint.return_value = ESLintResult(success=True, content=None, error=None)
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "token": "test",
            "base_branch": "main",
        },
    )
    result = await verify_task_is_ready(
        base_args=base_args, file_paths=["src/index.ts"]
    )
    assert result.success is True
    assert result.errors == []
    assert result.fixes_applied == ["- src/index.ts: Prettier"]
    assert result.files_with_errors == set()
    mock_replace.assert_called_once()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.replace_remote_file_content")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_eslint_partial_fix_pushes_and_reports_errors(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_replace
):
    original = "const x = 1\nconst unused = 2;"
    fixed = "const x = 1;\nconst unused = 2;"
    mock_get_raw_content.return_value = original
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=False,
        content=fixed,
        error="Line 2: 'unused' is defined but never used (no-unused-vars)",
    )
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "token": "test",
            "base_branch": "main",
        },
    )
    result = await verify_task_is_ready(
        base_args=base_args, file_paths=["src/index.ts"]
    )
    assert result.success is False
    assert len(result.errors) == 1
    assert "unused" in result.errors[0]
    assert result.fixes_applied == ["- src/index.ts: ESLint"]
    assert result.files_with_errors == {"src/index.ts"}
    mock_replace.assert_called_once()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.run_tsc_check")
@patch("services.agents.verify_task_is_ready.replace_remote_file_content")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_run_tsc_reports_type_errors(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_replace, mock_tsc
):
    mock_get_raw_content.return_value = "const x: number = 'hello';"
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(success=True, content=None, error=None)
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[
            "src/index.ts(1,7): error TS2322: Type 'string' is not assignable to type 'number'."
        ],
        error_files={"src/index.ts"},
    )

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "token": "test",
            "base_branch": "main",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await verify_task_is_ready(
        base_args=base_args, file_paths=["src/index.ts"], run_tsc=True
    )
    assert result.success is False
    assert len(result.errors) == 1
    assert "TS2322" in result.errors[0]
    assert result.files_with_errors == {"src/index.ts"}


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.run_jest_test")
@patch("services.agents.verify_task_is_ready.replace_remote_file_content")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_run_jest_reports_test_failures(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_replace, mock_jest
):
    mock_get_raw_content.return_value = (
        "describe('test', () => { it('fails', () => { expect(true).toBe(false); }); });"
    )
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(success=True, content=None, error=None)
    mock_jest.return_value = JestResult(
        success=False,
        errors=["FAIL src/index.test.ts", "Expected true to be false"],
        error_files={"src/index.test.ts"},
        runner_name="jest",
    )

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "token": "test",
            "base_branch": "main",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await verify_task_is_ready(
        base_args=base_args, file_paths=["src/index.test.ts"], run_jest=True
    )
    assert result.success is False
    assert len(result.errors) == 2
    assert "jest:" in result.errors[0]
    assert result.files_with_errors == {"src/index.test.ts"}
