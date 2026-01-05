import fcntl
import os
import subprocess

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
def install_node_packages(
    owner: str,
    owner_id: int,
    repo: str,
    branch: str,
    token: str,
    efs_dir: str,
):
    # Fetch package.json content from GitHub
    package_json_content = get_raw_content(
        owner=owner,
        repo=repo,
        file_path="package.json",
        ref=branch,
        token=token,
    )

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

            result = subprocess.run(
                ["npm", "install"],
                capture_output=True,  # Capture stdout/stderr to result.stdout/stderr
                text=True,  # Return strings instead of bytes
                timeout=300,
                check=False,  # Don't raise on non-zero return code, we handle it manually
                cwd=efs_dir,
                env=npm_env,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"npm install failed at {efs_dir} with code {result.returncode}: {result.stderr}"
                )

            print("node: Package installation completed successfully")
            return True

        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            print(f"node: Lock released for {efs_dir}")
