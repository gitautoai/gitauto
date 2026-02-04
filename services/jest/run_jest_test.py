import os
import subprocess
from dataclasses import dataclass

from constants.aws import EFS_TIMEOUT_SECONDS
from constants.files import JS_TEST_FILE_EXTENSIONS
from services.github.types.github_types import BaseArgs
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

    # Check if jest or vitest exists locally
    jest_bin = os.path.join(clone_dir, "node_modules", ".bin", "jest")
    vitest_bin = os.path.join(clone_dir, "node_modules", ".bin", "vitest")

    if os.path.exists(jest_bin):
        test_bin = jest_bin
        runner_name = "jest"
    elif os.path.exists(vitest_bin):
        test_bin = vitest_bin
        runner_name = "vitest"
    else:
        logger.info("test: No test runner (jest/vitest) installed locally, skipping")
        return JestResult(success=True, errors=[], error_files=set(), runner_name="")

    # Run tests on the specific test files
    cmd = [test_bin, "--no-coverage"] + test_files
    logger.info("%s: Running tests on %d files...", runner_name, len(test_files))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=EFS_TIMEOUT_SECONDS,
        check=False,
        cwd=clone_dir,
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
