# pyright: reportUnusedVariable=false
import os
import shutil
import subprocess
import tempfile
from unittest.mock import MagicMock, call, patch

import pytest

from services.git.git_merge_base_into_pr import git_merge_base_into_pr


# ---------------------------------------------------------------------------
# Solitary tests (mocked run_subprocess)
# ---------------------------------------------------------------------------


@patch("services.git.git_merge_base_into_pr.run_subprocess")
def test_clean_merge_with_api_count(mock_run):
    result = git_merge_base_into_pr(
        clone_dir="/tmp/repo", base_branch="main", behind_by=50
    )

    assert result is True
    # Should deepen by behind_by + buffer (50 + 10 = 60)
    mock_run.assert_any_call(
        ["git", "fetch", "--deepen", "60", "origin", "main"], "/tmp/repo"
    )
    mock_run.assert_any_call(["git", "merge", "origin/main", "--no-edit"], "/tmp/repo")
    # On clean merge, git diff --diff-filter=U should NOT be called
    for c in mock_run.call_args_list:
        assert c != call(["git", "diff", "--name-only", "--diff-filter=U"], "/tmp/repo")


@patch("services.git.git_merge_base_into_pr.run_subprocess")
def test_clean_merge_with_exponential_fallback(mock_run):
    result = git_merge_base_into_pr(
        clone_dir="/tmp/repo", base_branch="main", behind_by=0
    )

    assert result is True
    # Should try exponential deepen (first step = 100), then merge-base succeeds
    mock_run.assert_any_call(
        ["git", "fetch", "--deepen", "100", "origin", "main"], "/tmp/repo"
    )
    mock_run.assert_any_call(["git", "merge-base", "HEAD", "origin/main"], "/tmp/repo")


@patch("services.git.git_merge_base_into_pr.run_subprocess")
def test_conflict_merge_commits_markers(mock_run):
    mock_diff_result = MagicMock()
    mock_diff_result.stdout = "shared.txt\nother.txt\n"

    def side_effect(args, _cwd):
        if args[:2] == ["git", "merge"]:
            raise ValueError("merge conflict")
        if args[:2] == ["git", "diff"]:
            return mock_diff_result
        return MagicMock()

    mock_run.side_effect = side_effect

    result = git_merge_base_into_pr(
        clone_dir="/tmp/repo", base_branch="main", behind_by=50
    )

    assert result is True
    # After conflict, should get conflicted files and add them individually
    mock_run.assert_any_call(
        ["git", "diff", "--name-only", "--diff-filter=U"], "/tmp/repo"
    )
    mock_run.assert_any_call(["git", "add", "shared.txt"], "/tmp/repo")
    mock_run.assert_any_call(["git", "add", "other.txt"], "/tmp/repo")
    mock_run.assert_any_call(
        ["git", "commit", "--no-edit", "-m", "Merge main (conflicts)"], "/tmp/repo"
    )


# ---------------------------------------------------------------------------
# Integration tests (real git operations)
# ---------------------------------------------------------------------------


def _setup_repo_with_initial_commit(bare_dir: str, work_dir: str):
    """Initialize a bare repo, clone it, and create an initial commit on main."""

    def run(args, cwd):
        subprocess.run(args, cwd=cwd, check=True, capture_output=True)

    run(["git", "init", "--bare", bare_dir], bare_dir)
    run(["git", "symbolic-ref", "HEAD", "refs/heads/main"], bare_dir)
    run(["git", "clone", bare_dir, work_dir], work_dir)
    run(["git", "config", "user.name", "test"], work_dir)
    run(["git", "config", "user.email", "test@test.com"], work_dir)

    with open(os.path.join(work_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# Test\n")
    run(["git", "add", "."], work_dir)
    run(["git", "commit", "-m", "Initial commit"], work_dir)
    run(["git", "branch", "-M", "main"], work_dir)
    run(["git", "push", "-u", "origin", "main"], work_dir)


def _simulate_production_clone(clone_url: str, base_branch: str, pr_branch: str):
    """Simulate clone_repo_and_install_dependencies steps 1-3:
    clone base branch (shallow), fetch PR branch, checkout PR branch.
    Returns the clone directory path."""
    clone_dir = tempfile.mkdtemp(prefix="gitauto-clone-")

    def run(args):
        subprocess.run(args, cwd=clone_dir, check=True, capture_output=True)

    # Step 1: Shallow clone of base branch (matches git_clone_to_tmp)
    subprocess.run(
        ["git", "clone", "--depth", "1", "-b", base_branch, clone_url, clone_dir],
        check=True,
        capture_output=True,
    )
    # git_clone_to_tmp sets identity after clone
    run(["git", "config", "user.name", "test"])
    run(["git", "config", "user.email", "test@test.com"])
    # Step 2: Fetch PR branch (matches git_fetch)
    run(["git", "fetch", "--depth", "1", clone_url, pr_branch])
    # Step 3: Checkout PR branch (matches git_checkout)
    run(["git", "checkout", "-f", "-B", pr_branch, "FETCH_HEAD"])

    return clone_dir


@pytest.fixture
def conflict_repo():
    """Bare repo with conflicting changes on main and feature branches."""
    bare_dir = tempfile.mkdtemp(prefix="gitauto-merge-bare-")
    work_dir = tempfile.mkdtemp(prefix="gitauto-merge-work-")

    def run(args, cwd):
        subprocess.run(args, cwd=cwd, check=True, capture_output=True)

    _setup_repo_with_initial_commit(bare_dir, work_dir)

    # Create a shared file on main
    shared_file = os.path.join(work_dir, "shared.txt")
    with open(shared_file, "w", encoding="utf-8") as f:
        f.write("line 1\nline 2\nline 3\n")
    run(["git", "add", "."], work_dir)
    run(["git", "commit", "-m", "Add shared file"], work_dir)
    run(["git", "push", "origin", "main"], work_dir)

    # Create feature branch and modify shared.txt
    run(["git", "checkout", "-b", "feature"], work_dir)
    with open(shared_file, "w", encoding="utf-8") as f:
        f.write("line 1\nfeature change\nline 3\n")
    run(["git", "add", "."], work_dir)
    run(["git", "commit", "-m", "Feature change"], work_dir)
    run(["git", "push", "-u", "origin", "feature"], work_dir)

    # Go back to main and make a conflicting change on the same line
    run(["git", "checkout", "main"], work_dir)
    with open(shared_file, "w", encoding="utf-8") as f:
        f.write("line 1\nmain change\nline 3\n")
    run(["git", "add", "."], work_dir)
    run(["git", "commit", "-m", "Main conflicting change"], work_dir)
    run(["git", "push", "origin", "main"], work_dir)

    yield f"file://{bare_dir}", work_dir

    shutil.rmtree(bare_dir, ignore_errors=True)
    shutil.rmtree(work_dir, ignore_errors=True)


@pytest.fixture
def clean_merge_repo():
    """Bare repo where main and feature have non-conflicting changes."""
    bare_dir = tempfile.mkdtemp(prefix="gitauto-clean-bare-")
    work_dir = tempfile.mkdtemp(prefix="gitauto-clean-work-")

    def run(args, cwd):
        subprocess.run(args, cwd=cwd, check=True, capture_output=True)

    _setup_repo_with_initial_commit(bare_dir, work_dir)

    # Feature branch: add a new file (no conflict with main)
    run(["git", "checkout", "-b", "feature"], work_dir)
    with open(os.path.join(work_dir, "feature.txt"), "w", encoding="utf-8") as f:
        f.write("feature content\n")
    run(["git", "add", "."], work_dir)
    run(["git", "commit", "-m", "Add feature file"], work_dir)
    run(["git", "push", "-u", "origin", "feature"], work_dir)

    # Main: add a different file (no conflict with feature)
    run(["git", "checkout", "main"], work_dir)
    with open(os.path.join(work_dir, "main_only.txt"), "w", encoding="utf-8") as f:
        f.write("main content\n")
    run(["git", "add", "."], work_dir)
    run(["git", "commit", "-m", "Add main-only file"], work_dir)
    run(["git", "push", "origin", "main"], work_dir)

    yield f"file://{bare_dir}", work_dir

    shutil.rmtree(bare_dir, ignore_errors=True)
    shutil.rmtree(work_dir, ignore_errors=True)


@pytest.mark.integration
def test_integration_conflict_merge(conflict_repo):
    """Clone base, fetch+checkout PR, merge base - verify conflict markers appear."""
    clone_url, _ = conflict_repo
    clone_dir = _simulate_production_clone(clone_url, "main", "feature")

    try:
        # behind_by=0 triggers exponential deepen fallback (no GitHub API in local tests)
        git_merge_base_into_pr(clone_dir=clone_dir, base_branch="main", behind_by=0)

        # Verify conflict markers are in shared.txt (committed, not in working tree)
        shared_path = os.path.join(clone_dir, "shared.txt")
        with open(shared_path, encoding="utf-8") as f:
            content = f.read()

        assert "<<<<<<<" in content
        assert ">>>>>>>" in content

        # Verify git is in a clean state (no merge in progress)
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=clone_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == ""
    finally:
        shutil.rmtree(clone_dir, ignore_errors=True)


@pytest.mark.integration
def test_integration_clean_merge(clean_merge_repo):
    """Clone base, fetch+checkout PR, merge base - verify clean merge."""
    clone_url, _ = clean_merge_repo
    clone_dir = _simulate_production_clone(clone_url, "main", "feature")

    try:
        # behind_by=0 triggers exponential deepen fallback (no GitHub API in local tests)
        git_merge_base_into_pr(clone_dir=clone_dir, base_branch="main", behind_by=0)

        # After clean merge, feature.txt and main_only.txt should both exist
        assert os.path.isfile(os.path.join(clone_dir, "feature.txt"))
        assert os.path.isfile(os.path.join(clone_dir, "main_only.txt"))

        # Verify git is clean
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=clone_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == ""
    finally:
        shutil.rmtree(clone_dir, ignore_errors=True)
