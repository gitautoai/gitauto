import os
import shutil
import subprocess
from dataclasses import dataclass, field

from constants.aws import SUBPROCESS_TIMEOUT_SECONDS
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_python_test_file import is_python_test_file
from utils.logging.logging_config import logger
from utils.logs.remove_pytest_sections import remove_pytest_sections


@dataclass
class PytestResult:
    success: bool = True
    errors: list[str] = field(default_factory=list)
    error_files: set[str] = field(default_factory=set)


@handle_exceptions(default_return_value=PytestResult(), raise_on_error=False)
async def run_pytest_test(
    *,
    base_args: BaseArgs,
    test_file_paths: list[str],
):
    py_test_files = [f for f in test_file_paths if is_python_test_file(f)]
    if not py_test_files:
        logger.info("pytest: No Python test files to run")
        return PytestResult()

    clone_dir = base_args.get("clone_dir")
    if not clone_dir:
        logger.warning("pytest: No clone_dir provided, skipping")
        return PytestResult()

    # Detect pytest binary: venv first, then system
    pytest_bin = None
    for venv_dir in ("venv", ".venv"):
        candidate = os.path.join(clone_dir, venv_dir, "bin", "pytest")
        if os.path.exists(candidate):
            logger.info("pytest: Found binary at %s", candidate)
            pytest_bin = candidate
            logger.info("pytest: breaking venv scan")
            break
    if not pytest_bin:
        logger.info("pytest: No venv binary, falling back to system pytest")
        pytest_bin = shutil.which("pytest")
        if pytest_bin:
            logger.info("pytest: Found system binary at %s", pytest_bin)
    if not pytest_bin:
        logger.info("pytest: No pytest binary found, skipping")
        return PytestResult()

    # --tb=short: shorter tracebacks, --no-header: skip version/plugin info, -q: minimal output
    # --import-mode=importlib: let duplicate test filenames across directories coexist without the "import file mismatch" collection error (pytest's default prepend mode imports by module name and collides on same-named files when the repo has no __init__.py).
    cmd = (
        [pytest_bin]
        + py_test_files
        + [
            "--tb=short",
            "--no-header",
            "-q",
            "--import-mode=importlib",
        ]
    )
    logger.info("pytest: Running %s...", ", ".join(py_test_files))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
        cwd=clone_dir,
    )

    # Exit code 5 = no tests collected (e.g., test files removed), treat as success
    if result.returncode == 5:
        logger.info("pytest: No tests collected (exit code 5), treating as success")
        return PytestResult()

    if result.returncode == 0:
        logger.info("pytest: All tests passed")
        return PytestResult()

    output = result.stdout + result.stderr
    error_files: set[str] = set()

    # Parse "FAILED test_file.py::test_name" lines
    for line in output.splitlines():
        if line.startswith("FAILED "):
            logger.info("pytest: parsing FAILED line")
            # Format: "FAILED path/test_file.py::test_name - reason"
            failed_part = line[len("FAILED ") :]
            file_part = failed_part.split("::")[0].strip()
            for test_file in py_test_files:
                if test_file == file_part or test_file.endswith("/" + file_part):
                    logger.info("pytest: matched FAILED to %s", test_file)
                    error_files.add(test_file)

    if not error_files:
        logger.info("pytest: no FAILED lines parsed, falling back to all test files")
        error_files.update(py_test_files)

    cleaned_output = remove_pytest_sections(output.strip())
    logger.warning("pytest: tests failed:\n%s", cleaned_output)

    return PytestResult(
        success=False,
        errors=[cleaned_output] if cleaned_output else [output.strip()],
        error_files=error_files,
    )
