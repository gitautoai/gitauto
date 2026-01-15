import os
import subprocess

from config import UTF8
from services.efs.is_efs_install_ready import is_efs_install_ready
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def run_prettier(
    *, owner: str, repo: str, clone_dir: str, file_path: str, file_content: str
):
    if not file_content.strip():
        print(f"Prettier: Skipping {file_path} - empty content")
        return None

    if not file_path.endswith(
        (".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".scss", ".md", ".yaml", ".yml")
    ):
        print(f"Prettier: Skipping {file_path} - not a Prettier-supported file")
        return None

    # Wait for install to complete so npx uses local packages instead of downloading
    await is_efs_install_ready(owner, repo, "node")

    # Write to disk and use --write (alternative: stdin/stdout without file)
    full_path = os.path.join(clone_dir, file_path)
    os.makedirs(
        os.path.dirname(full_path), exist_ok=True
    )  # For new files in new directories

    with open(full_path, "w", encoding=UTF8) as f:
        f.write(file_content)

    # --yes: fallback to download if not in node_modules
    result = subprocess.run(
        ["npx", "--yes", "prettier", "--write", full_path],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        cwd=clone_dir,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Prettier failed for {file_path}: {result.stderr}")

    with open(full_path, "r", encoding=UTF8) as f:
        fixed_content = f.read()

    print(f"Prettier: Successfully formatted {file_path}")
    return fixed_content
