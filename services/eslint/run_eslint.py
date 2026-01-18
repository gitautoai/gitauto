import json
import os
import subprocess

import sentry_sdk

from config import UTF8
from services.efs.is_efs_install_ready import is_efs_install_ready
from services.node.get_npm_cache_dir import set_npm_cache_env
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def run_eslint(
    *, owner: str, repo: str, clone_dir: str, file_path: str, file_content: str
):
    if not file_content.strip():
        logger.info("ESLint: Skipping %s - empty content", file_path)
        return None

    if not file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
        logger.info("ESLint: Skipping %s - not a JS/TS file", file_path)
        return None

    # Wait for install to complete so npx uses local packages instead of downloading
    await is_efs_install_ready(owner, repo, "node")

    # Write to disk and use --fix (alternative: stdin/stdout without file)
    full_path = os.path.join(clone_dir, file_path)
    os.makedirs(
        os.path.dirname(full_path), exist_ok=True
    )  # For new files in new directories

    with open(full_path, "w", encoding=UTF8) as f:
        f.write(file_content)

    env = os.environ.copy()
    set_npm_cache_env(env)

    # --yes: fallback to download if not in node_modules
    logger.info("ESLint: Running eslint with --fix...")
    result = subprocess.run(
        ["npx", "--yes", "eslint", "--fix", "--format", "json", full_path],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        cwd=clone_dir,
        env=env,
    )

    # ESLint exit codes:
    # 0 = no linting errors
    # 1 = linting errors found (some fixable, some not)
    # 2+ = fatal error (bad config, missing file, crash)
    if result.returncode not in [0, 1]:
        raise RuntimeError(
            f"ESLint failed with code {result.returncode}: {result.stderr}"
        )

    with open(full_path, "r", encoding=UTF8) as f:
        fixed_content = f.read()

    if result.stdout:
        try:
            eslint_output = json.loads(result.stdout)
            errors = []
            for file_result in eslint_output:
                for message in file_result.get("messages", []):
                    errors.append(
                        {
                            "line": message.get("line"),
                            "column": message.get("column"),
                            "message": message.get("message"),
                            "ruleId": message.get("ruleId"),
                            "severity": message.get("severity"),
                        }
                    )

            if errors:
                sentry_sdk.capture_message(
                    f"ESLint: {len(errors)} unfixable errors in {file_path}: {errors}",
                    level="warning",
                )
            else:
                logger.info("ESLint: Successfully fixed %s with no errors", file_path)

            return fixed_content
        except json.JSONDecodeError as e:
            sentry_sdk.capture_exception(e)

    logger.info(
        "ESLint: Completed for %s (return code: %d)", file_path, result.returncode
    )
    return fixed_content
