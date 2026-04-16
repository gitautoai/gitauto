# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch, MagicMock

import pytest

from services.jest.run_js_ts_test import run_js_ts_test


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_success(
    mock_exists, mock_subprocess, create_test_base_args
):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True
    assert result.errors == []
    assert result.error_files == set()


@pytest.mark.asyncio
async def test_run_js_ts_test_no_test_files(create_test_base_args):
    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.ts", "README.md"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_run_js_ts_test_no_clone_dir(create_test_base_args):
    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_no_runner(mock_exists, create_test_base_args):
    mock_exists.return_value = False

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_with_failures(
    mock_exists, mock_subprocess, create_test_base_args
):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="FAIL src/index.test.ts\n● Test suite failed to run\nError: Cannot find module",
        stderr="",
    )

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is False
    assert len(result.errors) > 0
    assert "src/index.test.ts" in result.error_files


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_detects_updated_snapshots(
    mock_exists, mock_subprocess, create_test_base_args
):
    mock_exists.return_value = True
    jest_result = MagicMock(returncode=0, stdout="", stderr="")
    git_diff_result = MagicMock(
        returncode=0,
        stdout="src/__snapshots__/Button.test.tsx.snap\ntest/__snapshots__/utils.test.ts.snap\n",
    )
    # Single jest run + git diff = 2 calls
    mock_subprocess.side_effect = [jest_result, git_diff_result]

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True
    assert result.updated_snapshots == {
        "src/__snapshots__/Button.test.tsx.snap",
        "test/__snapshots__/utils.test.ts.snap",
    }


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_no_snapshots_updated(
    mock_exists, mock_subprocess, create_test_base_args
):
    mock_exists.return_value = True
    jest_result = MagicMock(returncode=0, stdout="", stderr="")
    git_diff_result = MagicMock(returncode=0, stdout="src/index.ts\n")
    # Single jest run + git diff = 2 calls
    mock_subprocess.side_effect = [jest_result, git_diff_result]

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True
    assert result.updated_snapshots == set()


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_uses_vitest_when_no_jest(
    mock_exists, mock_subprocess, create_test_base_args
):
    def exists_side_effect(path):
        # Jest doesn't exist, but vitest does
        if "jest" in path:
            return False
        return "vitest" in path or "node_modules" in path

    mock_exists.side_effect = exists_side_effect
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True

    # First call is the test, last is git diff
    cmd = mock_subprocess.call_args_list[0][0][0]
    assert "vitest" in cmd[0]


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_spec_files(
    mock_exists, mock_subprocess, create_test_base_args
):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/utils.spec.ts", "src/helper.spec.jsx"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True

    # 1 test run (all files together) + 1 git diff = 2
    assert mock_subprocess.call_count == 2


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_one_of_three_fails(
    mock_exists, mock_subprocess, create_test_base_args
):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="PASS src/a.test.ts\nFAIL src/b.test.ts\nPASS src/c.test.ts\nError in b",
        stderr="",
    )

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/a.test.ts", "src/b.test.ts", "src/c.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is False
    assert "src/a.test.ts" not in result.error_files
    assert "src/b.test.ts" in result.error_files
    assert "src/c.test.ts" not in result.error_files


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_two_of_three_fail(
    mock_exists, mock_subprocess, create_test_base_args
):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="FAIL src/a.test.ts\nPASS src/b.test.ts\nFAIL src/c.test.ts\nErrors in a and c",
        stderr="",
    )

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/a.test.ts", "src/b.test.ts", "src/c.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is False
    assert "src/a.test.ts" in result.error_files
    assert "src/b.test.ts" not in result.error_files
    assert "src/c.test.ts" in result.error_files


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_all_three_fail(
    mock_exists, mock_subprocess, create_test_base_args
):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="FAIL src/a.test.ts\nFAIL src/b.test.ts\nFAIL src/c.test.ts\nError in all",
        stderr="",
    )

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/a.test.ts", "src/b.test.ts", "src/c.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is False
    assert "src/a.test.ts" in result.error_files
    assert "src/b.test.ts" in result.error_files
    assert "src/c.test.ts" in result.error_files


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_type_error_in_output(
    mock_exists, mock_subprocess, create_test_base_args
):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="TypeError: Cannot read property 'foo' of undefined",
        stderr="",
    )

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is False
    assert any("TypeError" in e for e in result.errors)


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_sets_mongoms_download_dir(
    mock_exists, mock_subprocess, create_test_base_args
):
    """Verify MONGOMS_DOWNLOAD_DIR points to {clone_dir}/mongodb-binaries for S3 cache extraction."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = create_test_base_args(
        clone_dir="/tmp/clone",
    )
    await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )

    # Verify jest was called with MONGOMS_DOWNLOAD_DIR in env (first call is jest)
    call_kwargs = mock_subprocess.call_args_list[0].kwargs
    env = call_kwargs["env"]
    assert env["MONGOMS_DOWNLOAD_DIR"] == "/tmp/clone/mongodb-binaries"


# Real Jest output captured from foxden-rating-quoting-backend on 2026-03-23.
# Jest writes PASS/FAIL to stderr, coverage tables to stdout.
# This was the root cause of a bug where run_js_ts_test checked only result.stdout.
REAL_JEST_PASS_STDERR = (
    "PASS unit src/services/query/getQuote/fetchQuote.test.ts\n"
    "  fetchQuote\n"
    "    \u2713 throws when response typename is not GetQuoteOk (5 ms)\n"
    "    \u2713 returns quote with carrierPartner when truthy (1 ms)\n"
    "    \u2713 defaults carrierName to Munich when carrierPartner is falsy\n"
    "    \u2713 defaults carrierName to Munich when carrierPartner is empty string\n"
    "\n"
    "Test Suites: 1 passed, 1 total\n"
    "Tests:       4 passed, 4 total\n"
    "Snapshots:   0 total\n"
    "Time:        4.308 s, estimated 6 s\n"
    "Ran all test suites within paths "
    '"src/services/query/getQuote/fetchQuote.test.ts".\n'
)

REAL_JEST_FAIL_STDERR = (
    "FAIL unit src/fail_test.test.ts\n"
    "  intentional failure\n"
    "    \u2717 fails (1 ms)\n"
    "\n"
    "  \u25cf intentional failure \u203a fails\n"
    "\n"
    "    expect(received).toBe(expected) // Object.is equality\n"
    "\n"
    "    Expected: 2\n"
    "    Received: 1\n"
    "\n"
    "Test Suites: 1 failed, 1 total\n"
    "Tests:       1 failed, 1 total\n"
    "Snapshots:   0 total\n"
    "Time:        5.93 s\n"
    'Ran all test suites within paths "src/fail_test.test.ts".\n'
)

REAL_JEST_FORCEXIT_STDERR = (
    "PASS integration test/testing/foxden_quoting/fetchQuote.test.ts\n"
    "  fetchQuote tests\n"
    "    \u2713 quote response typename is not GetQuoteOk (2 ms)\n"
    "    \u2713 able to return the quotes successfully  (1 ms)\n"
    "\n"
    "Test Suites: 1 passed, 1 total\n"
    "Tests:       2 passed, 2 total\n"
    "Snapshots:   1 passed, 1 total\n"
    "Time:        6.502 s, estimated 7 s\n"
    "Ran all test suites within paths "
    '"test/testing/foxden_quoting/fetchQuote.test.ts".\n'
    "Force exiting Jest: Have you considered using "
    "`--detectOpenHandles` to detect async operations that kept "
    "running after all tests finished?\n"
)

# Real Jest error output from SPIDERPLUS-web PR #13518
REAL_JEST_ESM_ERROR = """FAIL unit tests/js/unit/annotation/print_dialog.kyuden.test.js
  ● Test suite failed to run

    Jest encountered an unexpected token

    Jest failed to parse a file. This happens e.g. when your code or its dependencies use non-standard JavaScript syntax, or when Jest is not configured to support such syntax.

    Out of the box Jest supports Babel, which will be used to transform your files into valid JS based on your Babel configuration.

    By default "node_modules" folder is ignored by transformers.

    Here's what you can do:
     • If you are trying to use ECMAScript Modules, see https://jestjs.io/docs/ecmascript-modules for how to enable it.
     • If you are trying to use TypeScript, see https://jestjs.io/docs/getting-started#using-typescript
     • To have some of your "node_modules" files transformed, you can specify a custom "transformIgnorePatterns" in your config.
     • If you need a custom transformation specify a "transform" option in your config.
     • If you simply want to mock your non-JS modules (e.g. binary assets) you can stub them out with the "moduleNameMapper" config option.

    You'll find more details and examples of these config options in the docs:
    https://jestjs.io/docs/configuration
    For information about custom transformations, see:
    https://jestjs.io/docs/code-transformation

    Details:

    /tmp/spiderplus/SPIDERPLUS-web/pr-13518/tests/js/unit/_globalSetup.mjs:2
    import {JSDOM} from 'jsdom';
    ^^^^^^

    SyntaxError: Cannot use import statement outside a module

      at Runtime.createScriptFromCode (node_modules/jest-runtime/build/index.js:1505:14)

Test Suites: 1 failed, 1 total
Tests:       0 total
Snapshots:   0 total
Time:        0.216 s
Ran all test suites matching /tests\\/js\\/unit\\/annotation\\/print_dialog.kyuden.test.js/i."""


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.get_test_script_name", return_value=(None, ""))
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_captures_full_esm_error(
    mock_exists, mock_subprocess, _mock_get_test_script_name, create_test_base_args
):
    """Verify the full error output is kept, including the file path and stack trace."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout=REAL_JEST_ESM_ERROR,
        stderr="",
    )

    base_args = create_test_base_args(
        owner="spiderplus",
        repo="SPIDERPLUS-web",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["tests/js/unit/annotation/print_dialog.kyuden.test.js"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is False
    assert "tests/js/unit/annotation/print_dialog.kyuden.test.js" in result.error_files
    errors_joined = "\n".join(result.errors)
    assert "_globalSetup.mjs:2" in errors_joined
    assert "SyntaxError: Cannot use import statement outside a module" in errors_joined
    # Runtime.createScriptFromCode is a node_modules stack frame, correctly stripped by minimize_jest_test_logs


@pytest.mark.asyncio
@patch(
    "services.jest.run_js_ts_test.detect_package_manager", return_value=("npm", "", "")
)
@patch(
    "services.jest.run_js_ts_test.get_test_script_name",
    return_value=("test:unit", "jest --selectProjects unit"),
)
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_uses_test_unit_script(
    mock_exists,
    mock_subprocess,
    _mock_get_test_script_name,
    _mock_detect_pm,
    create_test_base_args,
):
    """Verify that when get_test_script_name returns 'test:unit', the command uses
    'npm run test:unit --' instead of 'npm test --'."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
        new_branch="feature",
        token="token",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["tests/js/unit/annotation/print_dialog.kyuden.test.js"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True

    # First call is the test run, last is git diff
    cmd = mock_subprocess.call_args_list[0][0][0]
    assert "run" in cmd
    assert "test:unit" in cmd


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_exit_code_1_all_pass_in_stderr_treated_as_success(
    mock_exists, mock_subprocess, create_test_base_args
):
    """Real Jest output: PASS goes to stderr, not stdout (captured from
    foxden-rating-quoting-backend 2026-03-23). When --forceExit causes exit
    code 1 but all tests passed, treat as success."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="",
        stderr=REAL_JEST_PASS_STDERR,
    )

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/services/query/getQuote/fetchQuote.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True
    assert result.errors == []
    assert result.error_files == set()


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_forcexit_pass_in_stderr_treated_as_success(
    mock_exists, mock_subprocess, create_test_base_args
):
    """Real Jest --forceExit output: tests pass but exit code 1 because of
    uncleaned resources (MongoDB connections). PASS and forceExit message both
    in stderr, stdout has only coverage tables."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="",
        stderr=REAL_JEST_FORCEXIT_STDERR,
    )

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["test/testing/foxden_quoting/fetchQuote.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True
    assert result.errors == []
    assert result.error_files == set()


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_real_fail_in_stderr_treated_as_failure(
    mock_exists, mock_subprocess, create_test_base_args
):
    """Real Jest FAIL output (captured 2026-03-23): FAIL goes to stderr.
    Verifies the combined stdout+stderr check correctly detects failures."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="",
        stderr=REAL_JEST_FAIL_STDERR,
    )

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/fail_test.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is False
    assert len(result.errors) > 0
    assert "src/fail_test.test.ts" in result.error_files


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.kill_processes_by_name")
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_kills_mongod_before_tests(
    mock_exists, mock_subprocess, mock_kill, create_test_base_args
):
    """Verify kill_processes_by_name('mongod') is called before running tests."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )

    mock_kill.assert_called_once_with("mongod")


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_includes_force_exit(
    mock_exists, mock_subprocess, create_test_base_args
):
    """Verify --forceExit is in the jest command to prevent hangs from
    uncleaned resources like MongoDB connections."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )

    # First call is the jest run
    jest_cmd = mock_subprocess.call_args_list[0][0][0]
    assert "--forceExit" in jest_cmd


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_find_related_tests_with_only_test_files(
    mock_exists, mock_subprocess, create_test_base_args
):
    """--findRelatedTests with only test files (no source files) should work.
    Jest recognizes test files and runs them directly."""
    mock_exists.side_effect = lambda p: "jest" in p and "vitest" not in p
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=["src/index.test.ts"],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True

    cmd = mock_subprocess.call_args_list[0][0][0]
    assert "--findRelatedTests" in cmd
    assert "src/index.test.ts" in cmd


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_find_related_tests_with_both(
    mock_exists, mock_subprocess, create_test_base_args
):
    """When both test files and source files are provided, --findRelatedTests
    receives all files so jest discovers dependent tests for source files
    AND runs explicit test files."""
    mock_exists.side_effect = lambda p: "jest" in p and "vitest" not in p
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=["src/utils.ts"],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True

    cmd = mock_subprocess.call_args_list[0][0][0]
    assert "--findRelatedTests" in cmd
    assert "src/index.test.ts" in cmd
    assert "src/utils.ts" in cmd


@pytest.mark.asyncio
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_always_uses_find_related_tests(
    mock_exists, mock_subprocess, create_test_base_args
):
    """--findRelatedTests is always used, even when no source files are provided."""
    mock_exists.side_effect = lambda p: "jest" in p and "vitest" not in p
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True

    cmd = mock_subprocess.call_args_list[0][0][0]
    assert "--findRelatedTests" in cmd
    assert "src/index.test.ts" in cmd


@pytest.mark.asyncio
@patch(
    "services.jest.run_js_ts_test.detect_package_manager", return_value=("npm", "", "")
)
@patch(
    "services.jest.run_js_ts_test.get_test_script_name",
    return_value=("test", "jest"),
)
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_vitest_binary_but_jest_script_uses_find_related_tests(
    mock_exists,
    mock_subprocess,
    _mock_get_test_script_name,
    _mock_detect_pm,
    create_test_base_args,
):
    """Bug fix from gitautoai/website: "test": "jest" but both jest AND vitest
    binaries exist in node_modules/.bin/. Runner detection must use the script
    value, not binary existence. Should use --findRelatedTests (jest), not --related (vitest).
    """
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True
    assert result.runner_name == "jest"

    cmd = mock_subprocess.call_args_list[0][0][0]
    assert "--findRelatedTests" in cmd
    assert "--related" not in cmd


@pytest.mark.asyncio
@patch(
    "services.jest.run_js_ts_test.detect_package_manager", return_value=("npm", "", "")
)
@patch(
    "services.jest.run_js_ts_test.get_test_script_name",
    return_value=("test", "vitest run"),
)
@patch("services.jest.run_js_ts_test.subprocess.run")
@patch("services.jest.run_js_ts_test.os.path.exists")
async def test_run_js_ts_test_jest_binary_but_vitest_script_uses_related(
    mock_exists,
    mock_subprocess,
    _mock_get_test_script_name,
    _mock_detect_pm,
    create_test_base_args,
):
    """Inverse case from ghostwriter: "test": "vitest run" but jest binary also
    exists. Should use --related (vitest flag), not --findRelatedTests (jest flag)."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = create_test_base_args(
        owner="test",
        repo="test",
        clone_dir="/tmp/clone",
    )
    result = await run_js_ts_test(
        base_args=base_args,
        test_file_paths=["src/index.test.ts"],
        source_file_paths=[],
        impl_file_to_collect_coverage_from="",
    )
    assert result.success is True
    assert result.runner_name == "vitest"

    cmd = mock_subprocess.call_args_list[0][0][0]
    assert "--related" in cmd
    assert "--findRelatedTests" not in cmd
