# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch, MagicMock

import pytest

from services.github.types.github_types import BaseArgs
from services.jest.run_jest_test import run_jest_test


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_success(mock_exists, mock_subprocess, _mock_distro):
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
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is True
    assert result.errors == []
    assert result.error_files == set()


@pytest.mark.asyncio
async def test_run_jest_test_no_test_files():
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(
        base_args=base_args, file_paths=["src/index.ts", "README.md"]
    )
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_run_jest_test_no_clone_dir():
    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "",
        },
    )
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_no_runner(mock_exists):
    mock_exists.return_value = False

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is True
    assert result.errors == []


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_with_failures(mock_exists, mock_subprocess, _mock_distro):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="FAIL src/index.test.ts\n● Test suite failed to run\nError: Cannot find module",
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
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is False
    assert len(result.errors) > 0
    assert "src/index.test.ts" in result.error_files


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_detects_updated_snapshots(
    mock_exists, mock_subprocess, _mock_distro
):
    mock_exists.return_value = True
    pkill_result = MagicMock(returncode=0, stdout="", stderr="")
    jest_result = MagicMock(returncode=0, stdout="", stderr="")
    git_diff_result = MagicMock(
        returncode=0,
        stdout="src/__snapshots__/Button.test.tsx.snap\ntest/__snapshots__/utils.test.ts.snap\n",
    )
    mock_subprocess.side_effect = [pkill_result, jest_result, git_diff_result]

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is True
    assert result.updated_snapshots == {
        "src/__snapshots__/Button.test.tsx.snap",
        "test/__snapshots__/utils.test.ts.snap",
    }


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_no_snapshots_updated(
    mock_exists, mock_subprocess, _mock_distro
):
    mock_exists.return_value = True
    pkill_result = MagicMock(returncode=0, stdout="", stderr="")
    jest_result = MagicMock(returncode=0, stdout="", stderr="")
    git_diff_result = MagicMock(returncode=0, stdout="src/index.ts\n")
    mock_subprocess.side_effect = [pkill_result, jest_result, git_diff_result]

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is True
    assert result.updated_snapshots == set()


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_uses_vitest_when_no_jest(
    mock_exists, mock_subprocess, _mock_distro
):
    def exists_side_effect(path):
        # Jest doesn't exist, but vitest does
        if "jest" in path:
            return False
        return "vitest" in path or "node_modules" in path

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
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is True

    # Verify vitest was called (first call is pkill, second is the test, last is git diff)
    cmd = mock_subprocess.call_args_list[1][0][0]
    assert "vitest" in cmd[0]


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_spec_files(mock_exists, mock_subprocess, _mock_distro):
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
    result = await run_jest_test(
        base_args=base_args,
        file_paths=["src/utils.spec.ts", "src/helper.spec.jsx"],
    )
    assert result.success is True

    # 1 pkill + 2 test runs + 1 git diff = 4
    assert mock_subprocess.call_count == 4


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_multiple_failures(
    mock_exists, mock_subprocess, _mock_distro
):
    mock_exists.return_value = True
    # Both files fail
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="Error in test",
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
    result = await run_jest_test(
        base_args=base_args, file_paths=["src/a.test.ts", "src/b.test.ts"]
    )
    assert result.success is False
    assert "src/a.test.ts" in result.error_files
    assert "src/b.test.ts" in result.error_files


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_type_error_in_output(
    mock_exists, mock_subprocess, _mock_distro
):
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="TypeError: Cannot read property 'foo' of undefined",
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
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is False
    assert any("TypeError" in e for e in result.errors)


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_sets_mongoms_download_dir(
    mock_exists, mock_subprocess, _mock_distro
):
    """Verify MONGOMS_DOWNLOAD_DIR is set so MongoMemoryServer can cache mongod on EFS."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "clone_dir": "/tmp/clone",
        },
    )
    await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])

    # Verify jest was called with MONGOMS_DOWNLOAD_DIR in env (first call is pkill, second is jest)
    call_kwargs = mock_subprocess.call_args_list[1].kwargs
    env = call_kwargs["env"]
    assert "MONGOMS_DOWNLOAD_DIR" in env
    assert "test-owner" in env["MONGOMS_DOWNLOAD_DIR"]
    assert "test-repo" in env["MONGOMS_DOWNLOAD_DIR"]
    assert env["MONGOMS_DOWNLOAD_DIR"].endswith(".cache/mongodb-binaries")


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
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.get_test_script_name", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_captures_full_esm_error(
    mock_exists, mock_subprocess, _mock_get_test_script_name, _mock_distro
):
    """Verify the full error output is kept, including the file path and stack trace."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout=REAL_JEST_ESM_ERROR,
        stderr="",
    )

    base_args = cast(
        BaseArgs,
        {
            "owner": "spiderplus",
            "repo": "SPIDERPLUS-web",
            "clone_dir": "/tmp/clone",
        },
    )
    result = await run_jest_test(
        base_args=base_args,
        file_paths=["tests/js/unit/annotation/print_dialog.kyuden.test.js"],
    )
    assert result.success is False
    assert "tests/js/unit/annotation/print_dialog.kyuden.test.js" in result.error_files
    errors_joined = "\n".join(result.errors)
    assert "_globalSetup.mjs:2" in errors_joined
    assert "SyntaxError: Cannot use import statement outside a module" in errors_joined
    assert "Runtime.createScriptFromCode" in errors_joined


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch(
    "services.jest.run_jest_test.detect_package_manager", return_value=("npm", "", "")
)
@patch("services.jest.run_jest_test.get_test_script_name", return_value="test:unit")
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_uses_test_unit_script(
    mock_exists,
    mock_subprocess,
    _mock_get_test_script_name,
    _mock_detect_pm,
    _mock_distro,
):
    """Verify that when get_test_script_name returns 'test:unit', the command uses
    'npm run test:unit --' instead of 'npm test --'."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    base_args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_dir": "/tmp/clone",
            "new_branch": "feature",
            "token": "token",
        },
    )
    result = await run_jest_test(
        base_args=base_args,
        file_paths=["tests/js/unit/annotation/print_dialog.kyuden.test.js"],
    )
    assert result.success is True

    # First call is pkill, second is the test run, last is git diff
    cmd = mock_subprocess.call_args_list[1][0][0]
    assert "run" in cmd
    assert "test:unit" in cmd


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_exit_code_1_all_pass_treated_as_success(
    mock_exists, mock_subprocess, _mock_distro
):
    """When jest exits with code 1 but stdout shows all tests PASS (no FAIL),
    treat as success. Without this, the agent loops for 900s trying to fix it,
    and CI failure re-triggers GitAuto - burning more Lambda time and cost."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="PASS src/index.test.ts\n  Test suite\n    ✓ test 1\n    ✓ test 2\n\nTest Suites: 1 passed, 1 total",
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
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is True
    assert result.errors == []
    assert result.error_files == set()


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_exit_code_1_with_fail_treated_as_failure(
    mock_exists, mock_subprocess, _mock_distro
):
    """When jest exits with code 1 and stdout contains FAIL, treat as real failure."""
    mock_exists.return_value = True
    mock_subprocess.return_value = MagicMock(
        returncode=1,
        stdout="FAIL src/index.test.ts\n  ● Test suite failed to run\n\nTest Suites: 1 failed, 1 total",
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
    result = await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])
    assert result.success is False
    assert len(result.errors) > 0
    assert "src/index.test.ts" in result.error_files


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_kills_mongod_before_tests(
    mock_exists, mock_subprocess, _mock_distro
):
    """Verify pkill -f mongod is called before running tests to clean up stale
    MongoMemoryServer processes from previous verify_task_is_complete calls."""
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
    await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])

    # First call should be pkill, second is jest, third is git diff
    calls = mock_subprocess.call_args_list
    pkill_call = calls[0]
    assert pkill_call[0][0] == ["pkill", "-f", "mongod"]


@pytest.mark.asyncio
@patch("services.jest.run_jest_test.get_mongoms_distro", return_value=None)
@patch("services.jest.run_jest_test.subprocess.run")
@patch("services.jest.run_jest_test.os.path.exists")
async def test_run_jest_test_includes_force_exit(
    mock_exists, mock_subprocess, _mock_distro
):
    """Verify --forceExit is in the jest command to prevent hangs from
    uncleaned resources like MongoDB connections."""
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
    await run_jest_test(base_args=base_args, file_paths=["src/index.test.ts"])

    # Second call is the jest run (after pkill)
    jest_cmd = mock_subprocess.call_args_list[1][0][0]
    assert "--forceExit" in jest_cmd
