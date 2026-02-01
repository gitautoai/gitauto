import asyncio
import json
import subprocess

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value={}, raise_on_error=False)
async def detect_unreachable_lines(
    file_path: str, repo_dir: str, clone_task: asyncio.Task
):
    unreachable_lines: dict[int, str] = {}
    if not file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
        logger.info(
            "Skipping unreachable code detection for non-JS/TS file: %s", file_path
        )
        return unreachable_lines

    logger.info("Waiting for clone to complete before ESLint check")
    await clone_task
    logger.info("Clone completed, running ESLint check for %s", file_path)

    cmd = f"npx eslint {file_path} --rule '@typescript-eslint/no-unnecessary-condition: error' --format json"
    logger.info("Running ESLint: %s", cmd)
    result = subprocess.run(
        cmd,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        shell=True,
    )
    logger.info("ESLint completed with return code %d", result.returncode)

    if not result.stdout:
        logger.warning("ESLint returned no output. stderr: %s", result.stderr)
        return unreachable_lines

    data: list[dict[str, list[dict[str, str | int]]]] = json.loads(result.stdout)
    for file_result in data:
        for msg in file_result.get("messages", []):
            if msg.get("ruleId") == "@typescript-eslint/no-unnecessary-condition":
                line = msg.get("line", 0)
                message = msg.get("message", "")
                if isinstance(line, int) and isinstance(message, str):
                    unreachable_lines[line] = message

    return unreachable_lines
