# pylint: disable=use-implicit-booleaness-not-comparison
import os
import tempfile
from typing import cast

from services.github.types.pull_request_file import PullRequestFile
from services.git.save_pr_files import save_pr_files


def test_save_pr_files_reads_existing_files():
    with tempfile.TemporaryDirectory() as clone_dir:
        os.makedirs(os.path.join(clone_dir, "src"), exist_ok=True)
        with open(os.path.join(clone_dir, "src/app.py"), "w", encoding="utf-8") as f:
            f.write("print('hello')\n")
        with open(os.path.join(clone_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Readme\n")

        pr_files = cast(
            list[PullRequestFile],
            [
                {"filename": "src/app.py", "status": "modified"},
                {"filename": "README.md", "status": "added"},
            ],
        )
        saved, deleted = save_pr_files(clone_dir=clone_dir, pr_files=pr_files)
        assert saved == {"src/app.py": "print('hello')\n", "README.md": "# Readme\n"}
        assert deleted == []


def test_save_pr_files_handles_removed_files():
    with tempfile.TemporaryDirectory() as clone_dir:
        with open(os.path.join(clone_dir, "keep.py"), "w", encoding="utf-8") as f:
            f.write("keep\n")

        pr_files = cast(
            list[PullRequestFile],
            [
                {"filename": "keep.py", "status": "modified"},
                {"filename": "gone.py", "status": "removed"},
            ],
        )
        saved, deleted = save_pr_files(clone_dir=clone_dir, pr_files=pr_files)
        assert saved == {"keep.py": "keep\n"}
        assert deleted == ["gone.py"]


def test_save_pr_files_skips_missing_files():
    with tempfile.TemporaryDirectory() as clone_dir:
        pr_files = cast(
            list[PullRequestFile],
            [{"filename": "nonexistent.py", "status": "modified"}],
        )
        saved, deleted = save_pr_files(clone_dir=clone_dir, pr_files=pr_files)
        assert saved == {}
        assert deleted == []


def test_save_pr_files_empty_input():
    with tempfile.TemporaryDirectory() as clone_dir:
        saved, deleted = save_pr_files(clone_dir=clone_dir, pr_files=[])
        assert saved == {}
        assert deleted == []
