import os
import shutil
import subprocess
import tempfile

import pytest


@pytest.fixture
def local_repo():
    """Create a bare repo + working clone with commits on main and feature/test-branch."""
    bare_dir = tempfile.mkdtemp(prefix="gitauto-bare-")
    work_dir = tempfile.mkdtemp(prefix="gitauto-work-")

    subprocess.run(["git", "init", "--bare", bare_dir], check=True, capture_output=True)
    subprocess.run(
        ["git", "clone", bare_dir, work_dir], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )

    # Initial commit on main
    with open(os.path.join(work_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# Test\n")
    subprocess.run(["git", "add", "."], cwd=work_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "branch", "-M", "main"], cwd=work_dir, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )

    # Second branch with a commit
    subprocess.run(
        ["git", "checkout", "-b", "feature/test-branch"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "feature commit"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "feature/test-branch"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"], cwd=work_dir, check=True, capture_output=True
    )

    yield f"file://{bare_dir}", work_dir

    shutil.rmtree(bare_dir, ignore_errors=True)
    shutil.rmtree(work_dir, ignore_errors=True)
