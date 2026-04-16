import os
import shutil
import subprocess
from dataclasses import dataclass, field

from constants.aws import SUBPROCESS_TIMEOUT_SECONDS
from constants.mongoms import MONGOMS_MAJOR_TO_MONGODB_VERSION
from services.jest.parse_coverage_json import Coverage, parse_coverage_json
from services.mongoms.get_archive_name import get_mongoms_archive_name
from services.mongoms.get_distro_for_mongodb_server_version import (
    get_distro_for_mongodb_server_version,
)
from services.mongoms.get_mongodb_server_version import get_mongodb_server_version
from services.node.get_dependency_major_version import get_dependency_major_version
from services.node.detect_package_manager import detect_package_manager
from services.node.get_test_script_name import get_test_script_name
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.logs.minimize_jest_test_logs import minimize_jest_test_logs
from utils.process.kill_processes_by_name import kill_processes_by_name


@dataclass
class JsTsTestResult:
    success: bool = True
    errors: list[str] = field(default_factory=list)
    error_files: set[str] = field(default_factory=set)
    runner_name: str = ""
    updated_snapshots: set[str] = field(default_factory=set)
    coverage: Coverage | None = None


@handle_exceptions(
    default_return_value=JsTsTestResult(),
    raise_on_error=False,
)
async def run_js_ts_test(
    *,
    base_args: BaseArgs,
    test_file_paths: list[str],
    source_file_paths: list[str],
    impl_file_to_collect_coverage_from: str,
):
    if not test_file_paths and not source_file_paths:
        logger.info("test: No test or source files to run")
        return JsTsTestResult()

    clone_dir = base_args.get("clone_dir", "")
    if not clone_dir:
        logger.warning("test: No clone_dir provided, skipping")
        return JsTsTestResult()

    # Check which binaries exist
    jest_bin = os.path.join(clone_dir, "node_modules", ".bin", "jest")
    vitest_bin = os.path.join(clone_dir, "node_modules", ".bin", "vitest")
    if not os.path.exists(vitest_bin) and not os.path.exists(jest_bin):
        logger.info("test: No test runner (jest/vitest) installed locally, skipping")
        return JsTsTestResult()

    # Build base command and determine actual runner name. The test script in package.json may invoke a different runner than the binary (e.g. vitest binary exists but "test" script runs jest). runner_name must match the actual runner because CLI flags differ (--related vs --findRelatedTests).
    test_script_name, test_script_value = get_test_script_name(clone_dir)
    if test_script_name:
        pkg_manager, _, _ = detect_package_manager(clone_dir)
        base_cmd = [pkg_manager, "run", test_script_name, "--"]
        runner_name = "vitest" if "vitest" in test_script_value else "jest"
    elif os.path.exists(vitest_bin):
        runner_name = "vitest"
        base_cmd = [vitest_bin]
    else:
        runner_name = "jest"
        base_cmd = [jest_bin]

    # CI=true disables watch mode and interactive prompts for both jest and vitest
    env = os.environ.copy()
    env["CI"] = "true"

    # MongoMemoryServer looks for mongod binary here. CodeBuild caches it to S3 as mongodb-binaries.tar.gz, extracted alongside node_modules by download_and_extract_s3_deps into {clone_dir}/mongodb-binaries/.
    env["MONGOMS_DOWNLOAD_DIR"] = os.path.join(clone_dir, "mongodb-binaries")

    # MONGOMS_ARCHIVE_NAME bypasses OS auto-detection entirely by specifying the full archive filename. Pre-cached by CodeBuild to S3.
    archive_name = get_mongoms_archive_name(clone_dir)
    if archive_name:
        env["MONGOMS_ARCHIVE_NAME"] = archive_name
        # MONGOMS_DISTRO must match the distro in the archive name. MongoDB 7.0+ uses amazon2023, 6.0.x uses amazon2.
        mongoms_major = get_dependency_major_version(clone_dir, "mongodb-memory-server")
        mongodb_server_version = get_mongodb_server_version(clone_dir)
        if not mongodb_server_version and mongoms_major:
            mongodb_server_version = MONGOMS_MAJOR_TO_MONGODB_VERSION.get(mongoms_major)
        if mongodb_server_version:
            env["MONGOMS_DISTRO"] = get_distro_for_mongodb_server_version(
                mongodb_server_version
            )

    # Kill any lingering mongod processes from previous verify_task_is_complete calls.
    # MongoMemoryServer uses a fixed port (e.g. 34213) hardcoded in customer tests.
    # If a previous jest run's globalTeardown didn't fully clean up, the stale mongod causes "namespace already exists, but with different options" errors.
    kill_processes_by_name("mongod")

    # When impl_file_to_collect_coverage_from is set, add coverage flags to measure statement/branch/function/line coverage using Istanbul instead of V8, because V8 inflates branch counts in single-file mode (??, &&, ternary counted differently).
    use_coverage = bool(impl_file_to_collect_coverage_from)
    coverage_dir = os.path.join(clone_dir, "coverage")

    # Run all test files in a single invocation so Jest/vitest produces a single merged coverage report.
    # -u (--updateSnapshot) auto-updates stale .snap files instead of failing
    # --forceExit: Force jest to exit after tests complete, preventing hangs from uncleaned resources (e.g. MongoDB connections) that survive globalTeardown.
    find_flag = "--related" if runner_name == "vitest" else "--findRelatedTests"
    all_files = test_file_paths + source_file_paths
    cmd = base_cmd + [find_flag] + all_files + ["-u", "--forceExit"]
    if use_coverage and runner_name == "jest":
        cmd.extend(
            [
                "--coverage",
                f"--coverageDirectory={coverage_dir}",
                "--coverageProvider=babel",
                "--coverageReporters=json",
                f"--collectCoverageFrom={impl_file_to_collect_coverage_from}",
            ]
        )
    elif use_coverage and runner_name == "vitest":
        cmd.extend(
            [
                "--coverage.enabled",
                f"--coverage.reportsDirectory={coverage_dir}",
                "--coverage.provider=istanbul",
                "--coverage.reporter=json",
                f"--coverage.include={impl_file_to_collect_coverage_from}",
            ]
        )
    logger.info("%s: Running %s...", runner_name, ", ".join(test_file_paths))
    all_errors: list[str] = []
    error_files: set[str] = set()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
        cwd=clone_dir,
        env=env,
    )
    if result.returncode != 0:
        output = result.stdout + result.stderr
        # Jest/yarn may exit with code 1 due to environment issues (teardown failures, MongoDB Memory Server cleanup, etc.) even when all tests pass. Without this check, the agent loops for 900s trying to fix it, and if CI also fails, GitAuto gets re-triggered - burning more Lambda time and cost.
        # Check combined output because Jest writes PASS/FAIL to stderr, not stdout.
        if "PASS " in output and "FAIL " not in output:
            logger.warning(
                "%s: exit code %d but all tests PASSED, treating as success",
                runner_name,
                result.returncode,
            )
        else:
            # Parse which specific files failed from Jest output (e.g. "FAIL src/a.test.ts")
            for test_file in test_file_paths:
                if f"FAIL {test_file}" in output:
                    error_files.add(test_file)
            # If no specific files detected, mark all as failed
            if not error_files:
                error_files.update(test_file_paths)
            all_errors.append(minimize_jest_test_logs(output.strip()))
            logger.warning("%s: tests failed:\n%s", runner_name, output.strip())

    # Parse coverage data if coverage was enabled and tests passed
    coverage: Coverage | None = None
    if use_coverage and not error_files:
        coverage = parse_coverage_json(coverage_dir, impl_file_to_collect_coverage_from)
        logger.info(
            "coverage: %s - stmt=%s%%, branch=%s%%, func=%s%%, line=%s%%",
            impl_file_to_collect_coverage_from,
            coverage.statement_pct,
            coverage.branch_pct,
            coverage.function_pct,
            coverage.line_pct,
        )
    if os.path.isdir(coverage_dir):
        shutil.rmtree(coverage_dir, ignore_errors=True)
        logger.info("coverage: Cleaned up %s", coverage_dir)

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
        return JsTsTestResult(
            success=True,
            errors=[],
            error_files=set(),
            runner_name=runner_name,
            updated_snapshots=updated_snapshots,
            coverage=coverage,
        )

    return JsTsTestResult(
        success=False,
        errors=all_errors,
        error_files=error_files,
        runner_name=runner_name,
        updated_snapshots=updated_snapshots,
        coverage=coverage,
    )
