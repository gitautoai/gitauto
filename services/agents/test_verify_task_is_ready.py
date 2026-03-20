# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch, AsyncMock

import pytest

from services.agents.verify_task_is_ready import verify_task_is_ready
from services.eslint.run_eslint_fix import ESLintResult
from services.types.base_args import BaseArgs
from services.jest.run_jest_test import JestResult
from services.prettier.run_prettier_fix import PrettierResult
from services.tsc.run_tsc_check import TscResult


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.git_commit_and_push")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_valid_file_returns_success(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_commit
):
    mock_get_raw_content.return_value = "function foo() { return 1; }"
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=True, content=None, lint_errors=None, coverage_errors=None
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
        base_args=base_args,
        file_paths=["src/index.ts"],
        run_tsc=False,
        run_jest=False,
        run_phpunit=False,
    )
    assert result.success is True
    assert result.errors == []
    assert result.fixes_applied == []
    assert result.files_with_errors == set()
    mock_commit.assert_not_called()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.git_commit_and_push")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_prettier_fails_returns_errors(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_commit
):
    mock_get_raw_content.return_value = "function foo() { return 1;"
    mock_prettier.return_value = PrettierResult(
        success=False, content=None, error="SyntaxError: Unexpected token"
    )
    mock_eslint.return_value = ESLintResult(
        success=True, content=None, lint_errors=None, coverage_errors=None
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
        base_args=base_args,
        file_paths=["src/broken.ts"],
        run_tsc=False,
        run_jest=False,
        run_phpunit=False,
    )
    assert result.success is False
    assert len(result.errors) == 1
    assert "SyntaxError" in result.errors[0]
    assert result.fixes_applied == []
    assert result.files_with_errors == {"src/broken.ts"}


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.git_commit_and_push")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_eslint_fails_returns_errors(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_commit
):
    mock_get_raw_content.return_value = "function foo() { return 1; }"
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=False,
        content=None,
        lint_errors=None,
        coverage_errors="Parsing error: Unexpected token",
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
        base_args=base_args,
        file_paths=["src/broken.ts"],
        run_tsc=False,
        run_jest=False,
        run_phpunit=False,
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
        base_args=base_args,
        file_paths=["README.md", "config.json"],
        run_tsc=False,
        run_jest=False,
        run_phpunit=False,
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
    result = await verify_task_is_ready(
        base_args=base_args,
        file_paths=[],
        run_tsc=False,
        run_jest=False,
        run_phpunit=False,
    )
    assert result.success is True
    assert result.errors == []
    assert result.fixes_applied == []
    assert result.files_with_errors == set()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.git_commit_and_push")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_file_not_found_skipped(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_commit
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
        base_args=base_args,
        file_paths=["src/missing.ts"],
        run_tsc=False,
        run_jest=False,
        run_phpunit=False,
    )
    assert result.success is True
    assert result.errors == []
    assert result.fixes_applied == []
    assert result.files_with_errors == set()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.git_commit_and_push")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_fixes_applied_and_pushed(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_commit
):
    original = "function foo() { return 1; }"
    formatted = "function foo() {\n  return 1;\n}"
    mock_get_raw_content.return_value = original
    mock_prettier.return_value = PrettierResult(
        success=True, content=formatted, error=None
    )
    mock_eslint.return_value = ESLintResult(
        success=True, content=None, lint_errors=None, coverage_errors=None
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
        base_args=base_args,
        file_paths=["src/index.ts"],
        run_tsc=False,
        run_jest=False,
        run_phpunit=False,
    )
    assert result.success is True
    assert result.errors == []
    assert result.fixes_applied == ["- src/index.ts: Prettier"]
    assert result.files_with_errors == set()
    mock_commit.assert_called_once()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.git_commit_and_push")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_eslint_partial_fix_pushes_and_reports_errors(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_commit
):
    original = "const x = 1\nconst unused = 2;"
    fixed = "const x = 1;\nconst unused = 2;"
    mock_get_raw_content.return_value = original
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=False,
        content=fixed,
        lint_errors="Line 2: 'unused' is defined but never used (no-unused-vars)",
        coverage_errors=None,
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
        base_args=base_args,
        file_paths=["src/index.ts"],
        run_tsc=False,
        run_jest=False,
        run_phpunit=False,
    )
    # Lint-only errors (no-unused-vars) are ignored by verify_task_is_ready
    # Only coverage-relevant errors cause failure
    assert result.success is True
    assert result.errors == []
    assert result.fixes_applied == ["- src/index.ts: ESLint"]
    assert result.files_with_errors == set()
    mock_commit.assert_called_once()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.git_commit_and_push")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_no_explicit_any_ignored(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_commit
):
    mock_get_raw_content.return_value = (
        "export async function getUsers(): Promise<any[]> { return []; }"
    )
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=False,
        content=None,
        lint_errors="Line 79: Unexpected any. Specify a different type (@typescript-eslint/no-explicit-any); Line 111: Unexpected any. Specify a different type (@typescript-eslint/no-explicit-any)",
        coverage_errors=None,
    )
    base_args = cast(
        BaseArgs,
        {
            "owner": "Foxquilt",
            "repo": "foxden-auth-service",
            "token": "test",
            "base_branch": "main",
        },
    )
    result = await verify_task_is_ready(
        base_args=base_args,
        file_paths=["src/utils/auth0.ts"],
        run_tsc=False,
        run_jest=False,
        run_phpunit=False,
    )
    # no-explicit-any is a lint-only error, not coverage-relevant
    # Previously this caused the agent to loop for 900s trying to fix unfixable errors
    assert result.success is True
    assert result.errors == []
    assert result.files_with_errors == set()
    mock_commit.assert_not_called()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.run_tsc_check")
@patch("services.agents.verify_task_is_ready.git_commit_and_push")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_run_tsc_reports_type_errors(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_commit, mock_tsc
):
    mock_get_raw_content.return_value = "const x: number = 'hello';"
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=True, content=None, lint_errors=None, coverage_errors=None
    )
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
        base_args=base_args,
        file_paths=["src/index.ts"],
        run_tsc=True,
        run_jest=False,
        run_phpunit=False,
    )
    assert result.success is False
    assert len(result.errors) == 1
    assert "TS2322" in result.errors[0]
    assert result.files_with_errors == {"src/index.ts"}
    assert result.tsc_errors == [
        "src/index.ts(1,7): error TS2322: Type 'string' is not assignable to type 'number'."
    ]


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_ready.run_jest_test")
@patch("services.agents.verify_task_is_ready.git_commit_and_push")
@patch("services.agents.verify_task_is_ready.run_eslint_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.run_prettier_fix", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_ready.get_raw_content")
async def test_run_jest_reports_test_failures(
    mock_get_raw_content, mock_prettier, mock_eslint, mock_commit, mock_jest
):
    mock_get_raw_content.return_value = (
        "describe('test', () => { it('fails', () => { expect(true).toBe(false); }); });"
    )
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=True, content=None, lint_errors=None, coverage_errors=None
    )
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
        base_args=base_args,
        file_paths=["src/index.test.ts"],
        run_tsc=False,
        run_jest=True,
        run_phpunit=False,
    )
    assert result.success is False
    assert len(result.errors) == 2
    assert "jest:" in result.errors[0]
    assert result.files_with_errors == {"src/index.test.ts"}
