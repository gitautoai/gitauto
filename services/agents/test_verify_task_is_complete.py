# pylint: disable=too-many-lines,unused-argument
# pyright: reportArgumentType=false
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch, AsyncMock

import pytest

from services.agents.verify_task_is_complete import verify_task_is_complete
from services.eslint.run_eslint_fix import ESLintResult
from services.types.base_args import BaseArgs
from services.jest.run_jest_test import JestResult
from services.phpunit.run_phpunit_test import PhpunitResult
from services.prettier.run_prettier_fix import PrettierResult
from services.tsc.run_tsc_check import TscResult


@pytest.fixture(autouse=True)
def mock_tsc_check():
    """Auto-mock run_tsc_check for all tests to prevent actual tsc execution."""
    with patch(
        "services.agents.verify_task_is_complete.run_tsc_check",
        new_callable=AsyncMock,
        return_value=TscResult(success=True, errors=[], error_files=set()),
    ):
        yield


@pytest.fixture(autouse=True)
def mock_create_tsc_issue():
    """Auto-mock create_tsc_issue for all tests to prevent actual issue creation."""
    with patch(
        "services.agents.verify_task_is_complete.create_tsc_issue",
    ):
        yield


@pytest.fixture(autouse=True)
def mock_jest_test():
    """Auto-mock run_jest_test for all tests to prevent actual test execution."""
    with patch(
        "services.agents.verify_task_is_complete.run_jest_test",
        new_callable=AsyncMock,
        return_value=JestResult(
            success=True,
            errors=[],
            error_files=set(),
            runner_name="",
            updated_snapshots=set(),
        ),
    ):
        yield


@pytest.fixture(autouse=True)
def mock_phpunit_test():
    """Auto-mock run_phpunit_test for all tests to prevent actual test execution."""
    with patch(
        "services.agents.verify_task_is_complete.run_phpunit_test",
        new_callable=AsyncMock,
        return_value=PhpunitResult(success=True, errors=[], error_files=set()),
    ):
        yield


@pytest.fixture(autouse=True)
def mock_get_eslint_config():
    """Auto-mock get_eslint_config for all tests."""
    with patch(
        "services.agents.verify_task_is_complete.get_eslint_config",
        return_value=None,
    ):
        yield


@pytest.fixture(autouse=True)
def mock_ensure_eslint_relaxed():
    """Auto-mock ensure_eslint_relaxed_for_tests for all tests."""
    with patch(
        "services.agents.verify_task_is_complete.ensure_eslint_relaxed_for_tests",
        return_value=None,
    ):
        yield


@pytest.fixture
def base_args(tmp_path):
    return cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "clone_dir": str(tmp_path),
        },
    )


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_task_is_complete_success_with_changes(mock_get_files, base_args):
    mock_get_files.return_value = [
        {"filename": "file1.py", "status": "modified"},
    ]

    result = await verify_task_is_complete(base_args)

    assert result.success is True
    assert result.message == "Task completed."
    assert result.fixes_applied == []
    mock_get_files.assert_called_once_with(
        owner="test-owner", repo="test-repo", pr_number=123, token="test-token"
    )


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.run_eslint_fix")
@patch("services.agents.verify_task_is_complete.run_prettier_fix")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_partial_fix_with_remaining_errors(
    mock_get_files, mock_get_raw, mock_prettier, mock_eslint, base_args
):
    mock_get_files.return_value = [
        {"filename": "src/index.ts", "status": "modified"},
    ]
    original = "const x = 1\nconst unused = 2;"
    fixed = "const x = 1;\nconst unused = 2;"
    mock_get_raw.return_value = original
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=False,
        content=fixed,
        lint_errors="Line 2: 'unused' is defined but never used (no-unused-vars)",
        coverage_errors=None,
    )

    result = await verify_task_is_complete(base_args)

    assert result.success is False
    assert "NOT complete" in result.message
    assert "unused" in result.message
    assert "src/index.ts" in result.error_files


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_task_is_complete_failure_no_changes(mock_get_files, base_args):
    # Non-schedule PR with no changes should succeed (e.g. setup handler decided no work needed)
    mock_get_files.return_value = []

    result = await verify_task_is_complete(base_args)

    assert result.success is True
    assert "No changes were needed" in result.message


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_schedule_pr_no_changes_always_fails(mock_get_files, base_args):
    # Schedule/dashboard PR with 0 changes always fails without LLM call —
    # the schedule_handler already determined quality is bad when it created the PR
    mock_get_files.return_value = []
    base_args["trigger"] = "schedule"
    base_args["impl_file_to_collect_coverage_from"] = "src/resolvers/foo.ts"

    result = await verify_task_is_complete(base_args)

    assert result.success is False
    assert "0 changes" in result.message


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_task_is_complete_no_pr_number_returns_default(mock_get_files):
    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": None,
            "token": "test-token",
        },
    )

    result = await verify_task_is_complete(args)

    assert result.success is False
    assert "error" in result.message.lower()
    mock_get_files.assert_not_called()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_task_is_complete_api_error_returns_default(
    mock_get_files, base_args
):
    mock_get_files.side_effect = RuntimeError("API error")

    result = await verify_task_is_complete(base_args)

    assert result.success is False
    assert "error" in result.message.lower()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.run_eslint_fix")
@patch("services.agents.verify_task_is_complete.run_prettier_fix")
@patch("services.agents.verify_task_is_complete.ensure_jest_uses_tsconfig_for_tests")
@patch("services.agents.verify_task_is_complete.ensure_tsconfig_relaxed_for_tests")
@patch("services.agents.verify_task_is_complete.write_and_commit_file")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_autofixes_missing_braces_in_test_file(
    mock_get_files,
    mock_get_raw,
    mock_upload,
    mock_ensure_tsconfig,
    _mock_ensure_jest,
    mock_prettier,
    mock_eslint,
    base_args,
):
    mock_get_files.return_value = [
        {"filename": "src/components/Button.test.tsx", "status": "modified"},
    ]
    mock_get_raw.return_value = """describe('Button', () => {
  it('renders', () => {
    expect(true).toBe(true);

  it('clicks', () => {
    expect(true).toBe(true);
  });
});"""
    mock_upload.return_value = True
    mock_ensure_tsconfig.return_value = (None, None)
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=True, content=None, lint_errors=None, coverage_errors=None
    )

    result = await verify_task_is_complete(base_args)

    assert result.success is True
    assert result.message == "Task completed."


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_passes_with_correct_test_syntax(
    mock_get_files, mock_get_raw, base_args
):
    mock_get_files.return_value = [
        {"filename": "src/components/Button.test.tsx", "status": "modified"},
    ]
    mock_get_raw.return_value = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);
  });
});"""

    result = await verify_task_is_complete(base_args)

    assert result.success is True
    assert result.message == "Task completed."


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.run_eslint_fix")
@patch("services.agents.verify_task_is_complete.run_prettier_fix")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_ignores_non_test_files(
    mock_get_files, mock_get_raw, mock_prettier, mock_eslint, base_args
):
    mock_get_files.return_value = [
        {"filename": "src/components/Button.tsx", "status": "modified"},
    ]
    mock_get_raw.return_value = "const x = 1;\n"
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=True, content=None, lint_errors=None, coverage_errors=None
    )

    result = await verify_task_is_complete(base_args)

    assert result.success is True


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_ignores_removed_test_files(
    mock_get_files, mock_get_raw, base_args
):
    mock_get_files.return_value = [
        {"filename": "src/components/Button.test.tsx", "status": "removed"},
    ]

    result = await verify_task_is_complete(base_args)

    assert result.success is True
    mock_get_raw.assert_not_called()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.run_eslint_fix")
@patch("services.agents.verify_task_is_complete.run_prettier_fix")
@patch("services.agents.verify_task_is_complete.ensure_jest_uses_tsconfig_for_tests")
@patch("services.agents.verify_task_is_complete.ensure_tsconfig_relaxed_for_tests")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_checks_both_ts_test_files(
    mock_get_files,
    mock_get_raw,
    mock_ensure_tsconfig,
    _mock_ensure_jest,
    mock_prettier,
    mock_eslint,
    base_args,
):
    mock_get_files.return_value = [
        {"filename": "src/Button.test.tsx", "status": "modified"},
        {"filename": "src/Input.test.tsx", "status": "modified"},
    ]
    mock_get_raw.return_value = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);
  });
});"""
    mock_ensure_tsconfig.return_value = (None, None)
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=True, content=None, lint_errors=None, coverage_errors=None
    )

    result = await verify_task_is_complete(base_args)

    assert result.success is True
    assert mock_get_raw.call_count == 2


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.run_eslint_fix")
@patch("services.agents.verify_task_is_complete.run_prettier_fix")
@patch("services.agents.verify_task_is_complete.ensure_jest_uses_tsconfig_for_tests")
@patch("services.agents.verify_task_is_complete.ensure_tsconfig_relaxed_for_tests")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_checks_only_ts_when_mixed_with_py(
    mock_get_files,
    mock_get_raw,
    mock_ensure_tsconfig,
    _mock_ensure_jest,
    mock_prettier,
    mock_eslint,
    base_args,
):
    mock_get_files.return_value = [
        {"filename": "src/Button.test.tsx", "status": "modified"},
        {"filename": "tests/test_utils.py", "status": "modified"},
    ]
    mock_get_raw.return_value = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);
  });
});"""
    mock_ensure_tsconfig.return_value = (None, None)
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=True, content=None, lint_errors=None, coverage_errors=None
    )

    result = await verify_task_is_complete(base_args)

    assert result.success is True
    assert mock_get_raw.call_count == 1


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_ignores_all_non_js_test_files(
    mock_get_files, mock_get_raw, base_args
):
    mock_get_files.return_value = [
        {"filename": "tests/test_utils.py", "status": "modified"},
        {"filename": "tests/UtilsTest.php", "status": "modified"},
    ]

    result = await verify_task_is_complete(base_args)

    assert result.success is True
    mock_get_raw.assert_not_called()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.run_eslint_fix")
@patch("services.agents.verify_task_is_complete.run_prettier_fix")
@patch("services.agents.verify_task_is_complete.ensure_jest_uses_tsconfig_for_tests")
@patch("services.agents.verify_task_is_complete.ensure_tsconfig_relaxed_for_tests")
@patch("services.agents.verify_task_is_complete.write_and_commit_file")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_autofixes_when_one_of_two_ts_files_has_missing_braces(
    mock_get_files,
    mock_get_raw,
    mock_upload,
    mock_ensure_tsconfig,
    _mock_ensure_jest,
    mock_prettier,
    mock_eslint,
    base_args,
):
    mock_get_files.return_value = [
        {"filename": "src/Button.test.tsx", "status": "modified"},
        {"filename": "src/Input.test.tsx", "status": "modified"},
    ]
    correct_content = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);
  });
});"""
    broken_content = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);

  it('other', () => {
    expect(true).toBe(true);
  });
});"""
    mock_get_raw.side_effect = [correct_content, broken_content]
    mock_upload.return_value = True
    mock_ensure_tsconfig.return_value = (None, None)
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=True, content=None, lint_errors=None, coverage_errors=None
    )

    result = await verify_task_is_complete(base_args)

    assert result.success is True
    assert result.message == "Task completed."


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.run_eslint_fix")
@patch("services.agents.verify_task_is_complete.run_prettier_fix")
@patch("services.agents.verify_task_is_complete.ensure_jest_uses_tsconfig_for_tests")
@patch("services.agents.verify_task_is_complete.ensure_tsconfig_relaxed_for_tests")
@patch("services.agents.verify_task_is_complete.write_and_commit_file")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_autofixes_ts_with_missing_braces_ignores_py(
    mock_get_files,
    mock_get_raw,
    mock_upload,
    mock_ensure_tsconfig,
    _mock_ensure_jest,
    mock_prettier,
    mock_eslint,
    base_args,
):
    mock_get_files.return_value = [
        {"filename": "src/Button.test.tsx", "status": "modified"},
        {"filename": "tests/test_utils.py", "status": "modified"},
    ]
    broken_content = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);

  it('other', () => {
    expect(true).toBe(true);
  });
});"""
    mock_get_raw.return_value = broken_content
    mock_upload.return_value = True
    mock_ensure_tsconfig.return_value = (None, None)
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=True, content=None, lint_errors=None, coverage_errors=None
    )

    result = await verify_task_is_complete(base_args)

    assert result.success is True
    assert result.message == "Task completed."


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_fails_when_jest_tests_fail(
    mock_get_files, mock_get_raw, mock_tsc, mock_jest, base_args
):
    # Use JS file (not TS) to avoid triggering tsconfig setup for TS test files
    mock_get_files.return_value = [
        {"filename": "src/index.test.js", "status": "modified"},
    ]
    mock_get_raw.return_value = "const x = 1;"
    mock_tsc.return_value = TscResult(success=True, errors=[], error_files=set())
    mock_jest.return_value = JestResult(
        success=False,
        errors=["FAIL src/index.test.js", "Expected true to be false"],
        error_files={"src/index.test.js"},
        runner_name="jest",
        updated_snapshots=set(),
    )

    result = await verify_task_is_complete(base_args)

    assert result.success is False
    assert "NOT complete" in result.message
    assert "jest:" in result.message
    assert "src/index.test.js" in result.error_files


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_eslint_fix")
@patch("services.agents.verify_task_is_complete.run_prettier_fix")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_error_files_collected_from_eslint_and_jest(
    mock_get_files,
    mock_get_raw,
    mock_prettier,
    mock_eslint,
    mock_tsc,
    mock_jest,
    base_args,
):
    """Verify error_files collects files from both ESLint and jest failures."""
    mock_get_files.return_value = [
        {"filename": "src/index.ts", "status": "modified"},
        {"filename": "src/index.test.js", "status": "modified"},
    ]
    mock_get_raw.return_value = "const x = 1;"
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=False,
        content="const x = 1;",
        lint_errors="Line 1: 'x' is defined but never used (no-unused-vars)",
        coverage_errors=None,
    )
    mock_tsc.return_value = TscResult(success=True, errors=[], error_files=set())
    mock_jest.return_value = JestResult(
        success=False,
        errors=["FAIL src/index.test.js"],
        error_files={"src/index.test.js"},
        runner_name="jest",
        updated_snapshots=set(),
    )

    result = await verify_task_is_complete(base_args)

    assert result.success is False
    assert "src/index.ts" in result.error_files
    assert "src/index.test.js" in result.error_files


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.create_tsc_issue")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_baseline_tsc_errors_filtered(
    mock_get_files, mock_tsc, mock_jest, mock_create_tsc_issue
):
    pre_existing_error = (
        "src/passport-oidc.ts(217,32): error TS2339: "
        "Property 'id' does not exist on type 'Profile'."
    )
    new_error = (
        "src/index.ts(10,5): error TS2322: "
        "Type 'string' is not assignable to type 'number'."
    )

    mock_get_files.return_value = [
        {"filename": "src/index.ts", "status": "modified"},
    ]
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[pre_existing_error, new_error],
        error_files={"src/passport-oidc.ts", "src/index.ts"},
    )
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="",
        updated_snapshots=set(),
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "baseline_tsc_errors": {pre_existing_error},
        },
    )
    result = await verify_task_is_complete(args)

    # Pre-existing error filtered, new error reported
    assert result.success is False
    assert "TS2322" in result.message
    assert "TS2339" not in result.message

    # create_tsc_issue called with the pre-existing error
    mock_create_tsc_issue.assert_called_once()
    call_kwargs = mock_create_tsc_issue.call_args.kwargs
    assert call_kwargs["unrelated_errors"] == [pre_existing_error]


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.create_tsc_issue")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_all_tsc_errors_pre_existing_passes(
    mock_get_files, mock_tsc, mock_jest, mock_create_tsc_issue
):
    pre_existing = "src/old.ts(1,1): error TS2339: Property 'x' does not exist."

    mock_get_files.return_value = [
        {"filename": "src/index.ts", "status": "modified"},
    ]
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[pre_existing],
        error_files={"src/old.ts"},
    )
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="",
        updated_snapshots=set(),
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "baseline_tsc_errors": {pre_existing},
        },
    )
    result = await verify_task_is_complete(args)

    # All errors are pre-existing, so task passes
    assert result.success is True
    assert result.message == "Task completed."
    mock_create_tsc_issue.assert_called_once()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.create_tsc_issue")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_baseline_tsc_errors_in_pr_files_still_reported(
    mock_get_files, mock_tsc, mock_jest, mock_create_tsc_issue, tmp_path
):
    """Errors in PR-changed files should be reported even if in baseline.

    This tests the check_suite/review_run scenario where baseline captures
    errors from the PR branch before fixes. Errors in PR files must always
    be reported so the agent fixes them.
    """
    pr_file_error = (
        "src/models/InProgressPolicy.test.ts(15,21): error TS2339: "
        "Property 'collection' does not exist on type 'FoxcomObject'."
    )

    mock_get_files.return_value = [
        {"filename": "src/models/InProgressPolicy.test.ts", "status": "modified"},
    ]
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[pr_file_error],
        error_files={"src/models/InProgressPolicy.test.ts"},
    )
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="",
        updated_snapshots=set(),
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "baseline_tsc_errors": {pr_file_error},
            "clone_dir": str(tmp_path),
        },
    )
    result = await verify_task_is_complete(args)

    # Error is in baseline BUT also in PR files → must be reported
    assert result.success is False
    assert "TS2339" in result.message
    mock_create_tsc_issue.assert_not_called()


@pytest.mark.asyncio
@patch(
    "services.agents.verify_task_is_complete.read_local_file",
    return_value="// snapshot content",
)
@patch("services.agents.verify_task_is_complete.write_and_commit_file")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.os.listdir", return_value=[])
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_verify_commits_updated_snapshots(
    mock_get_files,
    _mock_listdir,
    mock_get_raw,
    mock_tsc,
    mock_jest,
    mock_upload,
    _mock_read_local,
):
    mock_get_files.return_value = [
        {"filename": "src/index.test.js", "status": "modified"},
    ]
    mock_get_raw.return_value = "const x = 1;"
    mock_tsc.return_value = TscResult(success=True, errors=[], error_files=set())
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="jest",
        updated_snapshots={"src/__snapshots__/index.test.js.snap"},
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await verify_task_is_complete(args)

    assert result.success is True
    mock_upload.assert_called_once()
    call_kwargs = mock_upload.call_args.kwargs
    assert call_kwargs["file_path"] == "src/__snapshots__/index.test.js.snap"
    assert call_kwargs["file_content"] == "// snapshot content"
    assert "snapshot" in call_kwargs["commit_message"]
    assert (
        "- src/__snapshots__/index.test.js.snap: Snapshot updated"
        in result.fixes_applied
    )


# ============================================================
# 9 handler × error-case matrix tests
# ============================================================
# 3 handlers: new_pr_handler, check_suite_handler, review_run_handler
# 3 cases per handler:
#   1. Error in PR file → always report
#   2. Error in non-PR file AND in baseline → skip (pre-existing)
#   3. Error in non-PR file AND NOT in baseline → report


# --- new_pr_handler: baseline comes from master (base) branch ---


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.create_tsc_issue")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_new_pr_handler_error_in_pr_file_reported(
    mock_get_files, mock_tsc, mock_jest, mock_create_tsc_issue
):
    """new_pr_handler: Agent wrote new code with a type error in a PR file.

    Baseline is from master (clean), so error is NOT in baseline.
    Error must be reported because the file is in the PR.
    """
    pr_file_error = "src/utils.ts(10,5): error TS2322: Type 'string' is not assignable."

    mock_get_files.return_value = [
        {"filename": "src/utils.ts", "status": "modified"},
    ]
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[pr_file_error],
        error_files={"src/utils.ts"},
    )
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="",
        updated_snapshots=set(),
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "baseline_tsc_errors": set(),  # Master was clean
        },
    )
    result = await verify_task_is_complete(args)

    assert result.success is False
    assert "TS2322" in result.message
    mock_create_tsc_issue.assert_not_called()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.create_tsc_issue")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_new_pr_handler_preexisting_non_pr_file_error_skipped(
    mock_get_files, mock_tsc, mock_jest, mock_create_tsc_issue
):
    """new_pr_handler: Master has a pre-existing tsc error in an unrelated file.

    Error is in a non-PR file AND in baseline → skip.
    Task should pass since the error is not caused by the PR.
    """
    preexisting = "src/legacy.ts(50,10): error TS2339: Property 'x' does not exist."

    mock_get_files.return_value = [
        {"filename": "src/new-feature.ts", "status": "added"},
    ]
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[preexisting],
        error_files={"src/legacy.ts"},
    )
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="",
        updated_snapshots=set(),
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "baseline_tsc_errors": {preexisting},
        },
    )
    result = await verify_task_is_complete(args)

    assert result.success is True
    assert result.message == "Task completed."
    mock_create_tsc_issue.assert_called_once()
    assert mock_create_tsc_issue.call_args.kwargs["unrelated_errors"] == [preexisting]


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.create_tsc_issue")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_new_pr_handler_new_non_pr_file_error_reported(
    mock_get_files, mock_tsc, mock_jest, mock_create_tsc_issue
):
    """new_pr_handler: PR changes caused a type error in a file the agent didn't modify.

    Error is in a non-PR file AND NOT in baseline → report.
    The PR changes broke an importing file.
    """
    new_error = "src/consumer.ts(20,3): error TS2345: Argument type mismatch."

    mock_get_files.return_value = [
        {"filename": "src/api.ts", "status": "modified"},
    ]
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[new_error],
        error_files={"src/consumer.ts"},
    )
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="",
        updated_snapshots=set(),
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "baseline_tsc_errors": set(),  # Master was clean
        },
    )
    result = await verify_task_is_complete(args)

    assert result.success is False
    assert "TS2345" in result.message
    mock_create_tsc_issue.assert_not_called()


# --- check_suite_handler: baseline comes from PR branch before fixes ---


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.create_tsc_issue")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_check_suite_error_in_pr_file_in_baseline_reported(
    mock_get_files, mock_tsc, mock_jest, mock_create_tsc_issue, tmp_path
):
    """check_suite: PR file has error that was also in baseline (PR branch state).

    Baseline captured this error from the PR branch before fix attempts.
    Error must still be reported because it's in a PR file - agent must fix it.
    This is the bug fix: baseline should NOT suppress errors in PR files.
    """
    pr_file_error = (
        "src/models/Policy.test.ts(15,21): error TS2339: "
        "Property 'collection' does not exist on type 'FoxcomObject'."
    )

    mock_get_files.return_value = [
        {"filename": "src/models/Policy.test.ts", "status": "modified"},
    ]
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[pr_file_error],
        error_files={"src/models/Policy.test.ts"},
    )
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="",
        updated_snapshots=set(),
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            # Baseline from PR branch contains this error
            "baseline_tsc_errors": {pr_file_error},
            "clone_dir": str(tmp_path),
        },
    )
    result = await verify_task_is_complete(args)

    assert result.success is False
    assert "TS2339" in result.message
    mock_create_tsc_issue.assert_not_called()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.create_tsc_issue")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_check_suite_preexisting_non_pr_file_error_skipped(
    mock_get_files, mock_tsc, mock_jest, mock_create_tsc_issue, tmp_path
):
    """check_suite: Pre-existing error in unrelated file on PR branch.

    Error is in a non-PR file AND in baseline → skip.
    The PR didn't cause this, it was already broken.
    """
    preexisting = "src/passport-oidc.ts(217,32): error TS2339: Property 'id' missing."

    mock_get_files.return_value = [
        {"filename": "src/models/Policy.test.ts", "status": "modified"},
    ]
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[preexisting],
        error_files={"src/passport-oidc.ts"},
    )
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="",
        updated_snapshots=set(),
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "baseline_tsc_errors": {preexisting},
            "clone_dir": str(tmp_path),
        },
    )
    result = await verify_task_is_complete(args)

    assert result.success is True
    assert result.message == "Task completed."
    mock_create_tsc_issue.assert_called_once()
    assert mock_create_tsc_issue.call_args.kwargs["unrelated_errors"] == [preexisting]


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.create_tsc_issue")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_check_suite_new_non_pr_file_error_reported(
    mock_get_files, mock_tsc, mock_jest, mock_create_tsc_issue, tmp_path
):
    """check_suite: Agent's fix attempt introduced error in a non-PR file.

    Error is in a non-PR file AND NOT in baseline → report.
    The agent's changes broke a dependent file.
    """
    new_error = "src/auth.ts(30,8): error TS2345: Argument type mismatch."

    mock_get_files.return_value = [
        {"filename": "src/models/Policy.test.ts", "status": "modified"},
    ]
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[new_error],
        error_files={"src/auth.ts"},
    )
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="",
        updated_snapshots=set(),
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "baseline_tsc_errors": set(),
            "clone_dir": str(tmp_path),
        },
    )
    result = await verify_task_is_complete(args)

    assert result.success is False
    assert "TS2345" in result.message
    mock_create_tsc_issue.assert_not_called()


# --- review_run_handler: baseline comes from PR branch before fixes ---


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.create_tsc_issue")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_review_run_error_in_pr_file_in_baseline_reported(
    mock_get_files, mock_tsc, mock_jest, mock_create_tsc_issue
):
    """review_run: Reviewer pointed out issue, PR file has error in baseline.

    Baseline captured this error from the PR branch before fix attempts.
    Error must still be reported because it's in a PR file.
    """
    pr_file_error = (
        "src/components/Form.tsx(42,10): error TS2322: "
        "Type 'string' is not assignable to type 'number'."
    )

    mock_get_files.return_value = [
        {"filename": "src/components/Form.tsx", "status": "modified"},
    ]
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[pr_file_error],
        error_files={"src/components/Form.tsx"},
    )
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="",
        updated_snapshots=set(),
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "baseline_tsc_errors": {pr_file_error},
        },
    )
    result = await verify_task_is_complete(args)

    assert result.success is False
    assert "TS2322" in result.message
    mock_create_tsc_issue.assert_not_called()


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.create_tsc_issue")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_review_run_preexisting_non_pr_file_error_skipped(
    mock_get_files, mock_tsc, mock_jest, mock_create_tsc_issue
):
    """review_run: Pre-existing error in unrelated file on PR branch.

    Error is in a non-PR file AND in baseline → skip.
    """
    preexisting = "src/legacy-auth.ts(100,5): error TS2339: Property 'role' missing."

    mock_get_files.return_value = [
        {"filename": "src/components/Form.tsx", "status": "modified"},
    ]
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[preexisting],
        error_files={"src/legacy-auth.ts"},
    )
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="",
        updated_snapshots=set(),
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "baseline_tsc_errors": {preexisting},
        },
    )
    result = await verify_task_is_complete(args)

    assert result.success is True
    assert result.message == "Task completed."
    mock_create_tsc_issue.assert_called_once()
    assert mock_create_tsc_issue.call_args.kwargs["unrelated_errors"] == [preexisting]


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.create_tsc_issue")
@patch("services.agents.verify_task_is_complete.run_jest_test", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.run_tsc_check", new_callable=AsyncMock)
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_review_run_new_non_pr_file_error_reported(
    mock_get_files, mock_tsc, mock_jest, mock_create_tsc_issue
):
    """review_run: Agent's fix introduced error in a non-PR file.

    Error is in a non-PR file AND NOT in baseline → report.
    """
    new_error = "src/validators.ts(15,3): error TS2345: Argument type mismatch."

    mock_get_files.return_value = [
        {"filename": "src/components/Form.tsx", "status": "modified"},
    ]
    mock_tsc.return_value = TscResult(
        success=False,
        errors=[new_error],
        error_files={"src/validators.ts"},
    )
    mock_jest.return_value = JestResult(
        success=True,
        errors=[],
        error_files=set(),
        runner_name="",
        updated_snapshots=set(),
    )

    args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 123,
            "token": "test-token",
            "new_branch": "test-branch",
            "baseline_tsc_errors": set(),
        },
    )
    result = await verify_task_is_complete(args)

    assert result.success is False
    assert "TS2345" in result.message
    mock_create_tsc_issue.assert_not_called()


# ============================================================
# ensure_eslint_relaxed_for_tests integration tests
# ============================================================


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.ensure_eslint_relaxed_for_tests")
@patch("services.agents.verify_task_is_complete.get_eslint_config")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_ensure_eslint_relaxed_called_for_js_test_files(
    mock_get_files, mock_get_raw, mock_get_eslint, mock_ensure_eslint, base_args
):
    mock_get_files.return_value = [
        {"filename": "src/index.test.js", "status": "modified"},
    ]
    mock_get_raw.return_value = "const x = 1;"
    mock_get_eslint.return_value = {"filename": ".eslintrc.json", "content": "{}"}

    await verify_task_is_complete(base_args)

    mock_get_eslint.assert_called_once()
    mock_ensure_eslint.assert_called_once_with(
        eslint_config={"filename": ".eslintrc.json", "content": "{}"},
        base_args=base_args,
    )


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.ensure_eslint_relaxed_for_tests")
@patch("services.agents.verify_task_is_complete.get_eslint_config")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_ensure_eslint_relaxed_not_called_for_non_test_files(
    mock_get_files, mock_get_eslint, mock_ensure_eslint, base_args
):
    mock_get_files.return_value = [
        {"filename": "src/index.ts", "status": "modified"},
    ]

    await verify_task_is_complete(base_args)

    mock_get_eslint.assert_not_called()
    mock_ensure_eslint.assert_not_called()


# ============================================================
# Dead code handling: no-unnecessary-condition as blocking error
# ============================================================


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.run_eslint_fix")
@patch("services.agents.verify_task_is_complete.run_prettier_fix")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_coverage_error_no_unnecessary_condition_blocks_completion(
    mock_get_files, mock_get_raw, mock_prettier, mock_eslint, base_args
):
    """Verify that no-unnecessary-condition coverage errors block task completion.

    Dead code detected by @typescript-eslint/no-unnecessary-condition must be
    reported as a blocking error so the agent removes it rather than adding
    istanbul ignore comments.
    """
    mock_get_files.return_value = [
        {"filename": "src/PaymentForm.tsx", "status": "modified"},
    ]
    mock_get_raw.return_value = (
        "const x = paymentMethod !== undefined ? <Component /> : null;"
    )
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=False,
        content="const x = paymentMethod !== undefined ? <Component /> : null;",
        lint_errors=None,
        coverage_errors="Line 1: Unnecessary conditional, expected expression to always be truthy (@typescript-eslint/no-unnecessary-condition)",
    )

    result = await verify_task_is_complete(base_args)

    assert result.success is False
    assert "NOT complete" in result.message
    assert "no-unnecessary-condition" in result.message
    assert "src/PaymentForm.tsx" in result.error_files


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.run_eslint_fix")
@patch("services.agents.verify_task_is_complete.run_prettier_fix")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_lint_only_errors_still_block_completion(
    mock_get_files, mock_get_raw, mock_prettier, mock_eslint, base_args
):
    """Verify that lint-only errors (e.g., no-explicit-any) also block completion.

    verify_task_is_complete reports both lint_errors and coverage_errors.
    """
    mock_get_files.return_value = [
        {"filename": "src/utils.ts", "status": "modified"},
    ]
    mock_get_raw.return_value = "const x: any = 1;"
    mock_prettier.return_value = PrettierResult(success=True, content=None, error=None)
    mock_eslint.return_value = ESLintResult(
        success=False,
        content="const x: any = 1;",
        lint_errors="Line 1: Unexpected any (@typescript-eslint/no-explicit-any)",
        coverage_errors=None,
    )

    result = await verify_task_is_complete(base_args)

    assert result.success is False
    assert "no-explicit-any" in result.message
    assert "src/utils.ts" in result.error_files


# --- Quality gate escape hatch tests ---


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_quality_gate_0_changes_first_attempt_rejects(mock_get_files, base_args):
    """First 0-change attempt on schedule PR rejects and increments counter."""
    mock_get_files.return_value = []
    base_args["trigger"] = "schedule"
    base_args["impl_file_to_collect_coverage_from"] = "src/foo.ts"

    result = await verify_task_is_complete(base_args)

    assert result.success is False
    assert "0 changes" in result.message
    assert base_args["quality_gate_fail_count"] == 1


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_quality_gate_0_changes_second_attempt_accepts(mock_get_files, base_args):
    """Second 0-change attempt accepts (escape hatch)."""
    mock_get_files.return_value = []
    base_args["trigger"] = "schedule"
    base_args["impl_file_to_collect_coverage_from"] = "src/foo.ts"
    base_args["quality_gate_fail_count"] = 1

    result = await verify_task_is_complete(base_args)

    assert result.success is True


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.slack_notify")
@patch("services.agents.verify_task_is_complete.run_quality_gate")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_quality_gate_skipped_after_3_failures(
    mock_get_files, mock_read, mock_quality_gate, mock_slack, base_args, tmp_path
):
    """Quality gate is skipped after 3 consecutive failures and notifies Slack."""
    mock_get_files.return_value = [
        {"filename": "test/foo.spec.ts", "status": "added"},
    ]
    mock_read.return_value = "test content"
    base_args["trigger"] = "schedule"
    base_args["impl_file_to_collect_coverage_from"] = "src/foo.ts"
    base_args["quality_gate_fail_count"] = 3
    base_args["slack_thread_ts"] = "ts_abc123"
    (tmp_path / "test/foo.spec.ts").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "test/foo.spec.ts").touch()

    result = await verify_task_is_complete(base_args)

    mock_quality_gate.assert_not_called()
    mock_slack.assert_called_once()
    assert "test-owner/test-repo#123" in mock_slack.call_args[0][0]
    assert "src/foo.ts" in mock_slack.call_args[0][0]
    assert mock_slack.call_args[0][1] == "ts_abc123"
    assert result.success is True


@pytest.mark.asyncio
@patch("services.agents.verify_task_is_complete.run_quality_gate")
@patch("services.agents.verify_task_is_complete.read_local_file")
@patch("services.agents.verify_task_is_complete.get_pull_request_files")
async def test_quality_gate_runs_when_fail_count_below_3(
    mock_get_files, mock_read, mock_quality_gate, base_args, tmp_path
):
    """Quality gate runs and increments counter on failure when count < 3."""
    mock_get_files.return_value = [
        {"filename": "test/foo.spec.ts", "status": "added"},
    ]
    mock_read.return_value = "test content"
    mock_quality_gate.return_value = (
        "Quality gate failed for src/foo.ts:\nadversarial.null_inputs: No null tests"
    )
    base_args["trigger"] = "schedule"
    base_args["impl_file_to_collect_coverage_from"] = "src/foo.ts"
    base_args["quality_gate_fail_count"] = 1
    (tmp_path / "test/foo.spec.ts").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "test/foo.spec.ts").touch()

    result = await verify_task_is_complete(base_args)

    mock_quality_gate.assert_called_once()
    assert result.success is False
    assert "adversarial.null_inputs" in result.message
    assert base_args["quality_gate_fail_count"] == 2
