# pyright: reportUnusedVariable=false
import subprocess
from unittest.mock import patch

import pytest

from services.git.get_local_head_sha import get_local_head_sha


def test_returns_empty_string_when_subprocess_fails():
    with patch("services.git.get_local_head_sha.run_subprocess") as mock_run:
        mock_run.side_effect = ValueError("not a git repo")
        result = get_local_head_sha(clone_dir="/nonexistent")
        assert result == ""


def test_returns_stripped_sha_from_stdout():
    class FakeResult:
        stdout = "abc123def456\n"

    with patch(
        "services.git.get_local_head_sha.run_subprocess", return_value=FakeResult()
    ) as mock_run:
        result = get_local_head_sha(clone_dir="/tmp/fake")
        assert result == "abc123def456"
        mock_run.assert_called_once_with(
            args=["git", "rev-parse", "HEAD"], cwd="/tmp/fake"
        )


@pytest.mark.integration
def test_sociable_reads_real_head_sha(local_repo):
    _clone_url, work_dir = local_repo
    expected = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=work_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    result = get_local_head_sha(clone_dir=work_dir)
    assert result == expected


@pytest.mark.integration
def test_sociable_head_sha_changes_after_commit(local_repo):
    _clone_url, work_dir = local_repo
    initial = get_local_head_sha(clone_dir=work_dir)

    with open(f"{work_dir}/new_file.txt", "w", encoding="utf-8") as f:
        f.write("new content\n")
    subprocess.run(
        ["git", "add", "new_file.txt"], cwd=work_dir, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "add new file"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )

    after = get_local_head_sha(clone_dir=work_dir)
    assert after != initial
    assert after != ""
    assert initial != ""
