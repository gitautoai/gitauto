import os
import subprocess
from dataclasses import dataclass

from constants.aws import EFS_TIMEOUT_SECONDS
from constants.files import JS_TEST_FILE_EXTENSIONS
from services.github.types.github_types import BaseArgs
from services.node.detect_package_manager import detect_package_manager
from services.node.get_test_script import get_test_script
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@dataclass
class JestResult:
    success: bool
    errors: list[str]
    error_files: set[str]
    runner_name: str


@handle_exceptions(
    default_return_value=JestResult(
        success=True, errors=[], error_files=set(), runner_name=""
    ),
    raise_on_error=False,
)
async def run_jest_test(*, base_args: BaseArgs, file_paths: list[str]):
    test_files = [f for f in file_paths if f.endswith(JS_TEST_FILE_EXTENSIONS)]
    if not test_files:
        logger.info("test: No test files to run")
        return JestResult(success=True, errors=[], error_files=set(), runner_name="")

    clone_dir = base_args.get("clone_dir", "")
    if not clone_dir:
        logger.warning("test: No clone_dir provided, skipping")
        return JestResult(success=True, errors=[], error_files=set(), runner_name="")

    # Determine runner name for logging (jest vs vitest)
    jest_bin = os.path.join(clone_dir, "node_modules", ".bin", "jest")
    vitest_bin = os.path.join(clone_dir, "node_modules", ".bin", "vitest")
    if os.path.exists(vitest_bin):
        runner_name = "vitest"
    elif os.path.exists(jest_bin):
        runner_name = "jest"
    else:
        logger.info("test: No test runner (jest/vitest) installed locally, skipping")
        return JestResult(success=True, errors=[], error_files=set(), runner_name="")

    # Prefer npm/yarn/pnpm test if package.json has a test script
    test_script = get_test_script(clone_dir)
    if test_script:
        owner = base_args.get("owner", "")
        repo = base_args.get("repo", "")
        branch = base_args.get("new_branch", "")
        token = base_args.get("token", "")
        pkg_manager, _, _ = detect_package_manager(
            clone_dir, owner, repo, branch, token
        )
        # Pass test files after -- to forward them to the test runner
        cmd = [pkg_manager, "test", "--"] + test_files
        logger.info(
            "%s test: Running tests on %d files...", pkg_manager, len(test_files)
        )
    else:
        # Fallback to direct binary call
        test_bin = vitest_bin if runner_name == "vitest" else jest_bin
        cmd = [test_bin] + test_files
        logger.info("%s: Running tests on %d files...", runner_name, len(test_files))

    # CI=true disables watch mode and interactive prompts for both jest and vitest
    env = os.environ.copy()
    env["CI"] = "true"

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=EFS_TIMEOUT_SECONDS,
        check=False,
        cwd=clone_dir,
        env=env,
    )

    if result.returncode == 0:
        logger.info("%s: All tests passed", runner_name)
        return JestResult(
            success=True, errors=[], error_files=set(), runner_name=runner_name
        )

    # Parse test output for errors
    errors: list[str] = []
    error_files: set[str] = set()
    output = result.stdout + result.stderr

    # Extract failing test info
    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Jest/Vitest error patterns: "FAIL path/to/test.ts" or "● Test suite failed"
        if line.startswith("FAIL "):
            file_path = line[5:].strip()
            error_files.add(file_path)
            errors.append(line)
        elif "FAIL" in line and any(f in line for f in test_files):
            for f in test_files:
                if f in line:
                    error_files.add(f)
            errors.append(line)
        elif line.startswith("●") or "Error:" in line or "TypeError:" in line:
            errors.append(line)

    # If no specific errors parsed, include raw output
    if not errors and output.strip():
        errors = [line for line in output.split("\n") if line.strip()]

    logger.warning("%s: Test failures:\n%s", runner_name, "\n".join(errors))
    return JestResult(
        success=False, errors=errors, error_files=error_files, runner_name=runner_name
    )
