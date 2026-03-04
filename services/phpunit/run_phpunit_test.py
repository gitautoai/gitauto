import glob
import os
import subprocess
from dataclasses import dataclass, field

from constants.aws import EFS_TIMEOUT_SECONDS
from constants.files import PHP_TEST_FILE_EXTENSIONS
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@dataclass
class PhpunitResult:
    success: bool = True
    errors: list[str] = field(default_factory=list)
    error_files: set[str] = field(default_factory=set)


@handle_exceptions(default_return_value=PhpunitResult(), raise_on_error=False)
async def run_phpunit_test(
    *,
    base_args: BaseArgs,
    test_file_paths: list[str],
):
    php_test_files = [
        f for f in test_file_paths if f.endswith(PHP_TEST_FILE_EXTENSIONS)
    ]
    if not php_test_files:
        logger.info("phpunit: No PHP test files to run")
        return PhpunitResult()

    clone_dir = base_args.get("clone_dir")
    if not clone_dir:
        logger.warning("phpunit: No clone_dir provided, skipping")
        return PhpunitResult()

    # Standard location first, then bamarni/composer-bin-plugin vendor-bin/*/
    phpunit_bin = os.path.join(clone_dir, "vendor", "bin", "phpunit")
    if not os.path.exists(phpunit_bin):
        matches = glob.glob(
            os.path.join(clone_dir, "vendor-bin", "*", "vendor", "bin", "phpunit")
        )
        phpunit_bin = matches[0] if matches else None
    if not phpunit_bin:
        logger.info("phpunit: No phpunit binary found, skipping")
        return PhpunitResult()

    # Build base command with PHP deprecation suppression for PHP 8.x running older codebases
    base_cmd = ["php", "-d", "error_reporting=E_ALL&~E_DEPRECATED", phpunit_bin]

    # Detect bootstrap: if phpunit.xml or phpunit.xml.dist exists, PHPUnit auto-discovers it.
    # Otherwise, fall back to vendor/autoload.php.
    has_config = os.path.exists(
        os.path.join(clone_dir, "phpunit.xml")
    ) or os.path.exists(os.path.join(clone_dir, "phpunit.xml.dist"))
    if not has_config:
        autoload = os.path.join(clone_dir, "vendor", "autoload.php")
        if os.path.exists(autoload):
            base_cmd.extend(["--bootstrap", autoload])

    # Run all test files in a single invocation for speed
    cmd = base_cmd + php_test_files
    logger.info("phpunit: Running %s...", ", ".join(php_test_files))
    all_errors: list[str] = []
    error_files: set[str] = set()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=EFS_TIMEOUT_SECONDS,
        check=False,
        cwd=clone_dir,
    )
    if result.returncode != 0:
        output = result.stdout + result.stderr
        # PHPUnit prints "OK" when all tests pass, even with non-zero exit (e.g., deprecation warnings)
        if "OK (" in result.stdout and "FAILURES!" not in result.stdout:
            logger.warning(
                "phpunit: exit code %d but all tests OK, treating as success",
                result.returncode,
            )
        else:
            # Parse which specific files failed from PHPUnit output
            for test_file in php_test_files:
                if test_file in output:
                    error_files.add(test_file)
            # If no specific files detected, mark all as failed
            if not error_files:
                error_files.update(php_test_files)
            all_errors.append(output.strip())
            logger.warning("phpunit: tests failed:\n%s", output.strip())

    if not error_files:
        logger.info("phpunit: All tests passed")
        return PhpunitResult(success=True, errors=[], error_files=set())

    return PhpunitResult(success=False, errors=all_errors, error_files=error_files)
