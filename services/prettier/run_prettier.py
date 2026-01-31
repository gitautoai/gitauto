import os
import subprocess

from config import UTF8
from constants.aws import EFS_TIMEOUT_SECONDS
from services.efs.extract_dependencies import extract_dependencies
from services.efs.get_efs_dir import get_efs_dir
from services.github.files.get_prettier_config import get_prettier_config
from services.github.types.github_types import BaseArgs
from services.node.get_npm_cache_dir import set_npm_cache_env
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def run_prettier(*, base_args: BaseArgs, file_path: str, file_content: str):
    if not file_content.strip():
        logger.info("Prettier: Skipping %s - empty content", file_path)
        return None

    if not file_path.endswith(
        (".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".scss", ".md", ".yaml", ".yml")
    ):
        logger.info("Prettier: Skipping %s - not a Prettier-supported file", file_path)
        return None

    if not get_prettier_config(base_args):
        logger.info(
            "Prettier: Skipping %s - no Prettier config found in repo", file_path
        )
        return None

    owner = base_args["owner"]
    repo = base_args["repo"]
    clone_dir = base_args.get("clone_dir", "")

    # Extract EFS deps to clone_dir
    efs_dir = get_efs_dir(owner, repo)
    extract_dependencies(efs_dir, clone_dir)

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
        raise RuntimeError(f"Prettier failed for {file_path}: {result.stderr}")

    with open(full_path, "r", encoding=UTF8) as f:
        fixed_content = f.read()

    logger.info("Prettier: Successfully formatted %s", file_path)
    return fixed_content
