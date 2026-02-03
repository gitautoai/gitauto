import asyncio
import difflib
import json
import os
import subprocess
from dataclasses import dataclass, field

from config import UTF8
from constants.aws import EFS_TIMEOUT_SECONDS
from services.github.files.get_eslint_config import get_eslint_config
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@dataclass
class UnreachableCodeResult:
    fixed_content: str | None = None
    unfixable_lines: dict[int, str] = field(default_factory=dict)


@handle_exceptions(default_return_value=UnreachableCodeResult(), raise_on_error=False)
async def fix_unreachable_code(
    *,
    file_path: str,
    repo_dir: str,
    clone_task: asyncio.Task,
    root_files: list[str],
    base_args: BaseArgs,
):
    result = UnreachableCodeResult()

    if not file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
        logger.info("Skipping unreachable code fix for non-JS/TS file: %s", file_path)
        return result

    logger.info("Waiting for clone to complete before ESLint fix")
    await clone_task
    logger.info("Clone completed, running ESLint --fix for %s", file_path)

    required_paths = [
        (
            "node_modules/@typescript-eslint/eslint-plugin",
            "@typescript-eslint/eslint-plugin",
        ),
        ("node_modules/@typescript-eslint/parser", "@typescript-eslint/parser"),
        ("node_modules/typescript", "typescript"),
    ]
    for path, name in required_paths:
        full_path = os.path.join(repo_dir, path)
        if not os.path.exists(full_path):
            logger.info("%s not found, skipping unreachable code fix", name)
            return result

    if "tsconfig.json" not in root_files:
        logger.info("No tsconfig.json found, skipping unreachable code fix")
        return result

    # Read original content to detect if --fix changed anything
    full_file_path = os.path.join(repo_dir, file_path)
    with open(full_file_path, "r", encoding=UTF8) as f:
        original_content = f.read()

    # Build ESLint command with --parser-options for typed linting fallback
    # This ensures typed linting works even if repo config lacks parserOptions.project
    cmd = (
        f"npx eslint {file_path} --fix "
        f"--rule '@typescript-eslint/no-unnecessary-condition: error' "
        f"--parser-options project:tsconfig.json "
        f"--format json"
    )
    logger.info("Running ESLint: %s", cmd)

    # Set environment for ESLint config mode (legacy configs need ESLINT_USE_FLAT_CONFIG=false)
    env = os.environ.copy()
    eslint_config = get_eslint_config(base_args)
    if eslint_config and eslint_config["filename"].startswith(".eslintrc"):
        env["ESLINT_USE_FLAT_CONFIG"] = "false"
        logger.info("Using legacy ESLint config mode")

    eslint_result = subprocess.run(
        cmd,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=EFS_TIMEOUT_SECONDS,
        check=False,
        shell=True,
        env=env,
    )
    logger.info("ESLint completed with return code %d", eslint_result.returncode)

    # Read fixed content
    with open(full_file_path, "r", encoding=UTF8) as f:
        fixed_content = f.read()

    # Only set fixed_content if something changed
    if fixed_content != original_content:
        result.fixed_content = fixed_content
        diff = difflib.unified_diff(
            original_content.splitlines(),
            fixed_content.splitlines(),
            fromfile=file_path,
            tofile=file_path,
            lineterm="",
        )
        logger.info("ESLint --fix changes to %s:\n%s", file_path, "\n".join(diff))

    # Parse remaining unfixable issues
    if eslint_result.stdout:
        data: list[dict[str, list[dict[str, str | int]]]] = json.loads(
            eslint_result.stdout
        )
        for file_result in data:
            for msg in file_result.get("messages", []):
                if msg.get("ruleId") == "@typescript-eslint/no-unnecessary-condition":
                    line = msg.get("line", 0)
                    message = msg.get("message", "")
                    if isinstance(line, int) and isinstance(message, str):
                        result.unfixable_lines[line] = message

        if result.unfixable_lines:
            logger.info(
                "ESLint: %d unfixable issues remain in %s",
                len(result.unfixable_lines),
                file_path,
            )

    elif eslint_result.stderr:
        logger.warning("ESLint returned no output. stderr: %s", eslint_result.stderr)

    return result
