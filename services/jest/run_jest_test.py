import os
import subprocess
from dataclasses import dataclass, field

from constants.aws import EFS_TIMEOUT_SECONDS
from constants.files import JS_TEST_FILE_EXTENSIONS
from services.efs.get_efs_dir import get_efs_dir
from services.github.types.github_types import BaseArgs
from services.jest.get_mongoms_distro import get_mongoms_distro
from services.node.detect_package_manager import detect_package_manager
from services.node.get_test_script_name import get_test_script_name
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@dataclass
class JestResult:
    success: bool = True
    errors: list[str] = field(default_factory=list)
    error_files: set[str] = field(default_factory=set)
    runner_name: str = ""
    updated_snapshots: set[str] = field(default_factory=set)


@handle_exceptions(
    default_return_value=JestResult(),
    raise_on_error=False,
)
async def run_jest_test(*, base_args: BaseArgs, file_paths: list[str]):
    test_files = [f for f in file_paths if f.endswith(JS_TEST_FILE_EXTENSIONS)]
    if not test_files:
        logger.info("test: No test files to run")
        return JestResult()

    clone_dir = base_args.get("clone_dir", "")
    if not clone_dir:
        logger.warning("test: No clone_dir provided, skipping")
        return JestResult()

    # Determine runner name for logging (jest vs vitest)
    jest_bin = os.path.join(clone_dir, "node_modules", ".bin", "jest")
    vitest_bin = os.path.join(clone_dir, "node_modules", ".bin", "vitest")
    if os.path.exists(vitest_bin):
        runner_name = "vitest"
    elif os.path.exists(jest_bin):
        runner_name = "jest"
    else:
        logger.info("test: No test runner (jest/vitest) installed locally, skipping")
        return JestResult()

    # Build base command
    owner = base_args["owner"]
    repo = base_args["repo"]
    test_script_name = get_test_script_name(clone_dir)
    if test_script_name:
        branch = base_args.get("new_branch", "")
        token = base_args.get("token", "")
        pkg_manager, _, _ = detect_package_manager(
            clone_dir, owner, repo, branch, token
        )
        base_cmd = [pkg_manager, "run", test_script_name, "--"]
    else:
        base_cmd = [vitest_bin if runner_name == "vitest" else jest_bin]

    # CI=true disables watch mode and interactive prompts for both jest and vitest
    env = os.environ.copy()
    env["CI"] = "true"

    # MongoMemoryServer needs a writable cache dir for the mongod binary.
    # Lambda's home dir (/home/sbx_user1051) doesn't exist, so point it to the EFS repo dir.
    # We don't copy this to /tmp unlike node_modules because it's a single ~100MB file (fine to read over NFS), not 150k+ small files.
    efs_dir = get_efs_dir(owner, repo)
    env["MONGOMS_DOWNLOAD_DIR"] = os.path.join(efs_dir, ".cache", "mongodb-binaries")
    mongoms_distro = get_mongoms_distro(clone_dir)
    if mongoms_distro:
        env["MONGOMS_DISTRO"] = mongoms_distro

    # Kill any lingering mongod processes from previous verify_task_is_complete calls.
    # MongoMemoryServer uses a fixed port (e.g. 34213) hardcoded in customer tests.
    # If a previous jest run's globalTeardown didn't fully clean up, the stale mongod causes "namespace already exists, but with different options" errors.
    subprocess.run(
        ["pkill", "-f", "mongod"],
        capture_output=True,
        text=True,
        check=False,  # if no mongod processes exist, pkill exits non-zero, silently ignored.
    )

    # Run each test file individually so we know exactly which files fail
    all_errors: list[str] = []
    error_files: set[str] = set()
    for test_file in test_files:
        # -u (--updateSnapshot) auto-updates stale .snap files instead of failing
        # --forceExit: Force jest to exit after tests complete, preventing hangs from uncleaned resources (e.g. MongoDB connections) that survive globalTeardown.
        cmd = base_cmd + [test_file, "-u", "--forceExit"]
        logger.info("%s: Running %s...", runner_name, test_file)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=EFS_TIMEOUT_SECONDS,
            check=False,
            cwd=clone_dir,
            env=env,
        )
        if result.returncode != 0:
            output = result.stdout + result.stderr
            # Jest/yarn may exit with code 1 due to environment issues (teardown failures, MongoDB Memory Server cleanup, etc.) even when all tests pass. Without this check, the agent loops for 900s trying to fix it, and if CI also fails, GitAuto gets re-triggered - burning more Lambda time and cost.
            if "PASS " in result.stdout and "FAIL " not in result.stdout:
                logger.warning(
                    "%s: %s exit code %d but all tests PASSED, treating as success",
                    runner_name,
                    test_file,
                    result.returncode,
                )
                continue
            error_files.add(test_file)
            all_errors.append(output.strip())
            logger.warning("%s: %s failed:\n%s", runner_name, test_file, output.strip())

    # Detect snapshot files updated by -u flag
    updated_snapshots: set[str] = set()
    diff_result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True,
        text=True,
        check=False,
        cwd=clone_dir,
    )
    if diff_result.returncode == 0:
        for line in diff_result.stdout.strip().splitlines():
            if line.endswith(".snap"):
                updated_snapshots.add(line)
    if updated_snapshots:
        logger.info(
            "%s: Updated %d snapshot(s): %s",
            runner_name,
            len(updated_snapshots),
            updated_snapshots,
        )

    if not error_files:
        logger.info("%s: All tests passed", runner_name)
        return JestResult(
            success=True,
            errors=[],
            error_files=set(),
            runner_name=runner_name,
            updated_snapshots=updated_snapshots,
        )

    return JestResult(
        success=False,
        errors=all_errors,
        error_files=error_files,
        runner_name=runner_name,
        updated_snapshots=updated_snapshots,
    )
