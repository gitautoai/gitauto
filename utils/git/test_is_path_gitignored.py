import subprocess
from pathlib import Path

import pytest

from utils.git.is_path_gitignored import is_path_gitignored


@pytest.fixture
def gitignore_repo(tmp_path):
    """Real git repo with a .gitignore declaring node_modules and dist/.
    Using a real git invocation keeps this test honest — the function exists to
    mirror git's own check-ignore semantics, so mocking would only test our mock."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text("node_modules\ndist/\n*.log\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    return str(tmp_path)


def test_returns_true_for_exact_gitignore_entry(gitignore_repo):
    assert is_path_gitignored(gitignore_repo, "node_modules") is True


def test_returns_true_for_nested_file_in_gitignored_dir(gitignore_repo):
    # Reproduces AGENT-3J4: agent ran search_and_replace on an installed dependency.
    assert (
        is_path_gitignored(gitignore_repo, "node_modules/test-exclude/index.js") is True
    )


def test_returns_true_for_glob_match(gitignore_repo):
    assert is_path_gitignored(gitignore_repo, "debug.log") is True


def test_returns_false_for_source_file(gitignore_repo):
    assert is_path_gitignored(gitignore_repo, "src/index.ts") is False


def test_returns_false_for_gitignore_itself(gitignore_repo):
    # .gitignore is committed, never ignored.
    assert is_path_gitignored(gitignore_repo, ".gitignore") is False


def test_returns_false_when_clone_dir_is_not_a_repo(tmp_path):
    # `git check-ignore` exits 128 outside a repo.
    # We treat non-0/non-1 as "not ignored" so a bad clone_dir doesn't silently block legitimate writes.
    Path(tmp_path, "somefile.ts").write_text("", encoding="utf-8")
    assert is_path_gitignored(str(tmp_path), "somefile.ts") is False
