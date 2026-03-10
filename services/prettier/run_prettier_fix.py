import os
import subprocess
from dataclasses import dataclass

from config import UTF8
from constants.aws import EFS_TIMEOUT_SECONDS
from services.prettier.get_prettier_config import get_prettier_config
from services.github.types.github_types import BaseArgs
from services.node.get_npm_cache_dir import set_npm_cache_env
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@dataclass
class PrettierResult:
    success: bool
    content: str | None
    error: str | None


@handle_exceptions(
    default_return_value=PrettierResult(success=True, content=None, error=None),
    raise_on_error=False,
)
async def run_prettier_fix(*, base_args: BaseArgs, file_path: str, file_content: str):
    if not file_content.strip():
        logger.info("Prettier: Skipping %s - empty content", file_path)
        return PrettierResult(success=True, content=None, error=None)

    if not file_path.endswith(
        (".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".scss", ".md", ".yaml", ".yml")
    ):
        logger.info("Prettier: Skipping %s - not a Prettier-supported file", file_path)
        return PrettierResult(success=True, content=None, error=None)

    if not get_prettier_config(base_args):
        logger.info(
            "Prettier: Skipping %s - no Prettier config found in repo", file_path
        )
        return PrettierResult(success=True, content=None, error=None)

    clone_dir = base_args.get("clone_dir", "")

    # Write to disk and use --write (alternative: stdin/stdout without file)
    full_path = os.path.join(clone_dir, file_path)
    os.makedirs(
        os.path.dirname(full_path), exist_ok=True
    )  # For new files in new directories

    with open(full_path, "w", encoding=UTF8) as f:
        f.write(file_content)

    env = os.environ.copy()
    set_npm_cache_env(env)

    # --yes: fallback to download if not in node_modules
    result = subprocess.run(
        ["npx", "--yes", "prettier", "--write", full_path],
        capture_output=True,
        text=True,
        timeout=EFS_TIMEOUT_SECONDS,
        check=False,
        cwd=clone_dir,
        env=env,
    )

    if result.returncode != 0:
        error_msg = result.stderr.strip() or result.stdout.strip()
        logger.warning("Prettier failed for %s: %s", file_path, error_msg)
        return PrettierResult(success=False, content=None, error=error_msg)

    with open(full_path, "r", encoding=UTF8) as f:
        fixed_content = f.read()

    logger.info("Prettier: Successfully formatted %s", file_path)
    return PrettierResult(success=True, content=fixed_content, error=None)
