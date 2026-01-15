import asyncio
import fcntl
import os

from config import UTF8
from services.github.files.get_raw_content import get_raw_content
from services.supabase.npm_tokens.get_npm_token import get_npm_token
from utils.error.handle_exceptions import handle_exceptions


def _can_reuse_packages(
    efs_dir: str, package_json_path: str, package_json_content: str
):
    node_modules_path = os.path.join(efs_dir, "node_modules")
    if not os.path.exists(node_modules_path):
        return False
    if not os.path.exists(package_json_path):
        return False
    with open(package_json_path, "r", encoding=UTF8) as f:
        stored_content = f.read()
    if stored_content == package_json_content:
        print(f"node: Reusing existing packages on EFS at {efs_dir}")
        return True
    return False


@handle_exceptions(default_return_value=False, raise_on_error=False)
async def install_node_packages(
    owner: str,
    owner_id: int,
    repo: str,
    branch: str,
    token: str,
    efs_dir: str,
    clone_dir: str | None = None,
):
    # Try reading package.json from clone_dir first (if available)
    package_json_content = None
    if clone_dir:
        local_path = os.path.join(clone_dir, "package.json")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding=UTF8) as f:
                package_json_content = f.read()
            print(f"node: Read package.json from clone_dir: {local_path}")

    # Fall back to GitHub API
    if not package_json_content:
        package_json_content = get_raw_content(
            owner=owner,
            repo=repo,
            file_path="package.json",
            ref=branch,
            token=token,
        )
        print(f"node: Fetched package.json from GitHub API for {owner}/{repo}")

    if not package_json_content:
        print(f"node: No package.json found for {owner}/{repo}, skipping installation")
        return False

    # Ensure EFS directory exists
    os.makedirs(efs_dir, exist_ok=True)

    lock_file_path = os.path.join(efs_dir, ".install.lock")
    package_json_path = os.path.join(efs_dir, "package.json")

    if _can_reuse_packages(efs_dir, package_json_path, package_json_content):
        return True

    with open(lock_file_path, "w", encoding=UTF8) as lock_file:
        try:
            print(f"node: Acquiring lock for {efs_dir}")
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            print(f"node: Lock acquired for {efs_dir}")

            if _can_reuse_packages(efs_dir, package_json_path, package_json_content):
                return True

            with open(package_json_path, "w", encoding=UTF8) as f:
                f.write(package_json_content)

            print(f"node: Installing packages to {efs_dir}")

            npm_env = os.environ.copy()
            npm_env["npm_config_cache"] = "/tmp/.npm"

            npm_token = get_npm_token(owner_id)
            if npm_token:
                npm_env["NPM_TOKEN"] = npm_token
                print(f"node: Using NPM_TOKEN for private packages in {owner}/{repo}")

            process = await asyncio.create_subprocess_exec(
                "npm",
                "install",
                cwd=efs_dir,
                env=npm_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)

            if process.returncode != 0:
                raise RuntimeError(
                    f"npm install failed at {efs_dir} with code {process.returncode}: {stderr.decode()}"
                )

            print("node: Package installation completed successfully")
            return True

        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            print(f"node: Lock released for {efs_dir}")
