import os
import subprocess
from dataclasses import dataclass

from constants.aws import EFS_TIMEOUT_SECONDS
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@dataclass
class TscResult:
    success: bool
    errors: list[str]
    error_files: set[str]


@handle_exceptions(
    default_return_value=TscResult(success=True, errors=[], error_files=set()),
    raise_on_error=False,
)
async def run_tsc_check(*, base_args: BaseArgs, file_paths: list[str]):
    ts_files = [f for f in file_paths if f.endswith((".ts", ".tsx"))]
    if not ts_files:
        logger.info("tsc: No TypeScript files to check")
        return TscResult(success=True, errors=[], error_files=set())

    clone_dir = base_args.get("clone_dir", "")
    if not clone_dir:
        logger.warning("tsc: No clone_dir provided, skipping")
        return TscResult(success=True, errors=[], error_files=set())

    # Check for tsconfig - prefer relaxed test configs over strict base config
    test_configs = ["tsconfig.test.json", "tsconfig.spec.json", "tsconfig.jest.json"]
    found_test_configs = [
        c for c in test_configs if os.path.exists(os.path.join(clone_dir, c))
    ]

    if len(found_test_configs) == 1:
        tsconfig = found_test_configs[0]
    elif os.path.exists(os.path.join(clone_dir, "tsconfig.json")):
        tsconfig = "tsconfig.json"
    else:
        logger.info("tsc: No tsconfig found, skipping type check")
        return TscResult(success=True, errors=[], error_files=set())

    # Check if tsc exists locally
    tsc_bin = os.path.join(clone_dir, "node_modules", ".bin", "tsc")
    if not os.path.exists(tsc_bin):
        logger.info("tsc: Not installed locally, skipping")
        return TscResult(success=True, errors=[], error_files=set())

    # Run tsc --noEmit to check types without generating output
    cmd = [tsc_bin, "--noEmit", "-p", tsconfig]
    logger.info("tsc: Running type check with %s...", tsconfig)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=EFS_TIMEOUT_SECONDS,
        check=False,
        cwd=clone_dir,
    )

    if result.returncode == 0:
        logger.info("tsc: No type errors found")
        return TscResult(success=True, errors=[], error_files=set())

    # Parse tsc output - format is "file(line,col): error TS1234: message"
    errors: list[str] = []
    error_files: set[str] = set()
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            errors.append(line)
            # Extract file path from "file(line,col): error..."
            if "(" in line:
                file_path = line.split("(")[0]
                if not file_path.startswith("node_modules"):
                    error_files.add(file_path)

    logger.warning("tsc: Type errors found:\n%s", "\n".join(errors))
    return TscResult(success=False, errors=errors, error_files=error_files)
